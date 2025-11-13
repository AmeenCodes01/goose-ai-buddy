#!/usr/bin/env python3
"""
Voice Chat Module for Productivity Buddy - FINAL VERSION
Handles voice input/output and conversation with LLM
"""

import os
import json
import time
import logging
import threading
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Callable

import sounddevice as sd
import numpy as np
import wave
import openai
from openai import OpenAI
import pyttsx3

logger = logging.getLogger(__name__)

class VoiceChat:
    def __init__(self, session_manager=None):
        """Initialize voice chat system"""
        self.session_manager = session_manager
        self.is_recording = False
        self.is_listening = False
        self.audio_data = []
        self.sample_rate = 44100
        self.channels = 1
        self.silence_threshold = 0.03  # Increased to reduce false triggers
        self.silence_duration = 3.0  # 3 seconds of silence to end recording
        self.min_recording_duration = 1.0  # Minimum 1 second of actual speech
        self.last_audio_time = time.time()
        
        # OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Text-to-speech engine with lock
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 175)
        self.tts_engine.setProperty('volume', 0.8)
        self.tts_lock = threading.Lock()
        self.is_speaking = False
        
        # Conversation memory
        self.conversation_history = []
        self.user_context = {
            "current_tasks": [],
            "mentioned_today": [],
            "mood_energy": "neutral",
            "last_check_in": None
        }
        
        # Callbacks for integration
        self.on_task_mentioned = None
        self.on_energy_change = None
        
        logger.info("🎤 Voice Chat initialized (improved noise filtering)")
    
    def start_listening(self):
        """Start continuous voice listening"""
        if self.is_listening:
            logger.warning("Already listening")
            return
            
        self.is_listening = True
        logger.info("🎧 Starting voice listening...")
        
        # Start audio monitoring in separate thread
        self.listen_thread = threading.Thread(target=self._audio_monitoring_loop, daemon=True)
        self.listen_thread.start()
    
    def stop_listening(self):
        """Stop voice listening"""
        self.is_listening = False
        if hasattr(self, 'listen_thread'):
            self.listen_thread.join(timeout=1.0)
        logger.info("🔇 Voice listening stopped")
    
    def _audio_monitoring_loop(self):
        """Main audio monitoring loop"""
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self._audio_callback,
                blocksize=1024
            ):
                logger.info("🎤 Listening for voice input... (improved sensitivity)")
                while self.is_listening:
                    time.sleep(0.1)
                    
                    # Check for silence timeout during recording
                    if self.is_recording:
                        silence_time = time.time() - self.last_audio_time
                        if silence_time >= self.silence_duration:
                            self._process_recorded_audio()
                            
        except Exception as e:
            logger.error(f"❌ Audio monitoring error: {e}")
            # Try to restart monitoring
            if self.is_listening:
                logger.info("🔄 Attempting to restart audio monitoring...")
                time.sleep(1)
                threading.Thread(target=self._audio_monitoring_loop, daemon=True).start()
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream"""
        if status:
            logger.warning(f"Audio status: {status}")
        
        # Skip recording while AI is speaking to avoid feedback
        if self.is_speaking:
            return
        
        # Calculate audio level
        audio_level = np.sqrt(np.mean(indata**2))
        
        # More sophisticated voice detection
        if not self.is_recording and audio_level > self.silence_threshold:
            # Additional check: ensure sustained audio for at least 100ms
            sustained_audio = True
            if len(indata) > 100:  # Check if we have enough samples
                recent_levels = [np.sqrt(np.mean(chunk**2)) for chunk in np.array_split(indata[:, 0], 5)]
                sustained_audio = sum(level > self.silence_threshold for level in recent_levels) >= 3
            
            if sustained_audio:
                logger.info("🗣️  Clear voice detected, starting recording...")
                self.is_recording = True
                self.audio_data = []
                self.recording_start_time = time.time()
                self.last_audio_time = time.time()
        
        # Continue recording and track silence
        if self.is_recording:
            self.audio_data.extend(indata[:, 0].copy())
            
            if audio_level > self.silence_threshold:
                self.last_audio_time = time.time()
    
    def _process_recorded_audio(self):
        """Process recorded audio and send to LLM"""
        if not self.audio_data:
            return
        
        # Check minimum recording duration and audio length
        recording_duration = time.time() - getattr(self, 'recording_start_time', time.time())
        audio_duration = len(self.audio_data) / self.sample_rate
        
        if recording_duration < self.min_recording_duration or audio_duration < 0.8:
            logger.info(f"⏱️  Recording too short (rec:{recording_duration:.1f}s, audio:{audio_duration:.1f}s), likely noise...")
            self.is_recording = False
            self.audio_data = []
            return
            
        logger.info(f"🎵 Processing recorded audio ({audio_duration:.2f}s)...")
        self.is_recording = False
        
        try:
            # Save audio to temporary file with better cleanup
            audio_array = np.array(self.audio_data, dtype=np.float32)
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_filename = temp_file.name
            temp_file.close()  # Close file handle immediately
            
            with wave.open(temp_filename, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                
                # Convert float32 to int16
                audio_int16 = (audio_array * 32767).astype(np.int16)
                wav_file.writeframes(audio_int16.tobytes())
            
            # Transcribe with Whisper
            with open(temp_filename, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            
            # Clean up temp file immediately
            try:
                os.unlink(temp_filename)
            except OSError:
                pass  # File might already be deleted
            
            user_text = transcript.text.strip()
            if user_text and len(user_text) > 1:  # Ignore single character transcriptions
                logger.info(f"👤 User said: {user_text}")
                # Process user message in separate thread to avoid blocking
                threading.Thread(target=self._handle_user_message, args=(user_text,), daemon=True).start()
            else:
                logger.info("🤐 Empty or minimal transcription, ignoring...")
            
        except Exception as e:
            logger.error(f"❌ Audio processing error: {e}")
            # Try to clean up temp file on error
            try:
                if 'temp_filename' in locals():
                    os.unlink(temp_filename)
            except OSError:
                pass
        finally:
            self.audio_data = []
    
    def _handle_user_message(self, user_text: str):
        """Process user message and generate response"""
        try:
            # Update conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_text,
                "timestamp": datetime.now().isoformat()
            })
            
            # Extract context and update user state
            self._update_user_context(user_text)
            
            # Generate AI response
            response = self._generate_ai_response(user_text)
            
            # Speak the response (with proper concurrency control)
            self._speak_response(response)
            
            # Add AI response to history
            self.conversation_history.append({
                "role": "assistant", 
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Message handling error: {e}")
            self._speak_response("Sorry, I had trouble processing that. Could you try again?")
    
    def _generate_ai_response(self, user_text: str) -> str:
        """Generate response using OpenAI LLM"""
        try:
            # Build context for LLM
            system_prompt = self._build_system_prompt()
            
            # Prepare messages for LLM
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add recent conversation history (last 10 messages)
            recent_history = self.conversation_history[-10:] if self.conversation_history else []
            for msg in recent_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Get response from LLM
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ LLM response error: {e}")
            return "I'm having trouble thinking right now. How about we try that again?"
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with current context"""
        current_time = datetime.now().strftime("%H:%M")
        current_date = datetime.now().strftime("%A, %B %d")
        
        # Get session info if available
        session_info = ""
        if self.session_manager:
            status = self.session_manager.get_current_status()
            if status.get('state') != 'idle':
                session_info = f"Currently in {status.get('state')} mode. "
        
        prompt = f"""You are a supportive AI buddy helping your user stay productive and accountable. 

Current context:
- Time: {current_time} on {current_date}
- User's energy/mood: {self.user_context['mood_energy']}
- {session_info}
- Recent tasks mentioned: {', '.join(self.user_context['current_tasks'][-3:]) if self.user_context['current_tasks'] else 'None'}

Your personality:
- Warm, encouraging, and supportive like a good friend
- Gently nudging but never pushy or judgmental
- Remember things they mention and check in about them organically
- Help them break things down when they feel overwhelmed
- Celebrate small wins and progress

Guidelines:
- Keep responses short and conversational (1-2 sentences usually)
- Ask open-ended questions to understand their day/goals
- If they mention tasks, remember them and check in later
- Adapt your energy to match theirs
- Offer gentle suggestions rather than demands
- Be genuinely interested in their wellbeing

Respond naturally as their supportive AI buddy."""
        
        return prompt
    
    def _update_user_context(self, user_text: str):
        """Extract and update context from user message"""
        text_lower = user_text.lower()
        
        # Extract mood/energy indicators
        if any(word in text_lower for word in ["tired", "exhausted", "drained", "sleepy"]):
            self.user_context["mood_energy"] = "low"
        elif any(word in text_lower for word in ["good", "great", "energetic", "ready", "motivated"]):
            self.user_context["mood_energy"] = "high"
        elif any(word in text_lower for word in ["okay", "fine", "alright", "stressed", "overwhelmed"]):
            self.user_context["mood_energy"] = "medium"
        
        # Extract task mentions (simple keyword detection)
        task_keywords = ["assignment", "essay", "project", "presentation", "homework", "study", "work", "call", "meeting"]
        for keyword in task_keywords:
            if keyword in text_lower and keyword not in [task.lower() for task in self.user_context["current_tasks"]]:
                self.user_context["current_tasks"].append(f"{keyword} mentioned")
        
        # Keep only recent tasks (last 10)
        self.user_context["current_tasks"] = self.user_context["current_tasks"][-10:]
        
        # Update last check-in time
        self.user_context["last_check_in"] = datetime.now().isoformat()
    
    def _speak_response(self, text: str):
        """Convert text to speech - THREAD-SAFE"""
        try:
            logger.info(f"🤖 AI says: {text}")
            
            # Use a queue-based approach to prevent TTS conflicts
            def speak_in_thread():
                with self.tts_lock:  # Ensure only one TTS at a time
                    try:
                        self.is_speaking = True
                        self.tts_engine.say(text)
                        self.tts_engine.runAndWait()
                        logger.info("🔊 Finished speaking, ready for next input...")
                    except Exception as e:
                        logger.error(f"❌ TTS thread error: {e}")
                    finally:
                        self.is_speaking = False
            
            # Only start new TTS if not already speaking
            if not self.is_speaking:
                speak_thread = threading.Thread(target=speak_in_thread, daemon=True)
                speak_thread.start()
            else:
                logger.info("🔊 Already speaking, queuing response...")
            
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
    
    def proactive_check_in(self):
        """Initiate a proactive check-in with the user"""
        if not self.user_context.get("last_check_in"):
            message = "Hey! How's your day going? Anything on your mind?"
        elif self.user_context["current_tasks"]:
            recent_task = self.user_context["current_tasks"][-1]
            message = f"Quick check - how's that {recent_task} coming along?"
        else:
            message = "What's bubbling up for you right now? Anything calling for your attention?"
        
        self._speak_response(message)
    
    def set_task_mentioned_callback(self, callback: Callable):
        """Set callback for when user mentions a task"""
        self.on_task_mentioned = callback
    
    def set_energy_change_callback(self, callback: Callable):
        """Set callback for when user's energy changes"""
        self.on_energy_change = callback
    
    def get_conversation_summary(self) -> Dict:
        """Get summary of current conversation state"""
        return {
            "total_messages": len(self.conversation_history),
            "current_tasks": self.user_context["current_tasks"],
            "mood_energy": self.user_context["mood_energy"],
            "last_check_in": self.user_context.get("last_check_in"),
            "is_listening": self.is_listening,
            "is_speaking": self.is_speaking
        }

#!/usr/bin/env python3
"""
Simple Voice Chat - No Threads, Clean Implementation
Continuous back-and-forth conversation with 2-second silence detection
"""

import os
import time
import tempfile
import wave
import logging
from datetime import datetime

import sounddevice as sd
import numpy as np
from openai import OpenAI
import pyttsx3
from dotenv import load_dotenv

load_dotenv()
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleVoiceChat:
    def __init__(self):
        # Audio settings
        self.sample_rate = 44100
        self.channels = 1
        self.silence_threshold = 0.02  # Adjust based on your environment
        self.silence_duration = 2.0    # 2 seconds of silence to end recording
        
        # OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Text-to-speech engine
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 175)
        self.tts_engine.setProperty('volume', 0.8)
        
        # Conversation memory
        self.conversation_history = []
        
        logger.info("🎤 Simple Voice Chat initialized")
    
    def record_audio(self):
        """Record audio until 2 seconds of silence"""
        logger.info("🎧 Listening for voice input...")
        
        audio_data = []
        is_recording = False
        last_audio_time = time.time()
        
        def audio_callback(indata, frames, callback_time, status):
            nonlocal audio_data, is_recording, last_audio_time
            
            if status:
                logger.warning(f"Audio status: {status}")
            
            # Calculate audio level
            audio_level = np.sqrt(np.mean(indata**2))
            
            # Start recording on voice detection
            if not is_recording and audio_level > self.silence_threshold:
                logger.info("🗣️  Voice detected, starting recording...")
                is_recording = True
                audio_data = []
                last_audio_time = time.time()
            
            # Continue recording
            if is_recording:
                audio_data.extend(indata[:, 0].copy())
                if audio_level > self.silence_threshold:
                    last_audio_time = time.time()
        
        # Start audio stream
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=audio_callback,
            blocksize=1024
        ):
            # Wait for recording to start and complete
            while True:
                time.sleep(0.1)
                
                # Check if we should stop recording due to silence
                if is_recording:
                    silence_time = time.time() - last_audio_time
                    if silence_time >= self.silence_duration:
                        break
        
        return np.array(audio_data, dtype=np.float32) if audio_data else None
    
    def transcribe_audio(self, audio_data):
        """Convert audio to text using OpenAI Whisper"""
        if audio_data is None or len(audio_data) == 0:
            return None
        
        # Check minimum audio length
        audio_duration = len(audio_data) / self.sample_rate
        if audio_duration < 0.5:
            logger.info(f"⏱️  Audio too short ({audio_duration:.2f}s), ignoring...")
            return None
        
        logger.info(f"🎵 Processing recorded audio ({audio_duration:.2f}s)...")
        
        try:
            # Save audio to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_filename = temp_file.name
            temp_file.close()
            
            with wave.open(temp_filename, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                
                # Convert float32 to int16
                audio_int16 = (audio_data * 32767).astype(np.int16)
                wav_file.writeframes(audio_int16.tobytes())
            
            # Transcribe with Whisper
            with open(temp_filename, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            
            # Clean up temp file
            os.unlink(temp_filename)
            
            return transcript.text.strip()
            
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            return None
    
    def generate_response(self, user_text):
        """Generate AI response using OpenAI"""
        try:
            # Build conversation context
            current_time = datetime.now().strftime("%H:%M")
            current_date = datetime.now().strftime("%A, %B %d")
            
            system_prompt = f"""You are a supportive AI buddy helping your user stay productive and accountable.

Current context:
- Time: {current_time} on {current_date}

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
- Be genuinely interested in their wellbeing

Respond naturally as their supportive AI buddy."""

            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add recent conversation history (last 10 messages)
            recent_history = self.conversation_history[-10:] if self.conversation_history else []
            for msg in recent_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current user message
            messages.append({"role": "user", "content": user_text})
            
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
            return "I'm having trouble thinking right now. Could you try again?"
    
    def speak_text(self, text):
        """Convert text to speech"""
        try:
            logger.info(f"🤖 AI says: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            logger.info("🔊 Finished speaking")
            
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
    
    def run_conversation(self):
        """Main conversation loop"""
        logger.info("🚀 Starting continuous conversation...")
        logger.info("💬 Speak naturally, then wait 2 seconds for processing")
        logger.info("🛑 Press Ctrl+C to stop\n")
        
        try:
            conversation_count = 0
            
            while True:
                # Record user input
                audio_data = self.record_audio()
                
                # Transcribe to text
                user_text = self.transcribe_audio(audio_data)
                
                if user_text and len(user_text.strip()) > 1:
                    logger.info(f"👤 User said: {user_text}")
                    
                    # Add to conversation history
                    self.conversation_history.append({
                        "role": "user",
                        "content": user_text,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Generate AI response
                    ai_response = self.generate_response(user_text)
                    
                    # Add AI response to history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": ai_response,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Speak the response
                    self.speak_text(ai_response)
                    
                    conversation_count += 1
                    logger.info(f"💬 Conversation turn: {conversation_count}\n")
                
                else:
                    logger.info("🤐 No clear speech detected, listening again...")
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Conversation ended by user")
            total_turns = len(self.conversation_history) // 2
            logger.info(f"📊 Total conversation turns: {total_turns}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")

def main():
    """Main function"""
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key:")
        print("   Windows: set OPENAI_API_KEY=your_api_key_here")
        print("   or add it to your .env file")
        return
    
    # Create and run voice chat
    voice_chat = SimpleVoiceChat()
    voice_chat.run_conversation()

if __name__ == "__main__":
    main()

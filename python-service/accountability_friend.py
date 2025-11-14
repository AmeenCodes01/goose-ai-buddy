"""
Conversational Accountability Friend for Productivity Buddy.
Orchestrates voice-first interactions with Goose AI for endless chat, logging, and summarization.
"""

import os
import time
import re
import logging
from datetime import datetime
from typing import List, Dict, Callable, Optional

# Assuming these are in the same python-service directory
from goose_integration import GooseClient
from voice_interaction import VoiceInteraction,SpeakText
# SimpleScheduler is removed as per instruction

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Manages voice-first interactive conversations with Goose for accountability.
    Handles conversation logging, Goose interaction, and summarization.
    Timer scheduling functionality has been removed.
    """

    CONVERSATION_LOG_DIR = "conversation_logs"
    DEBUG_TEXT_INPUT_ENABLED = False # Set to False for production (voice-only)

    def __init__(self, voice_interaction_instance: Optional[VoiceInteraction] = None):
        self.goose_client = GooseClient()
        self.voice = voice_interaction_instance if voice_interaction_instance else VoiceInteraction()
        # self.scheduler = SimpleScheduler() # Removed timer functionality
        self.conversation_log_path: Optional[str] = None
        self.current_session_id: Optional[str] = None
        
        os.makedirs(self.CONVERSATION_LOG_DIR, exist_ok=True)
        print("ConversationManager initialized (timer functionality removed).")

    def _start_new_conversation_log(self) -> None:
        """
        Starts a new log file for the current conversation.
        """
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.conversation_log_path = os.path.join(
            self.CONVERSATION_LOG_DIR,
            f"conversation_{self.current_session_id}.md"
        )
        with open(self.conversation_log_path, "w", encoding="utf-8") as f:
            f.write(f"# Conversation Log - {self.current_session_id}")
        print(f"[LOG] New conversation log started at: {self.conversation_log_path}")

    def _log_turn(self, speaker: str, text: str) -> None:
        """
        Logs a single turn of the conversation.
        """
        if not self.conversation_log_path:
            self._start_new_conversation_log()

        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(self.conversation_log_path, "a", encoding="utf-8") as f:
            f.write(f"**{timestamp} - {speaker}:** {text}")
        logger.info(f"[CONV LOG] {speaker}: {text}")

    def _get_goose_response(self, user_input: str) -> str:
        """
        Sends user input to Goose and returns its response.
        Includes Goose's persona instructions.
        """
        # This prompt defines Goose's empathetic and accountability-focused persona
        # persona_instructions = f"""
        # You are an empathetic and supportive accountability friend. Your goal is to help the user stay focused and achieve their tasks. When talking to the user, always:
        # - Be friendly and understanding, never judgmental.
        # - Ask open-ended questions like 'What's next?', 'How can I help you plan?', 'What are you aiming to get done?'
        # - Encourage them to set small, achievable goals.
        # - Keep responses concise and focused on helping the user stay productive and motivated.
        # - Do NOT suggest or offer to set any timers or reminders, as that functionality is handled separately.
        # - If the user asks for a summary, respond with a placeholder like "Okay, I can summarize that for you, but I need to quickly review our chat first. What else is on your mind?"

        # Here is the user's input:
        # {user_input}
        # """

        try:
            print("[GOOSE] Getting response...")
            result = self.goose_client.run_task(
                instructions=user_input,
                extensions=["developer"], # Assuming developer extension is useful for context
                max_turns=1 # One turn at a time for interactive conversation
            )
            if result.get('success'):
                goose_output = result.get('output', '[Goose has no response]').strip()
                return goose_output
            else:
                error_msg = f"Goose AI error: {result.get('error', 'Unknown error')}"
                print(f"[ERROR] {error_msg}")
                return "I'm having a bit of trouble connecting right now. Could you try again?"
        except Exception as e:
            print(f"[ERROR] Error interacting with Goose AI: {e}")
            return "Oops, something went wrong when I tried to think. Let's try that again."

    # Timer intent detection and scheduled check-in handling methods removed

    def summarize_conversation(self) -> str:
        """
        Reads the conversation log and asks Goose to summarize it.
        """
        if not self.conversation_log_path or not os.path.exists(self.conversation_log_path):
            return "I haven't recorded enough conversation to summarize yet."

        with open(self.conversation_log_path, "r", encoding="utf-8") as f:
            full_conversation = f.read()
        
        summary_instructions = f"""
        Please provide a concise, friendly summary of the following conversation. Focus on key discussions, decisions, and any action items or goals mentioned. Keep it under 100 words.

        Conversation Log:
        {full_conversation}
        """
        
        try:
            print("[GOOSE] Generating summary...")
            result = self.goose_client.run_task(
                instructions=summary_instructions,
                extensions=["developer"],
                no_session=True,
                max_turns=2 # Enough for a summary
            )
            if result.get('success'):
                summary = result.get('output', 'Could not generate summary.').strip()
                self._log_turn("GOOSE_SUMMARY", summary)
                return summary
            else:
                error_msg = f"Summary generation failed: {result.get('error', 'Unknown error')}"
                print(f"[ERROR] {error_msg}")
                return "I'm having trouble summarizing right now. Please try again later."
        except Exception as e:
            print(f"[ERROR] Error generating summary: {e}")
            return "Oops, something went wrong while trying to summarize."

    def start_accountability_conversation(self, initial_message: str = "Hey there! How are you doing today? Ready to tackle some tasks?") -> None:
        """
        Starts the main voice-first accountability conversation loop.
        """
        self._start_new_conversation_log() # Start a new log for this conversation
        self._log_turn("GOOSE", initial_message)
        print("--- Accountability Conversation Started ---")
        SpeakText(initial_message)
        print("Say 'quit', 'exit', 'goodbye', or 'summarize' to manage the conversation.")

        while True:
            print("Inside while loop of COnvoManager")
            if self.DEBUG_TEXT_INPUT_ENABLED: # Fallback for dev if voice fails
                 user_input = input("YOU (TEXT DEBUG): ").strip()
                 if user_input.lower() == "voice": # Allow switching to voice if engine works
                     SpeakText("Switching to voice mode. Please speak now.")
                     user_input = self.voice.listen()
                 elif not user_input: # If empty text input, try voice
                     user_input = self.voice.listen()
            else:
                user_input = self.voice.listen()
                print(f"user input: {user_input}")
            if user_input is None or not user_input.strip():
                # print("[CONVERSATION] No significant speech detected, waiting for user input...")
                continue

            user_input_lower = user_input.lower()
            self._log_turn("USER: -----", user_input)
            
            if any(word in user_input_lower for word in ['quit', 'exit', 'goodbye', 'all set', 'done']):
                final_message = "Okay, sounds good! Remember, I'm here to help you stay focused whenever you need me. Take care!"
                self.voice.speak(final_message)
                self._log_turn("GOOSE", final_message)
                break
            elif "summarize conversation" in user_input_lower or "summarize our chat" in user_input_lower:
                summary = self.summarize_conversation()
                self.voice.speak(summary)
                self._log_turn("GOOSE", summary)
                continue
            
            goose_response = self._get_goose_response(user_input)
            
            self._log_turn("GOOSE", goose_response)
            print(goose_response," goose about to speak")
            SpeakText(goose_response)

            # Timer intent detection and scheduling call removed from here

if __name__ == "__main__":
    # Basic logging config for main execution
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🚀 Initializing Accountability Friend...")
    manager = ConversationManager()
    manager.start_accountability_conversation("Hey there! How are you feeling today? Ready to talk about your goals?")
    print("--- Conversation Ended ---")

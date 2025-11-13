"""
Voice Interaction Module
Provides non-blocking text-to-speech and speech-to-text capabilities for conversational interactions.
"""

import pyttsx3
import speech_recognition as sr
import logging
import threading # Import threading for non-blocking speak
from typing import Optional


class VoiceInteraction:
    """
    A class to handle voice interactions including non-blocking text-to-speech and speech-to-text.
    
    Dependencies:
    - pyttsx3: Text-to-speech engine
    - SpeechRecognition: Speech-to-text recognition
    - pyaudio: Audio input/output (required by SpeechRecognition)
    """
    
    def __init__(self, voice_rate: int = 200, voice_volume: float = 0.9):
        """
        Initialize the VoiceInteraction class.
        
        Args:
            voice_rate (int): Speech rate (words per minute)
            voice_volume (float): Voice volume (0.0 to 1.0)
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize TTS engine
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', voice_rate)
            self.tts_engine.setProperty('volume', voice_volume)
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            self.tts_engine = None
            
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Adjust for ambient noise
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            self.logger.warning(f"Could not adjust for ambient noise: {e}")

    def _speak_thread_target(self, text: str):
        """Target function for the TTS thread."""
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            self.logger.error(f"TTS thread error: {e}")

    def speak(self, text: str) -> bool:
        """
        Convert text to speech and play it in a non-blocking manner.
        
        Args:
            text (str): The text to convert to speech
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.tts_engine:
            self.logger.error("TTS engine not available")
            print(f"[SPEAK]: {text}")  # Fallback to text output
            return False
            
        try:
            # Run TTS in a separate thread to prevent blocking
            tts_thread = threading.Thread(target=self._speak_thread_target, args=(text,))
            tts_thread.daemon = True # Allow program to exit even if thread is running
            tts_thread.start()
            return True
        except Exception as e:
            self.logger.error(f"TTS error: {e}")
            print(f"[SPEAK]: {text}")  # Fallback to text output
            return False
    
    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """
        Convert speech to text using the microphone.
        
        Args:
            timeout (int): Seconds to wait for speech before timing out
            phrase_time_limit (int): Maximum seconds for a single phrase
            
        Returns:
            Optional[str]: The recognized text, or None if recognition failed
        """
        try:
            with self.microphone as source:
                print("Listening...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
            
            print("Processing speech...")
            # Use Google's free speech recognition service
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
            
        except sr.WaitTimeoutError:
            print("No speech detected within timeout period.")
            return None
        except sr.UnknownValueError:
            print("Could not understand the speech.")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition service error: {e}")
            print("Speech recognition service is unavailable.")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during speech recognition: {e}")
            return None
    
    def have_conversation(self, initial_message: str = "Hello! How can I help you today?") -> None:
        """
        Start a conversation loop with voice interaction.
        
        Args:
            initial_message (str): The initial message to speak
        """
        print("Starting voice conversation. Say 'quit', 'exit', or 'goodbye' to end.")
        
        # Speak initial message
        self.speak(initial_message)
        
        while True:
            # Listen for user input
            user_input = self.listen()
            
            if user_input is None:
                self.speak("I didn't catch that. Could you please repeat?")
                continue
            
            # Check for exit conditions
            exit_words = ['quit', 'exit', 'goodbye', 'bye', 'stop']
            if any(word in user_input.lower() for word in exit_words):
                self.speak("Goodbye! Have a great day!")
                break
            
            # Echo back what was heard (MVP functionality)
            # In a real implementation, this would integrate with your AI system
            response = f"You said: {user_input}. This is a basic echo response."
            self.speak(response)
    
    def test_audio_system(self) -> bool:
        """
        Test both TTS and STT functionality.
        
        Returns:
            bool: True if both systems work, False otherwise
        """
        print("Testing audio systems...")
        
        # Test TTS
        tts_works = self.speak("Testing text to speech. Can you hear this?")
        if not tts_works:
            print("TTS test failed")
            return False
        
        # Test STT
        print("Now testing speech to text. Please say something...")
        result = self.listen(timeout=15)
        if result is None:
            print("STT test failed")
            return False
        
        print(f"STT test successful! Recognized: {result}")
        self.speak(f"Great! I heard you say: {result}")
        return True


def main():
    """
    Example usage of the VoiceInteraction class.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Create voice interaction instance
    voice = VoiceInteraction()
    
    # Test the system
    if voice.test_audio_system():
        print("Audio system test passed!")
        
        # Start conversation
        voice.have_conversation()
    else:
        print("Audio system test failed. Please check your microphone and speakers.")


if __name__ == "__main__":
    main()

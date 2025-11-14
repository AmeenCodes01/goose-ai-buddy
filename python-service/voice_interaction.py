# """
# Voice Interaction Module
# Simplified class-based text-to-speech (TTS) and optional speech-to-text (STT).
# """
import speech_recognition as sr
import pyttsx3 

# Initialize the recognizer 
# r = sr.Recognizer() 

# Function to convert text to
# speech
def SpeakText(command):
    print(command," command")
    # Initialize the 
    engine = pyttsx3.init()
    print("init")
    engine.say(command) 
    print("said")
    engine.runAndWait()
    print("stop")
    engine.stop()
    
    
import pyttsx3
import speech_recognition as sr
import logging
import time
from typing import Optional


class VoiceInteraction:
    """
    Handles voice interactions with simple, reliable synchronous TTS.
    """

    def __init__(self, voice_rate: int = 200, voice_volume: float = 0.9):
        """
        Initialize the VoiceInteraction class.

        Args:
            voice_rate (int): Speech rate (words per minute)
            voice_volume (float): Voice volume (0.0 to 1.0)
        """
        self.logger = logging.getLogger(__name__)
        self.voice_rate = voice_rate
        self.voice_volume = voice_volume
      #  self._init_engine()

        # Initialize STT recognizer (optional)
        self.recognizer = sr.Recognizer()
        self.microphone = None  # delay initialization

    # -------------------------------------------------------------------------
    # TTS
    # -------------------------------------------------------------------------
    def _init_engine(self):
        """Initialize pyttsx3 engine."""
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty("rate", self.voice_rate)
            self.tts_engine.setProperty("volume", self.voice_volume)

            voices = self.tts_engine.getProperty("voices")
            if voices:
                self.tts_engine.setProperty("voice", voices[0].id)
                print(f"[INIT] Voice loaded: {voices[0].name}")
            else:
                print("[INIT WARNING] No voices found in pyttsx3")
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            self.tts_engine = None

    def speak(self, text: str):
        """Speak text synchronously (blocks until finished)."""
        if not text:
            return
        try:
            SpeakText(text)
            # print(text, " speak")
            # engine = pyttsx3.init()
            # engine.say(text)
            # engine.runAndWait()
        except Exception as e:
            self.logger.error(f"TTS error: {e}")
            print(f"[TTS FALLBACK] {text}")

    # -------------------------------------------------------------------------
    # STT
    # -------------------------------------------------------------------------
    def listen(self, timeout: int = 15, phrase_time_limit: int = 15):
        """Listen from mic and return recognized text."""
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                print("Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except Exception as e:
            print(f"[LISTEN ERROR] {e}")
            return None
    def stop(self):
        """Placeholder for API symmetry (does nothing here)."""
        print("[VOICE] Stopped (no background threads to close).")


# -------------------------------------------------------------------------
# Example usage
# -------------------------------------------------------------------------
def main():
    logging.basicConfig(level=logging.INFO)
    voice = VoiceInteraction()
    SpeakText("hello")
    SpeakText("hello")
    SpeakText("hello")
    user_text = input("Enter text to speak: ")
    voice.speak(user_text)
  #  voice.speak("Done speaking.")
   # voice.speak("This is the third message, spoken in sequence.")
    print("✅ All speech done.")


if __name__ == "__main__":
    main()


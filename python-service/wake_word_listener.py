
import threading
import time

class AlwaysListener:
    def __init__(self, voice_interaction_instance, conversation_manager_instance):
        self.voice_interaction_instance = voice_interaction_instance
        self.conversation_manager_instance = conversation_manager_instance

    def start_listening(self):
        print("AlwaysListener started. Listening for 'hey goose'...")
        while True:
            try:
                print("Listening...")
                speech_text = self.voice_interaction_instance.listen()

                if speech_text:
                    print(f"Heard: '{speech_text}'")
                    if "hello" in speech_text.lower():
                        print("Wake word 'hey goose' detected!")
                        self.conversation_manager_instance.start_accountability_conversation()
                else:
                    print("No speech detected.")

            except Exception as e:
                print(f"An error occurred during listening: {e}")


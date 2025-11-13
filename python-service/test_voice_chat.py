#!/usr/bin/env python3
"""
Voice Chat Test Script
Test the continuous conversation capability
"""

import os
import sys
import logging
import time
from voice_chat import VoiceChat
import dotenv

dotenv.load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Test voice chat functionality"""
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key:")
        print("   Windows: set OPENAI_API_KEY=your_api_key_here")
        print("   or add it to your .env file")
        return
    
    print("🤖 Starting Voice Chat Test...")
    print("💡 This tests CONTINUOUS conversation capability")
    print("🎤 Speak, wait for AI response, then speak again!")
    print("🛑 Press Ctrl+C to stop\n")
    
    try:
        # Initialize voice chat (without session manager for testing)
        voice_chat = VoiceChat(session_manager=None)
        
        # Start listening
        voice_chat.start_listening()
        
        print("🎧 Voice chat is now listening...")
        print("💬 Start a conversation and keep it going!")
        print("")
        print("📝 Conversation Flow:")
        print("   1. Say something (e.g., 'Hi, how are you?')")
        print("   2. Wait 3 seconds for silence detection")
        print("   3. AI will process and respond")
        print("   4. After AI finishes speaking, talk again!")
        print("   5. Repeat steps 1-4 for continuous chat")
        print("")
        print("✨ Try these conversation starters:")
        print("   - 'Hello, I'm testing the voice chat'")
        print("   - 'I have an assignment due tomorrow'")
        print("   - 'I'm feeling overwhelmed today'")
        print("   - 'What should I work on next?'")
        print("")
        print("🔄 The conversation continues until you press Ctrl+C...")
        print("=" * 60)
        
        # Keep the program running and show status updates
        conversation_count = 0
        start_time = time.time()
        
        while True:
            time.sleep(5)  # Check every 5 seconds
            
            # Show periodic status
            runtime = int(time.time() - start_time)
            current_conversations = len(voice_chat.conversation_history) // 2  # User + AI pairs
            
            if current_conversations > conversation_count:
                conversation_count = current_conversations
                print(f"💬 Conversations so far: {conversation_count} | Runtime: {runtime}s")
                
                # Show recent context
                if voice_chat.user_context["mood_energy"] != "neutral":
                    print(f"   😊 Detected mood: {voice_chat.user_context['mood_energy']}")
                
                if voice_chat.user_context["current_tasks"]:
                    print(f"   📋 Tasks mentioned: {', '.join(voice_chat.user_context['current_tasks'][-2:])}")
                
                print("   🎤 Ready for next input...")
                print()
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping voice chat test...")
        print(f"📊 Final stats:")
        if 'voice_chat' in locals():
            total_conversations = len(voice_chat.conversation_history) // 2
            print(f"   💬 Total conversations: {total_conversations}")
            print(f"   🕐 Session duration: {int(time.time() - start_time)}s")
            if voice_chat.user_context["current_tasks"]:
                print(f"   📝 Tasks discussed: {', '.join(voice_chat.user_context['current_tasks'])}")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        if 'voice_chat' in locals():
            voice_chat.stop_listening()
        print("👋 Voice chat test ended!")

if __name__ == "__main__":
    main()

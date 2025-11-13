#!/usr/bin/env python3
"""
Simple Productivity Buddy - URL Logging with Distraction Analysis and Voice Intervention
"""

import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

from goose_integration import GooseClient
from distraction_tracker import DistractionTracker
from voice_interaction import VoiceInteraction
from accountability_friend import ConversationManager
from wake_word_listener import AlwaysListener

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app)

# Global components
tracker = DistractionTracker()
voice = VoiceInteraction()
# ConversationManager needs the global voice instance
conversation_manager = ConversationManager(voice_interaction_instance=voice) 

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "running", "timestamp": datetime.now().isoformat()})

# @app.route('/log/url', methods=['POST'])
# def log_url():
#     """Simple URL logging endpoint (currently commented out)"""
#     try:
#         data = request.get_json() or {}
#         url = data.get('url', 'No URL provided')
#         title = data.get('title', 'No title')
#         timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
#         logger.info(f"📱 TAB SWITCH: {url} | {title}")
        
#         with open('url_log.txt', 'a', encoding='utf-8') as f:
#             f.write(f"{timestamp} | {url} | {title}
        
#         return jsonify({
#             "status": "logged", 
#             "url": url, 
#             "title": title,
#             "timestamp": timestamp
#         })
        
#     except Exception as e:
#         logger.error(f"❌ Error logging URL: {e}")
#         return jsonify({
#             "status": "error",
#             "message": str(e)
#         }), 500

@app.route('/analyze-distraction', methods=['POST'])
def analyze_distraction():
    """Analyze if URL is a distraction using Goose, trigger intervention if needed"""
    try:
        data = request.get_json() or {}
        url = data.get('url', '')
        title = data.get('title', '')
        
        if not url:
            return jsonify({"status": "error", "message": "URL is required"}), 400
        
        logger.info(f"🧠 Analyzing URL for distraction: {url}")
        
        # Call the tracker to log distraction and get intervention message/flag
        # tracker.log_distraction internally calls Goose for analysis
        intervention_message, should_speak = tracker.log_distraction(url, title)
        
        # Prepare response data based on tracker's internal analysis
        # `is_distraction` is true if an intervention message was generated (meaning Goose flagged it)
        is_distraction = (intervention_message is not None)

        response_data = {
            "status": "analyzed",
            "url": url,
            "title": title,
            "is_distraction": is_distraction,
            "analysis": ('YES' if is_distraction else 'NO'),
            "timestamp": datetime.now().isoformat()
        }
        
        # If it's a distraction, include redirect action (browser extension handles this)
        if is_distraction:
            response_data["action"] = "close_tab" # Browser extension interprets this as redirect now
            logger.info(f"🚫 Distraction detected - instructing to redirect tab: {url}")
            
            if should_speak and intervention_message: 
                print("🤖 Intervention needed! Starting voice conversation...")
                # Start the voice conversation loop with Goose's intervention message
                conversation_manager.start_accountability_conversation(initial_message=intervention_message)

        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Error analyzing distraction: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def main():
    """Main application entry point"""
    logger.info("🤖 Starting Simple Productivity Buddy - URL Logger...")
    logger.info("🌐 API server running on http://localhost:5000")
    logger.info("🧠 Goose integration enabled for distraction analysis and voice interventions.")
    
    # Start the always-listening wake word detection in a separate thread
    listener = AlwaysListener(voice_interaction_instance=voice, conversation_manager_instance=conversation_manager)
    wake_word_thread = threading.Thread(target=listener.start_listening, daemon=True)
    wake_word_thread.start()
    logger.info("👂 Always-listening for wake word ('hey goose')...")

    try:
        app.run(host='localhost', port=5000, debug=True, use_reloader=False) 
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

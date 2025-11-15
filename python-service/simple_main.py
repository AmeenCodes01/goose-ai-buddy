#!/usr/bin/env python3
"""
Simple Productivity Buddy - URL Logging with Distraction Analysis and Voice Intervention
"""

import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import ctypes
import sys

from goose_integration import GooseClient
from distraction_tracker import DistractionTracker
from voice_interaction import VoiceInteraction,SpeakText
from accountability_friend import ConversationManager
from wake_word_listener import AlwaysListener
from wifi_scanner import wifi_scanner_agent_loop
from gesture_recognition import GestureRecognizer

# --- Admin Privilege Functions ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin_privileges():
    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        return result > 32  # Success if result > 32
    except Exception as e:
        print("Error:", str(e))
        return False
# -------------------------

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app)

# Global components
voice = VoiceInteraction()
goose = GooseClient()
# ConversationManager needs the global voice instance
conversation_manager = ConversationManager(voice_interaction_instance=voice) 
tracker = DistractionTracker()

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
    print("endpoint hit")
    try:
        data = request.get_json() or {}
        url = data.get('url', '')
        title = data.get('title', '')
        
        print("result:  ", request)
        if not url:
            return jsonify({"status": "error", "message": "URL is required"}), 400

        # Always log the distraction, regardless of analysis status
        tracker.log_distraction(url, title=title)

        # Check if analysis is enabled before calling Goose
        print(tracker.analysis_enabled, "enabled")
        if not tracker.analysis_enabled:
            logger.info(f"🧠 Distraction analysis is currently DISABLED. Skipping Goose for URL: {url}")
            return jsonify({
                "status": "analysis_disabled",
                "url": url,
                "title": title,
                "is_distraction": False, # Assume not a distraction if analysis is off
                "analysis": "DISABLED",
                "timestamp": datetime.now().isoformat()
            })
       
        result = goose.run_task(
                instructions=f"REPLY with only YES or NO. Is this URL {url} a distraction or not for user who's studying/working. ",
                extensions=["developer"],
                no_session=False,
                max_turns=3
            )

        print(result.get("output",""), ": result")
        is_distraction = "YES" in result.get("output","")
        print("YES" in result.get("output"), " ttttt")
        logger.info(f"🧠 Analyzing URL for distraction: {url}")
        
        # Prepare response data based on tracker's internal analysis
        # `is_distraction` is true if an intervention message was generated (meaning Goose flagged it)

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
            
        return jsonify(response_data)
        
    except Exception as e:
        print(data, "request")
        logger.error(f"❌ Error analyzing distraction: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def handle_station_event(ssid):
    """Callback function to handle station detection events from the scanner."""
    instruction_path = "C:/Users/User/productivity-buddy/recipes/commute-instructions.txt"

    result = goose.run_task(
    instructions_file=instruction_path ,
    extensions=["developer"],
    no_session=False,
    max_turns=3
    )
            
    if result.get('success'):
        response = result.get('output', 'Intervention completed')
        SpeakText(response)
        print(f"[SUCCESS] COMMUT5 completed: {response[:100]}...")
        return response
    else:
            error_msg = f"Intervention failed: {result.get('error', 'Unknown error')}"
            print(f"[ERROR] {error_msg}")
            return error_msg
    logger.info(f"🚉 EVENT: Transit station detected via Wi-Fi SSID: {ssid}")

def main():
    """Main application entry point"""
   # --- Admin Privilege Check ---
    if not is_admin():
        print("Admin privileges are required for Wi-Fi scanning.")
        success = request_admin_privileges()
        if success:
            print("Requested admin privileges. Please re-run the script in the new window.")
        else:
            print("Admin privilege request was denied. Wi-Fi scanning will not work.")
        sys.exit()
    else:
        print("Running with admin privileges!")
    # -------------------------

    logger.info("🤖 Starting Simple Productivity Buddy...")
    
    # Start the always-listening wake word detection in a separate thread
    listener = AlwaysListener(voice_interaction_instance=voice, conversation_manager_instance=conversation_manager)
    wake_word_thread = threading.Thread(target=listener.start_listening, daemon=True)
    wake_word_thread.start()
    logger.info("👂 Always-listening for wake word ('hey goose')...")

    # Initialize GestureRecognizer and register callbacks for toggling analysis
    recognizer = GestureRecognizer()
    recognizer.register_gesture_callback("thumbs_up", tracker.enable_analysis)
    recognizer.register_gesture_callback("peace", tracker.disable_analysis)
    
    gesture_thread = threading.Thread(target=recognizer.start_recognition, daemon=True)
    gesture_thread.start()
    logger.info("👋 Gesture recognition started. (Thumbs Up = Enable Analysis, Peace Sign = Disable Analysis)")

    #Start the Wi-Fi scanner agent in a separate thread
    wifi_thread = threading.Thread(target=wifi_scanner_agent_loop, args=(handle_station_event,), daemon=True)
    wifi_thread.start()

    logger.info("🌐 API server running on http://localhost:5000")
    try:
        app.run(host='localhost', port=5000, debug=True, use_reloader=False) 
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

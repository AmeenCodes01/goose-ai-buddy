#!/usr/bin/env python3
"""
Productivity Buddy - Python Service
Main entry point for gesture recognition and system control
"""

import asyncio
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify

from flask_cors import CORS
import threading

from gesture_recognition import GestureRecognizer
from session_manager import SessionManager
from system_controller import SystemController
from content_analyzer import ContentAnalyzer
from voice_chat import VoiceChat

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for browser extension communication
app = Flask(__name__)
CORS(app)  # Enable CORS for browser extension

# Global components
gesture_recognizer = None
session_manager = None
system_controller = None
content_analyzer = None
voice_chat = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "running", "timestamp": datetime.now().isoformat()})

@app.route('/session/start', methods=['POST'])
def start_session():
    """Start a focus session"""
    data = request.get_json() or {}
    duration = data.get('duration', 25)  # Default 25 minutes
    
    logger.info(f"Starting focus session for {duration} minutes")
    session_manager.start_focus_session(duration)
    
    return jsonify({"status": "session_started", "duration": duration})

@app.route('/session/break', methods=['POST'])
def start_break():
    """Start a break session"""
    data = request.get_json() or {}
    duration = data.get('duration', 5)  # Default 5 minutes
    
    logger.info(f"Starting break session for {duration} minutes")
    session_manager.start_break_session(duration)
    
    return jsonify({"status": "break_started", "duration": duration})

@app.route('/session/status', methods=['GET'])

def get_session_status():
    """Get current session status"""
    status = session_manager.get_current_status()
    return jsonify(status)

@app.route('/gesture/latest', methods=['GET'])
def get_latest_gesture():
    """Get the latest detected gesture"""
    gesture = gesture_recognizer.get_latest_gesture()
    return jsonify({"gesture": gesture, "timestamp": datetime.now().isoformat()})

@app.route('/system/block-sites', methods=['POST'])

def block_sites():
    """Block distracting websites"""
    data = request.get_json() or {}
    sites = data.get('sites', [])
    
    system_controller.block_websites(sites)
    return jsonify({"status": "sites_blocked", "count": len(sites)})


@app.route('/analyze/content', methods=['POST'])
def analyze_content():
    """Analyze web page content for work vs distraction classification"""
    try:
        data = request.get_json() or {}
        
        # Analyze the content
        result = content_analyzer.analyze_content(data)
        
        # If it's a distraction during focus mode, handle accordingly
        current_session = session_manager.get_current_status()
        if (current_session.get('state') == 'focus' and 
            result['decision'] == 'DISTRACTION' and 
            result['confidence'] > 0.6):
            
            # Increment blocked count
            session_manager.increment_distractions_blocked()
            
            # Return with close_tab instruction
            result['action'] = 'close_tab'
            result['message'] = f"Distraction blocked: {result['reason']}"
            
        else:
            result['action'] = 'allow'
            result['message'] = f"Content allowed: {result['reason']}"
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Error analyzing content: {e}")
        return jsonify({
            'decision': 'NEUTRAL',
            'confidence': 0.0,
            'action': 'allow',
            'message': f'Analysis error: {str(e)}'
        }), 500

@app.route('/voice/start', methods=['POST'])
def start_voice_chat():
    """Start voice chat listening"""
    voice_chat.start_listening()
    return jsonify({"status": "voice_chat_started"})

@app.route('/voice/stop', methods=['POST'])
def stop_voice_chat():
    """Stop voice chat listening"""
    voice_chat.stop_listening()
    return jsonify({"status": "voice_chat_stopped"})

@app.route('/voice/status', methods=['GET'])
def get_voice_status():
    """Get voice chat status"""
    status = voice_chat.get_conversation_summary()
    return jsonify(status)

@app.route('/voice/check-in', methods=['POST'])
def proactive_check_in():
    """Trigger a proactive check-in"""
    voice_chat.proactive_check_in()
    return jsonify({"status": "check_in_initiated"})
def run_flask_server():
    """Run Flask server in a separate thread"""
    app.run(host='localhost', port=5000, debug=False)

def main():
    """Main application entry point"""
    global gesture_recognizer, session_manager, system_controller, content_analyzer, voice_chat
    
    logger.info("🤖 Starting Productivity Buddy Python Service...")
    
    try:
        # Initialize components
        gesture_recognizer = GestureRecognizer()
        session_manager = SessionManager()
        system_controller = SystemController()
        voice_chat = VoiceChat(session_manager=session_manager)
        content_analyzer = ContentAnalyzer()
        
        # Connect gestures to session management
        def on_wave_gesture():
            logger.info("👋 Wave gesture detected - Starting focus session!")
            session_manager.start_focus_session(25)
        
        def on_stop_gesture():
            logger.info("✋ Stop gesture detected - Starting break session!")
            session_manager.start_break_session(5)
        
        def on_thumbs_up_gesture():
            logger.info("👍 Thumbs up gesture detected - Override action!")
            # Could be used for overriding blocks or approving content
        
        # Register gesture callbacks
        gesture_recognizer.register_gesture_callback("wave", on_wave_gesture)
        gesture_recognizer.register_gesture_callback("stop", on_stop_gesture)
        gesture_recognizer.register_gesture_callback("thumbs_up", on_thumbs_up_gesture)
        
        # Start Flask server in background thread
        flask_thread = threading.Thread(target=run_flask_server, daemon=True)
        flask_thread.start()
        
        logger.info("🌐 API server running on http://localhost:5000")
        logger.info("👋 Starting gesture recognition...")
        
        # Start gesture recognition (main loop)
        gesture_recognizer.start_recognition()
        
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down Productivity Buddy...")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        if gesture_recognizer:
            gesture_recognizer.stop()
        if voice_chat:
            voice_chat.stop_listening()
        logger.info("👋 Goodbye!")

if __name__ == "__main__":
    main()

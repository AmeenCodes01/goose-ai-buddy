#!/usr/bin/env python3
"""
Simple Productivity Buddy - URL Logging with Distraction Analysis
"""

import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from goose_integration import GooseClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "running", "timestamp": datetime.now().isoformat()})

@app.route('/log/url', methods=['POST'])
def log_url():
    """Simple URL logging endpoint"""
    try:
        data = request.get_json() or {}
        url = data.get('url', 'No URL provided')
        title = data.get('title', 'No title')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Simple logging
        logger.info(f"📱 TAB SWITCH: {url} | {title}")
        
        # Also log to file for persistence
        with open('url_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} | {url} | {title}\n")
        
        return jsonify({
            "status": "logged", 
            "url": url, 
            "title": title,
            "timestamp": timestamp
        })
        
    except Exception as e:
        logger.error(f"❌ Error logging URL: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/analyze-distraction', methods=['POST'])
def analyze_distraction():
    """Analyze if URL is a distraction using Goose"""
    try:
        data = request.get_json() or {}
        url = data.get('url', '')
        title = data.get('title', '')
        
        if not url:
            return jsonify({
                "status": "error",
                "message": "URL is required"
            }), 400
        
        logger.info(f"🧠 Analyzing URL for distraction: {url}")
        
        # Initialize Goose client
        client = GooseClient()
        
        # Use Goose to analyze distraction
        result = client.run_task(
            instructions=f"tell is this URL a distraction or not? REPLY WITH ONLY YES/NO {url} {title}",
            no_session=True
        )
        
        # Extract YES/NO from the response
        response_text = result.get('output', '').strip().upper()
        is_distraction = 'YES' in response_text
        
        # Log the analysis result
        analysis_result = "YES" if is_distraction else "NO"
        logger.info(f"🎯 Distraction analysis for {url}: {analysis_result}")
        
        # Prepare response
        response_data = {
            "status": "analyzed",
            "url": url,
            "title": title,
            "is_distraction": is_distraction,
            "analysis": analysis_result,
            "timestamp": datetime.now().isoformat()
        }
        
        # If it's a distraction, include close_tab instruction
        if is_distraction:
            response_data["action"] = "close_tab"
            logger.info(f"🚫 Distraction detected - instructing to close tab: {url}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Error analyzing distraction: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

def main():
    """Main application entry point"""
    logger.info("🤖 Starting Simple Productivity Buddy - URL Logger...")
    logger.info("🌐 API server running on http://localhost:5000")
    logger.info("📝 URLs will be logged to console and url_log.txt")
    logger.info("🧠 Goose integration enabled for distraction analysis")
    
    try:
        app.run(host='localhost', port=5000, debug=False)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Debug server to test endpoints"""

import requests
import time
import threading
import subprocess
import sys

def test_endpoints():
    """Test both endpoints"""
    time.sleep(2)  # Wait for server to start
    
    # Test health endpoint
    try:
        response = requests.get('http://localhost:5000/health')
        print(f"✅ Health: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Health failed: {e}")
    
    # Test log/url endpoint
    try:
        response = requests.post('http://localhost:5000/log/url', json={"url": "test", "title": "test"})
        print(f"✅ Log URL: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Log URL failed: {e}")
    
    # Test analyze-distraction endpoint
    try:
        response = requests.post('http://localhost:5000/analyze-distraction', json={"url": "https://facebook.com", "title": "Facebook"})
        print(f"✅ Analyze: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"❌ Analyze failed: {e}")

if __name__ == "__main__":
    print("🧪 Starting debug test...")
    
    # Start test in background
    test_thread = threading.Thread(target=test_endpoints)
    test_thread.start()
    
    # Import and run the server
    from simple_main import main
    main()

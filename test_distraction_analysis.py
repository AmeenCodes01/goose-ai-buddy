#!/usr/bin/env python3
"""
Test script for distraction analysis integration
"""

import requests
import json

def test_distraction_analysis():
    """Test the distraction analysis endpoint"""
    
    # Test URLs
    test_cases = [
        {
            "url": "https://www.youtube.com/watch?v=waosMIRyDjw&t=4645s",
            "title": "2-HOUR STUDY WITH ME 🌲 in Rainy Forest | 🌧️ Gentle Rain Sounds | Pomodoro 25-5 | Nature Ambience"
        },
        {
            "url": "https://stackoverflow.com/questions/python-help",
            "title": "Python Help - Stack Overflow"
        },
        {
            "url": "https://www.facebook.com",
            "title": "Facebook"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['url']}")
        print(f"Title: {test_case['title']}")
        
        try:
            response = requests.post(
                'http://localhost:5000/analyze-distraction',
                json=test_case,
                timeout=60  # Goose can take time
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Result: {result['analysis']}")
                if result.get('action') == 'close_tab':
                    print("🚫 Would close tab (distraction detected)")
                else:
                    print("✅ Tab allowed")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🤖 Testing Distraction Analysis Integration")
    print("Make sure simple_main.py is running on localhost:5000")
    input("Press Enter to continue...")
    
    test_distraction_analysis()
    
    print("\n✅ Test complete!")

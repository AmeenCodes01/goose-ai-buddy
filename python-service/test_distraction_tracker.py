"""
Test script for DistractionTracker

Demonstrates the basic functionality without triggering actual Goose calls
for quick testing purposes.
"""

from distraction_tracker import DistractionTracker
import time

def test_basic_functionality():
    """Test basic DistractionTracker functionality."""
    print("=== DistractionTracker Basic Test ===\n")
    
    # Create tracker
    tracker = DistractionTracker()
    
    # Test single distraction (should not trigger intervention)
    print("1. Testing single distraction:")
    tracker.log_distraction("https://facebook.com", "Facebook - Social Feed")
    print(f"   Should intervene? {tracker.should_intervene()}")
    
    print("\n2. Testing second distraction (should trigger intervention):")
    # Add a small delay to show timestamps work
    time.sleep(1)
    tracker.log_distraction("https://instagram.com", "Instagram - Stories")
    
    print(f"\n3. Current status:")
    status = tracker.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print(f"\n4. Testing cooldown:")
    print(f"   Should intervene now? {tracker.should_intervene()}")
    
    print(f"\n5. Testing cooldown reset:")
    tracker.reset_cooldown()
    print(f"   Should intervene after reset? {tracker.should_intervene()}")
    
    return tracker

def test_time_window():
    """Test the 10-minute detection window."""
    print("\n=== Time Window Test ===\n")
    
    tracker = DistractionTracker()
    
    # Manually set an old timestamp to test window
    old_distraction = {
        'url': 'https://old-site.com',
        'title': 'Old Distraction',
        'timestamp': time.time() - 700,  # 11+ minutes ago
        'datetime': '2025-11-11T20:20:00.000000'
    }
    
    tracker.distractions.append(old_distraction)
    print("Added old distraction (11+ minutes ago)")
    
    # Add recent distraction
    tracker.log_distraction("https://new-site.com", "Recent Distraction")
    
    recent = tracker._get_recent_distractions()
    print(f"Recent distractions count: {len(recent)} (should be 1, not 2)")
    print(f"Should intervene? {tracker.should_intervene()} (should be False)")

if __name__ == "__main__":
    # Run tests
    tracker = test_basic_functionality()
    test_time_window()
    
    print(f"\n=== Final Status ===")
    final_status = tracker.get_status()
    for key, value in final_status.items():
        print(f"{key}: {value}")

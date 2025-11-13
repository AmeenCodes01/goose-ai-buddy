"""
Minimal DistractionTracker for Productivity Buddy

Tracks distraction events and triggers interventions using GooseClient.
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from goose_integration import GooseClient


class DistractionTracker:
    """
    Minimal distraction tracker with intervention capabilities.
    
    Features:
    - Track distraction events with timestamps
    - Detect when intervention is needed (2+ distractions in 10 minutes)
    - Trigger Goose-based interventions
    - Simple logging via print statements
    """
    
    def __init__(self):
        """Initialize the distraction tracker."""
        self.distractions: List[Dict] = []
        # self.last_intervention_time: Optional[float] = None # Cooldown removed
        self.goose_client = GooseClient()
        # self.intervention_cooldown = 3600  # 1 hour in seconds # Cooldown removed
        self.detection_window = 600  # 10 minutes in seconds
        self.intervention_threshold = 2  # 2+ distractions triggers intervention
        
        print("DistractionTracker initialized")
    
    def log_distraction(self, url: str, title: str) -> None:
        """
        Log a distraction event with timestamp.
        
        Args:
            url: The URL that was accessed
            title: The title/description of the distraction
        """
        distraction = {
            'url': url,
            'title': title,
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat()
        }
        
        self.distractions.append(distraction)
        print(f"[DISTRACTION] {title} - {url} at {distraction['datetime']}")
        
        # Check if intervention is needed
        if self.should_intervene():
            recent_distractions = self._get_recent_distractions()
            response = self.start_intervention(recent_distractions)
            print(f"[INTERVENTION] Triggered - Response: {response}")
        
        return response
    
    def should_intervene(self) -> bool:
        """
        Check if intervention is needed based on recent activity.
        
        Returns:
            True if intervention should be triggered, False otherwise
        """
        # Cooldown logic removed per instructions
        # if self._is_in_cooldown():
        #     print("[COOLDOWN] Intervention skipped - still in cooldown period")
        #     return False
        
        # Get recent distractions
        recent_distractions = self._get_recent_distractions()
        
        # Check threshold
        should_trigger = len(recent_distractions) >= self.intervention_threshold
        
        if should_trigger:
            print(f"[TRIGGER] {len(recent_distractions)} distractions in last 10 minutes - intervention needed")
        
        return should_trigger
    
    def start_intervention(self, recent_distractions: List[Dict]) -> str:
        """
        Start an intervention using GooseClient.
        
        Args:
            recent_distractions: List of recent distraction events
            
        Returns:
            String response from Goose intervention
        """
        # Cooldown update logic removed
        # self.last_intervention_time = time.time()
        
        # Prepare distraction context
        distraction_context = []
        for d in recent_distractions:
            distraction_context.append(f"- {d['title']} ({d['url']}) at {d['datetime']}")
        
        context_text = "".join(distraction_context)
        
        # Create friend-like intervention instructions
        instructions = f"""
        Hey there! I noticed you've been jumping around a bit recently. You've visited a few sites that might be pulling you away from your tasks, like:
        {context_text}
        
        It seems like something might be on your mind today, or perhaps you're feeling a little scattered. What's going on? No judgment at all, just wanted to check in and see how I can help you get back on track.
        
        If you'd like, I can suggest a quick refocus technique or a helpful productivity tip. Just let me know what you need or if you want to chat for a bit.
        """
        
        try:
            print("[GOOSE] Starting productivity intervention...")
            result = self.goose_client.run_task(
                instructions=instructions,
                extensions=["developer"],
                no_session=True,
                max_turns=3
            )
            
            if result.get('success'):
                response = result.get('output', 'Intervention completed')
                print(f"[SUCCESS] Intervention completed: {response[:100]}...")
                return response
            else:
                error_msg = f"Intervention failed: {result.get('error', 'Unknown error')}"
                print(f"[ERROR] {error_msg}")
                return error_msg
                
        except Exception as e:
            error_msg = f"Intervention error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return error_msg
    
    # Cooldown reset method removed
    # def reset_cooldown(self) -> None:
    #     """Reset the intervention cooldown manually."""
    #     self.last_intervention_time = None
    #     print("[RESET] Intervention cooldown reset")
    
    def _get_recent_distractions(self) -> List[Dict]:
        """
        Get distractions from the last 10 minutes.
        
        Returns:
            List[Dict]: A list of distraction events within the detection window.
        """
        current_time = time.time()
        cutoff_time = current_time - self.detection_window
        
        # Filter out old distractions and keep only recent ones
        self.distractions = [d for d in self.distractions if d['timestamp'] > cutoff_time]
        return self.distractions
    
    # Cooldown check method removed
    # def _is_in_cooldown(self) -> bool:
    #     """Check if we're still in the intervention cooldown period."""
    #     if self.last_intervention_time is None:
    #         return False
        
    #     current_time = time.time()
    #     time_since_last = current_time - self.last_intervention_time
        
    #     return time_since_last < self.intervention_cooldown
    
    def get_status(self) -> Dict:
        """
        Get current tracker status for debugging."""
        recent_distractions = self._get_recent_distractions()
        
        return {
            'total_distractions': len(self.distractions),
            'recent_distractions': len(recent_distractions),
            'last_intervention': None, # Cooldown removed
            'in_cooldown': False, # Cooldown removed
            'cooldown_remaining': 0 # Cooldown removed
        }


# Example usage and testing
if __name__ == "__main__":
    # Create tracker
    tracker = DistractionTracker()
    
    # Simulate some distractions
    print("=== Testing DistractionTracker ===")
    
    # First distraction
    tracker.log_distraction("https://youtube.com/cats", "YouTube - Funny Cat Videos")
    
    # Second distraction (should trigger intervention without cooldown)
    tracker.log_distraction("https://reddit.com/r/aww", "Reddit - Cute Animals")
    
    # Check status
    status = tracker.get_status()
    print(f"Status: {status}")
    
    # Third distraction - should also trigger (no cooldown)
    tracker.log_distraction("https://twitter.com", "Twitter Feed")
    
    # Now, if enough time passes, distractions will clear
    print("Waiting for 11 minutes to clear distractions...")
    time.sleep(660) # 11 minutes
    
    status_after_delay = tracker.get_status()
    print(f"Status after delay: {status_after_delay}")
    print(f"Should intervene now (after delay)? {tracker.should_intervene()}")

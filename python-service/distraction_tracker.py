"""Minimal DistractionTracker for Productivity Buddy

Tracks distraction events and triggers interventions using GooseClient.
"""

import time
from datetime import datetime
from typing import List, Dict, Optional
from goose_integration import GooseClient
from voice_interaction import VoiceInteraction,SpeakText
import logging
logger = logging.getLogger(__name__)



class DistractionTracker:
    """
    Minimal distraction tracker with intervention capabilities.

    Features:
    - Track distraction events with timestamps
    - Detect when intervention is needed (2+ distractions in 10 minutes)
- Trigger Goose-based interventions
    - Simple logging via print statements
    """
    instruction_path = "C:/Users/User/productivity-buddy/recipes/distracted-instructions.txt"
    def __init__(self):
        """Initialize the distraction tracker."""
        self.distractions: List[Dict] = []
        self.goose_client = GooseClient()
        self.detection_window = 600  # 10 minutes in seconds
        self.intervention_threshold = 1  # 2+ distractions triggers intervention
        self.analysis_enabled = True  # State flag for toggling analysis

        print("DistractionTracker initialized")

    def enable_analysis(self):
        """Enable distraction analysis."""
        if not self.analysis_enabled:
            self.analysis_enabled = True
            print("✅ Distraction analysis has been ENABLED.")
            SpeakText("Distraction analysis enabled.")

    def disable_analysis(self):
        """Disable distraction analysis."""
        if self.analysis_enabled:
            self.analysis_enabled = False
            print("❌ Distraction analysis has been DISABLED.")
            SpeakText("Distraction analysis disabled.")

    def log_distraction(self, url: str, title: str) -> Optional[str]:
        """
        Log a distraction event and trigger intervention if analysis is enabled.
        """
        # If analysis is disabled, do nothing.
        if not self.analysis_enabled:
            print(f"[SKIPPED] Analysis is disabled. Ignoring URL: {url}")
            return None

        timestamp = time.time()
        distraction = {
            'url': url,
            'title': title,
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp).isoformat()
        }

        # Deduplicate: avoid logging same URL within detection window
        cutoff = timestamp - self.detection_window
        if not any(d['url'] == url and d['timestamp'] > cutoff for d in self.distractions):
            self.distractions.append(distraction)
            print(f"[LOGGED] {title} - {url}")
        else:
            print(f"[SKIPPED LOG] Duplicate distraction ignored: {title} - {url}")

        # Check if intervention is needed
        response = None
        if self.should_intervene():
            recent_distractions = self._get_recent_distractions()
            response = self.start_intervention(recent_distractions)
            print(f"[INTERVENTION] Triggered - Response: {response}")

        return response

    def should_intervene(self) -> bool:
        """Check if intervention is needed based on recent activity."""
        recent_distractions = self._get_recent_distractions()
        should_trigger = len(recent_distractions) >= self.intervention_threshold

        if should_trigger:
            print(f"[TRIGGER] {len(recent_distractions)} distractions in last 10 minutes - intervention needed")

        return should_trigger

    def start_intervention(self, recent_distractions: List[Dict]) -> str:
        """Start an intervention using GooseClient."""
        try:
            print("[GOOSE] Starting productivity intervention...")
            context_text = "\n".join(
                f"- {d['title']} ({d['url']}) at {d['datetime']}" for d in recent_distractions
            )
            print("[GOOSE] Recent distractions:\n" + context_text)

            result = self.goose_client.run_task(
                instructions_file=self.instruction_path,
                extensions=["developer"],
                no_session=False,
                max_turns=3
            )
            
            if result.get('success'):
                response = result.get('output', 'Intervention completed')
                SpeakText(response)
                print(f"[SUCCESS] Intervention completed: {response[:100]}...")
                return response
            else:
                error_msg = f"Intervention failed: {result.get('error', 'Unknown error')}"
                print(f"[ERROR] {error_msg}")
                return error_msg

            return "Intervention simulated (GooseClient call commented out)"

        except Exception as e:
            error_msg = f"Intervention error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return error_msg

    def _get_recent_distractions(self) -> List[Dict]:
        """Get distractions from the last 10 minutes."""
        cutoff_time = time.time() - self.detection_window
        return [d for d in self.distractions if d['timestamp'] > cutoff_time]

    def get_status(self) -> Dict:
        """Get current tracker status for debugging."""
        recent_distractions = self._get_recent_distractions()
        return {
            'total_distractions': len(self.distractions),
            'recent_distractions': len(recent_distractions),
            'last_intervention': None,
            'in_cooldown': False,
            'cooldown_remaining': 0
        }

    def trigger_url_analysis(self):
        """
        Triggers a URL analysis, typically from a gesture.
        This simulates a browser event for a generic "distraction" to initiate Goose analysis.
        """
        logger.info("Gesture-triggered URL analysis initiated.")
        # Use a dummy URL/title to trigger the existing distraction analysis flow
        self.log_distraction(url="gesture://analysis_trigger", title="Gesture Triggered Analysis")


# Example usage and testing
if __name__ == "__main__":
    tracker = DistractionTracker()
    print("=== Testing DistractionTracker ===")

    tracker.log_distraction("https://youtube.com/cats", "YouTube - Funny Cat Videos")
    tracker.log_distraction("https://youtube.com/cats", "YouTube - Funny Cat Videos")
    tracker.log_distraction("https://youtube.com/cats", "YouTube - Funny Cat Videos")
    tracker.log_distraction("https://youtube.com/cats", "YouTube - Funny Cat Videos")
    tracker.log_distraction("https://reddit.com/r/aww", "Reddit - Cute Animals")
    tracker.log_distraction("https://reddit.com/r/aww", "Reddit - Cute Animals")  # Should be skipped

    print("Current distractions:")
    for d in tracker.distractions:
        print(d)

    status = tracker.get_status()
    print(f"Status: {status}")
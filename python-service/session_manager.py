"""
Session Manager Module
Handles focus sessions, breaks, and productivity tracking
"""

import time
import json
import logging
import threading
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class SessionState(Enum):
    IDLE = "idle"
    FOCUS = "focus"
    BREAK = "break"

class SessionManager:
    def __init__(self):
        self.current_state = SessionState.IDLE
        self.session_start_time = None
        self.session_duration = 0  # in minutes
        self.session_timer = None
        
        # Statistics
        self.daily_stats = {
            "focus_minutes": 0,
            "break_minutes": 0,
            "sessions_completed": 0,
            "distractions_blocked": 0
        }
        
        # Load previous stats if available
        self._load_stats()
        
        # Callbacks for session events
        self.session_callbacks = {
            "session_start": [],
            "session_end": [],
            "break_start": [],
            "break_end": []
        }
    
    def start_focus_session(self, duration_minutes=25):
        """Start a focus session"""
        if self.current_state != SessionState.IDLE:
            logger.warning("⚠️ Cannot start focus session - already in session")
            return False
        
        self.current_state = SessionState.FOCUS
        self.session_start_time = datetime.now()
        self.session_duration = duration_minutes
        
        logger.info(f"🎯 Starting focus session for {duration_minutes} minutes")
        
        # Set timer for session end
        self.session_timer = threading.Timer(
            duration_minutes * 60, 
            self._on_focus_session_end
        )
        self.session_timer.start()
        
        # Trigger callbacks
        self._trigger_callbacks("session_start")
        
        return True
    
    def start_break_session(self, duration_minutes=5):
        """Start a break session"""
        if self.current_state == SessionState.BREAK:
            logger.warning("⚠️ Already on break")
            return False
        
        # If coming from focus session, mark it as completed
        if self.current_state == SessionState.FOCUS:
            self._complete_focus_session()
        
        self.current_state = SessionState.BREAK
        self.session_start_time = datetime.now()
        self.session_duration = duration_minutes
        
        logger.info(f"☕ Starting break session for {duration_minutes} minutes")
        
        # Set timer for break end
        self.session_timer = threading.Timer(
            duration_minutes * 60,
            self._on_break_session_end
        )
        self.session_timer.start()
        
        # Trigger callbacks
        self._trigger_callbacks("break_start")
        
        return True
    
    def end_current_session(self):
        """Manually end the current session"""
        if self.current_state == SessionState.IDLE:
            return False
        
        if self.session_timer:
            self.session_timer.cancel()
        
        if self.current_state == SessionState.FOCUS:
            self._on_focus_session_end()
        elif self.current_state == SessionState.BREAK:
            self._on_break_session_end()
        
        return True
    
    def _on_focus_session_end(self):
        """Called when focus session timer expires"""
        logger.info("⏰ Focus session completed!")
        self._complete_focus_session()
        
        # Trigger callbacks
        self._trigger_callbacks("session_end")
        
        # Auto-start break session
        self.start_break_session(5)
    
    def _on_break_session_end(self):
        """Called when break session timer expires"""
        logger.info("⏰ Break session completed!")
        
        # Update stats
        if self.session_start_time:
            elapsed = (datetime.now() - self.session_start_time).total_seconds() / 60
            self.daily_stats["break_minutes"] += elapsed
        
        self.current_state = SessionState.IDLE
        self.session_start_time = None
        
        # Trigger callbacks
        self._trigger_callbacks("break_end")
        
        # Save stats
        self._save_stats()
    
    def _complete_focus_session(self):
        """Complete the current focus session"""
        if self.session_start_time:
            elapsed = (datetime.now() - self.session_start_time).total_seconds() / 60
            self.daily_stats["focus_minutes"] += elapsed
            self.daily_stats["sessions_completed"] += 1
        
        self.current_state = SessionState.IDLE
        self.session_start_time = None
    
    def get_current_status(self):
        """Get current session status"""
        status = {
            "state": self.current_state.value,
            "duration_minutes": self.session_duration,
            "elapsed_minutes": 0,
            "remaining_minutes": 0
        }
        
        if self.session_start_time:
            elapsed = (datetime.now() - self.session_start_time).total_seconds() / 60
            status["elapsed_minutes"] = round(elapsed, 1)
            status["remaining_minutes"] = max(0, self.session_duration - elapsed)
        
        return status
    
    def get_daily_stats(self):
        """Get daily productivity statistics"""
        return self.daily_stats.copy()
    
    def increment_distractions_blocked(self):
        """Increment the count of blocked distractions"""
        self.daily_stats["distractions_blocked"] += 1
        logger.info(f"🚫 Distraction blocked (total today: {self.daily_stats['distractions_blocked']})")
    
    def register_callback(self, event, callback):
        """Register a callback for session events"""
        if event in self.session_callbacks:
            self.session_callbacks[event].append(callback)
            logger.info(f"📝 Registered callback for event: {event}")
    
    def _trigger_callbacks(self, event):
        """Trigger all callbacks for an event"""
        if event in self.session_callbacks:
            for callback in self.session_callbacks[event]:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"❌ Error in session callback: {e}")
    
    def _save_stats(self):
        """Save daily statistics to file"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            stats_data = {
                "date": today,
                "stats": self.daily_stats
            }
            
            with open("daily_stats.json", "w") as f:
                json.dump(stats_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Error saving stats: {e}")
    
    def _load_stats(self):
        """Load daily statistics from file"""
        try:
            with open("daily_stats.json", "r") as f:
                data = json.load(f)
                
            # Check if stats are from today
            today = datetime.now().strftime("%Y-%m-%d")
            if data.get("date") == today:
                self.daily_stats.update(data.get("stats", {}))
                logger.info("📊 Loaded daily statistics")
            else:
                logger.info("📊 Starting fresh daily statistics")
                
        except FileNotFoundError:
            logger.info("📊 No previous statistics found, starting fresh")
        except Exception as e:
            logger.error(f"❌ Error loading stats: {e}")

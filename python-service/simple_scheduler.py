"""
SimpleScheduler class for delayed reminders using Python threading.
"""

import threading
from typing import Callable

class SimpleScheduler:
    """
    A simple, in-process scheduler for delayed reminders using Python threading.
    """
    def __init__(self):
        self.timers = []
        print("SimpleScheduler initialized.")

    def _timer_callback(self, message: str, callback: Callable):
        """Internal callback for the threading.Timer."""
        print(f"[SCHEDULER] Executing scheduled check-in: '{message}'")
        callback(message)

    def schedule_check_in(self, delay_minutes: int, check_in_message: str, callback_function: Callable) -> None:
        """
        Schedules a check-in reminder for a specified delay.

        Args:
            delay_minutes: The delay in minutes before the check-in.
            check_in_message: The message to pass to the callback function.
            callback_function: The function to call when the timer expires.
        """
        delay_seconds = delay_minutes * 60
        timer = threading.Timer(
            delay_seconds,
            self._timer_callback,
            args=[check_in_message, callback_function]
        )
        self.timers.append(timer)
        timer.start()
        print(f"[SCHEDULER] Scheduled check-in in {delay_minutes} minutes with message: '{check_in_message}'")

    def cancel_all_check_ins(self):
        """Cancels all pending scheduled check-ins."""
        for timer in self.timers:
            timer.cancel()
        self.timers = []
        print("[SCHEDULER] All pending check-ins cancelled.")

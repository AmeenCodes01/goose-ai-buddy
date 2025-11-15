"""
Gesture Recognition Module (Rewritten for Simplicity and Reliability)
Uses MediaPipe for hand tracking and gesture detection.
"""

import cv2
import mediapipe as mp
import logging
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class GestureRecognizer:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,  # Focus on one hand for clarity
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.cap = None
        self.running = False
        self.gesture_callbacks = {}
        
        # Cooldown parameters
        self.gesture_cooldown = 2.0  # seconds
        self.last_gesture_time = {}
        
    def start_recognition(self):
        """Start the gesture recognition loop."""
        self.running = True
        
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                logger.error("❌ Cannot open camera")
                return
                
            logger.info("📹 Camera opened successfully. Press 'q' in the window to quit.")
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb_frame)
                
                gesture = self._detect_gesture(results)
                if gesture:
                    self._handle_gesture(gesture)
                
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        self.mp_drawing.draw_landmarks(
                            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                cv2.imshow('Gesture Recognition', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except Exception as e:
            logger.error(f"❌ Error in gesture recognition loop: {e}")
        finally:
            self.stop()
    
    def _detect_gesture(self, results) -> Optional[str]:
        """Detects a gesture from the hand landmarks."""
        if not results.multi_hand_landmarks:
            return None
            
        for hand_landmarks in results.multi_hand_landmarks:
            return self._classify_hand_gesture(hand_landmarks)
        
        return None
    
    def _classify_hand_gesture(self, hand_landmarks) -> Optional[str]:
        """
        Classifies the hand gesture using a simple and reliable finger-counting method.
        """
        try:
            landmarks = hand_landmarks.landmark
            
            # This list will hold a boolean for each finger [Thumb, Index, Middle, Ring, Pinky]
            fingers_up = []

            # --- Thumb ---
            # A common robust check is to see if the thumb tip's X-coordinate is further
            # out than its IP joint's X-coordinate (assuming a vertical right hand).
            # This helps distinguish a thumbs-up from a closed fist where the thumb is tucked in.
            # We get the handedness to make this work for both left and right hands.
            hand_label = "left" # Placeholder
            # Note: handedness detection is not perfectly reliable, but we can try.
            # A simpler check is just comparing y-coordinates, which we'll use for consistency.
            if landmarks[self.mp_hands.HandLandmark.THUMB_TIP].y < landmarks[self.mp_hands.HandLandmark.THUMB_IP].y:
                fingers_up.append(True)
            else:
                fingers_up.append(False)

            # --- Other 4 Fingers ---
            # A finger is "up" if its tip is above its PIP joint (the middle joint).
            finger_tip_indices = [8, 12, 16, 20]
            finger_pip_indices = [6, 10, 14, 18]

            for i in range(4):
                if landmarks[finger_tip_indices[i]].y < landmarks[finger_pip_indices[i]].y:
                    fingers_up.append(True)
                else:
                    fingers_up.append(False)

            # --- Gesture Matching ---
            # Now we match the boolean list to our desired gestures.
            
            # Thumbs Up: [True, False, False, False, False]
            if fingers_up == [True, False, False, False, False]:
                return "thumbs_up"
            
            # Peace Sign: [False, True, True, False, False]
            if fingers_up == [False, True, True, False, False]:
                return "peace"
            
            # Open Hand: All five fingers are up
            if all(fingers_up):
                return "open"
            
            # Closed Fist: No fingers are up
            if not any(fingers_up):
                return "closed"

        except Exception:
            return None
        
        return None
    
    def _handle_gesture(self, gesture: str):
        """Handles a detected gesture, checking cooldowns and triggering callbacks."""
        current_time = time.time()
        
        if current_time - self.last_gesture_time.get(gesture, 0) > self.gesture_cooldown:
            self.last_gesture_time[gesture] = current_time
            logger.info(f"👋 Gesture Detected: {gesture}")
            
            if gesture in self.gesture_callbacks:
                try:
                    self.gesture_callbacks[gesture]()
                except Exception as e:
                    logger.error(f"❌ Error in gesture callback for '{gesture}': {e}")
    
    def register_gesture_callback(self, gesture: str, callback: Callable):
        """Registers a callback function for a specific gesture."""
        self.gesture_callbacks[gesture] = callback
        logger.info(f"📝 Registered callback for gesture: '{gesture}'")
    
    def stop(self):
        """Stops the recognition loop and releases resources."""
        self.running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        logger.info("🛑 Gesture recognition stopped.")
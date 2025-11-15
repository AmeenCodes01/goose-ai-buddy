import cv2
import mediapipe as mp
import numpy as np
import logging
import threading
import time
from datetime import datetime
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
        """Start the gesture recognition loop"""
        self.running = True
        
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                logger.error("❌ Cannot open camera")
                return
                
            logger.info("📹 Camera opened successfully")
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning("⚠️ Failed to read frame")
                    continue
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process the frame
                results = self.hands.process(rgb_frame)
                
                # Detect gestures
                gesture = self._detect_gesture(results)
                if gesture:
                    self._handle_gesture(gesture)
                
                # Draw hand landmarks
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        self.mp_drawing.draw_landmarks(
                            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                        )
                
                # Display the frame
                cv2.imshow('Productivity Buddy - Gesture Recognition', frame)
                
                # Exit on 'q' key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except Exception as e:
            logger.error(f"❌ Error in gesture recognition: {e}")
        finally:
            self.stop()
    
    def _detect_gesture(self, results):
        """Detect specific gestures from hand landmarks"""
        if not results.multi_hand_landmarks:
            return None
            
        for hand_landmarks in results.multi_hand_landmarks:
            # Detect different gestures
            gesture = self._classify_hand_gesture(hand_landmarks)
            if gesture:
                return gesture
        
        return None
    
    def _classify_hand_gesture(self, hand_landmarks):
        """Classify the hand gesture based on landmarks into 'open' or 'closed'."""
        try:
            landmarks = hand_landmarks.landmark
            
            # Get the y-coordinates of fingertips and their corresponding MCP joints
            index_tip_y = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP].y
            index_mcp_y = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_MCP].y
            middle_tip_y = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y
            middle_mcp_y = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP].y
            ring_tip_y = landmarks[self.mp_hands.HandLandmark.RING_FINGER_TIP].y
            ring_mcp_y = landmarks[self.mp_hands.HandLandmark.RING_FINGER_MCP].y
            pinky_tip_y = landmarks[self.mp_hands.HandLandmark.PINKY_TIP].y
            pinky_mcp_y = landmarks[self.mp_hands.HandLandmark.PINKY_MCP].y

            # An open hand has fingertips above (lower y-value) the base of the fingers
            is_open = (index_tip_y < index_mcp_y and
                       middle_tip_y < middle_mcp_y and
                       ring_tip_y < ring_mcp_y and
                       pinky_tip_y < pinky_mcp_y)

            # A closed hand has fingertips below (higher y-value) the base
            is_closed = (index_tip_y > index_mcp_y and
                         middle_tip_y > middle_mcp_y)

            if is_open:
                return "open"
            elif is_closed:
                return "closed"
        except Exception:
            return None
        return None

    def _handle_gesture(self, gesture: str):
        """Handle a detected gesture, checking cooldowns and triggering callbacks."""
        current_time = time.time()
        
        if current_time - self.last_gesture_time.get(gesture, 0) > self.gesture_cooldown:
            self.last_gesture_time[gesture] = current_time
            logger.info(f"👋 Gesture Detected: {gesture}")
            
            if gesture in self.gesture_callbacks:
                try:
                    self.gesture_callbacks[gesture]()
                except Exception as e:
                    logger.error(f"❌ Error in gesture callback for '{gesture}': {e}")

    def register_gesture_callback(self, gesture, callback):
        """Register a callback for a specific gesture"""
        self.gesture_callbacks[gesture] = callback
        logger.info(f"📝 Registered callback for gesture: {gesture}")
    
    def get_latest_gesture(self):
        """Get the latest detected gesture"""
        gesture = self.latest_gesture
        self.latest_gesture = None  # Clear after reading
        return gesture
    
    def stop(self):
        """Stop the gesture recognition"""
        self.running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        logger.info("🛑 Gesture recognition stopped")

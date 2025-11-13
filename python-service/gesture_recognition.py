"""
Gesture Recognition Module
Uses MediaPipe for hand tracking and gesture detection
"""

import cv2
import mediapipe as mp
import numpy as np
import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class GestureRecognizer:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.cap = None
        self.running = False
        self.latest_gesture = None
        self.gesture_callbacks = {}
        
        # Gesture detection parameters
        self.gesture_cooldown = 2.0  # seconds between same gesture
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
                gesture = self._detect_gesture(results, frame)
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
    
    def _detect_gesture(self, results, frame):
        """Detect specific gestures from hand landmarks"""
        if not results.multi_hand_landmarks:
            return None
            
        for hand_landmarks in results.multi_hand_landmarks:
            landmarks = hand_landmarks.landmark
            
            # Get hand landmarks as numpy array
            h, w, _ = frame.shape
            hand_points = np.array([[lm.x * w, lm.y * h] for lm in landmarks])
            
            # Detect different gestures
            gesture = self._classify_hand_gesture(hand_points, landmarks)
            if gesture:
                return gesture
        
        return None
    
    def _classify_hand_gesture(self, hand_points, landmarks):
        """Classify the hand gesture based on landmarks"""
        
        # Get finger tip and base positions
        finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        finger_bases = [3, 6, 10, 14, 18]
        
        # Check if fingers are extended
        fingers_up = []
        
        # Thumb (different logic due to orientation)
        if landmarks[finger_tips[0]].x > landmarks[finger_bases[0]].x:
            fingers_up.append(1)
        else:
            fingers_up.append(0)
            
        # Other fingers
        for i in range(1, 5):
            if landmarks[finger_tips[i]].y < landmarks[finger_bases[i]].y:
                fingers_up.append(1)
            else:
                fingers_up.append(0)
        
        # Gesture classification
        total_fingers = sum(fingers_up)
        
        if total_fingers == 5:
            return "wave"  # Open palm - start focus session
        elif total_fingers == 0:
            return "stop"  # Closed fist - start break
        elif fingers_up == [1, 1, 0, 0, 0]:  # Thumb and index up
            return "thumbs_up"  # Override/approve
        elif fingers_up == [0, 1, 0, 0, 0]:  # Only index finger
            return "point"  # Point gesture
        
        return None
    
    def _handle_gesture(self, gesture):
        """Handle detected gesture with cooldown"""
        current_time = time.time()
        
        # Check cooldown
        if gesture in self.last_gesture_time:
            if current_time - self.last_gesture_time[gesture] < self.gesture_cooldown:
                return
        
        self.last_gesture_time[gesture] = current_time
        self.latest_gesture = gesture
        
        logger.info(f"👋 Gesture detected: {gesture}")
        
        # Trigger callbacks
        if gesture in self.gesture_callbacks:
            try:
                self.gesture_callbacks[gesture]()
            except Exception as e:
                logger.error(f"❌ Error in gesture callback: {e}")
    
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

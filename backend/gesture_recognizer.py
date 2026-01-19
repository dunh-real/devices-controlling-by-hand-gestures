import cv2
import mediapipe as mp
import numpy as np
from collections import deque

class GestureRecognizer:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Lưu lịch sử để detect gesture động
        self.distance_history = deque(maxlen=10)
        
    def count_fingers(self, landmarks):
        """Đếm số ngón tay đang giơ"""
        fingers = []
        
        # Ngón cái (so sánh x)
        if landmarks[4].x < landmarks[3].x:  # Tay phải
            fingers.append(1)
        else:
            fingers.append(0)
            
        # 4 ngón còn lại (so sánh y)
        finger_tips = [8, 12, 16, 20]
        finger_pips = [6, 10, 14, 18]
        
        for tip, pip in zip(finger_tips, finger_pips):
            if landmarks[tip].y < landmarks[pip].y:
                fingers.append(1)
            else:
                fingers.append(0)
                
        return sum(fingers)
    
    def detect_pinch(self, landmarks):
        """Phát hiện cử chỉ zoom (khoảng cách ngón cái - ngón trỏ)"""
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        
        distance = np.sqrt(
            (thumb_tip.x - index_tip.x)**2 + 
            (thumb_tip.y - index_tip.y)**2
        )
        
        self.distance_history.append(distance)
        
        if len(self.distance_history) >= 5:
            # Zoom in: khoảng cách giảm
            if self.distance_history[-1] < self.distance_history[0] - 0.05:
                return "zoom_in"
            # Zoom out: khoảng cách tăng
            elif self.distance_history[-1] > self.distance_history[0] + 0.05:
                return "zoom_out"
        
        return "pinch_hold"
    
    def detect_swipe(self, landmarks):
        """Phát hiện vuốt tay trái/phải"""
        wrist = landmarks[0]
        middle_finger = landmarks[9]
        
        # Tính góc của bàn tay
        dx = middle_finger.x - wrist.x
        
        if abs(dx) > 0.15:  # Threshold
            return "swipe_right" if dx > 0 else "swipe_left"
        
        return None
    
    def detect_rotation(self, landmarks):
        """Phát hiện xoay tay (cho điều hòa)"""
        # Tính góc giữa cổ tay và ngón giữa
        wrist = landmarks[0]
        middle = landmarks[9]
        
        angle = np.arctan2(middle.y - wrist.y, middle.x - wrist.x)
        angle_deg = np.degrees(angle)
        
        if angle_deg > 45:
            return "rotate_up"
        elif angle_deg < -45:
            return "rotate_down"
        
        return None
    
    def process_frame(self, frame):
        """Xử lý frame và trả về kết quả"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)
        
        gesture_data = {
            'hand_detected': False,
            'finger_count': 0,
            'gesture': None,
            'landmarks': None
        }
        
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            gesture_data['hand_detected'] = True
            gesture_data['landmarks'] = hand_landmarks
            
            # Đếm ngón tay
            gesture_data['finger_count'] = self.count_fingers(
                hand_landmarks.landmark
            )
            
            # Phát hiện các gesture
            pinch_gesture = self.detect_pinch(hand_landmarks.landmark)
            swipe_gesture = self.detect_swipe(hand_landmarks.landmark)
            rotation_gesture = self.detect_rotation(hand_landmarks.landmark)
            
            # Ưu tiên gesture
            if swipe_gesture:
                gesture_data['gesture'] = swipe_gesture
            elif pinch_gesture and pinch_gesture != "pinch_hold":
                gesture_data['gesture'] = pinch_gesture
            elif rotation_gesture:
                gesture_data['gesture'] = rotation_gesture
            
            # Vẽ landmarks lên frame
            self.mp_draw.draw_landmarks(
                frame, 
                hand_landmarks, 
                self.mp_hands.HAND_CONNECTIONS
            )
        
        return gesture_data, frame
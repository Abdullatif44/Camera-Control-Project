import pyautogui
import cv2
import mediapipe as mp

class GestureRecognition:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1, 
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.prev_x, self.prev_y = 0, 0

    def detect_gestures(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb_image)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                self.map_gestures(hand_landmarks)

        return frame

    def map_gestures(self, landmarks):
        screen_w, screen_h = pyautogui.size()
        finger = landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]

        # Invert x if mirrored camera
        x = screen_w - int(finger.x * screen_w)
        y = int(finger.y * screen_h)

        # Smooth mouse movement
        smooth_x = self.prev_x + (x - self.prev_x) * 0.2
        smooth_y = self.prev_y + (y - self.prev_y) * 0.2
        pyautogui.moveTo(smooth_x, smooth_y)
        self.prev_x, self.prev_y = smooth_x, smooth_y

        # Gesture actions
        if self.is_click(landmarks):
            pyautogui.click()

        elif self.is_right_click(landmarks):
            pyautogui.click(button='right')

    def is_click(self, landmarks):
        index_tip = landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        thumb_tip = landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]

        distance = ((index_tip.x - thumb_tip.x) ** 2 +
                    (index_tip.y - thumb_tip.y) ** 2) ** 0.5
        return distance < 0.05  # Adjust threshold as needed

    def is_right_click(self, landmarks):
        middle_tip = landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        thumb_tip = landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]

        distance = ((middle_tip.x - thumb_tip.x) ** 2 +
                    (middle_tip.y - thumb_tip.y) ** 2) ** 0.5
        return distance < 0.05  # Adjust as needed

    def is_fist(self, landmarks):
        # Check if 3+ fingers are folded (approximate "fist")
        tips = [self.mp_hands.HandLandmark.INDEX_FINGER_TIP,
                self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
                self.mp_hands.HandLandmark.RING_FINGER_TIP,
                self.mp_hands.HandLandmark.PINKY_TIP]
        
        folded_fingers = 0
        for tip in tips:
            tip_y = landmarks.landmark[tip].y
            pip_y = landmarks.landmark[tip - 2].y  # PIP joint
            if tip_y > pip_y:
                folded_fingers += 1

        return folded_fingers >= 3

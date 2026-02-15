import pyautogui
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class GestureRecognition:
    def __init__(self):
        base_options = python.BaseOptions(
            model_asset_path="models/hand_landmarker.task"
        )

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1
        )

        self.detector = vision.HandLandmarker.create_from_options(options)
        self.prev_x, self.prev_y = 0, 0

    def detect_gestures(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = self.detector.detect(mp_image)

        if result.hand_landmarks:
            for hand_landmarks in result.hand_landmarks:
                self.map_gestures(hand_landmarks)

        return frame

    def map_gestures(self, landmarks):
        screen_w, screen_h = pyautogui.size()

        finger = landmarks[8]  # index finger tip

        x = screen_w - int(finger.x * screen_w)
        y = int(finger.y * screen_h)

        smooth_x = self.prev_x + (x - self.prev_x) * 0.2
        smooth_y = self.prev_y + (y - self.prev_y) * 0.2

        pyautogui.moveTo(smooth_x, smooth_y)

        self.prev_x, self.prev_y = smooth_x, smooth_y

        if self.is_click(landmarks):
            pyautogui.click()

        elif self.is_right_click(landmarks):
            pyautogui.click(button='right')

    def is_click(self, landmarks):
        index_tip = landmarks[8]
        thumb_tip = landmarks[4]

        distance = ((index_tip.x - thumb_tip.x) ** 2 +
                    (index_tip.y - thumb_tip.y) ** 2) ** 0.5

        return distance < 0.05

    def is_right_click(self, landmarks):
        middle_tip = landmarks[12]
        thumb_tip = landmarks[4]

        distance = ((middle_tip.x - thumb_tip.x) ** 2 +
                    (middle_tip.y - thumb_tip.y) ** 2) ** 0.5

        return distance < 0.05

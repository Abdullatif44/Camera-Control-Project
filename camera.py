import cv2

class CameraHandler:
    def __init__(self, width=640, height=480):
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
    def get_frame(self):
        ret, frame = self.capture.read()
        if not ret:
            return None
        return frame
    
    def release(self):
        self.capture.release()

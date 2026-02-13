import face_recognition
import cv2

class FaceAuthentication:
    def __init__(self):
        self.known_face_encodings = [self.load_face_encoding("user.jpg")]
    
    def load_face_encoding(self, image_path):
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            return encodings[0]
        raise ValueError("No face found in the image!")


    def authenticate_user(self):
        video_capture = cv2.VideoCapture(0)
        ret, frame = video_capture.read()

        if not ret:
            video_capture.release()  # RELEASE the camera
            return False

        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        video_capture.release()  # <<<<< ADD THIS

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
            if True in matches:
                return True

        return False


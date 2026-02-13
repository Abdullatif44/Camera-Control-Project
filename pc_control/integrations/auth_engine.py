from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pc_control.core.config import AuthenticationConfig


@dataclass(slots=True)
class AuthResult:
    success: bool
    attempts: int
    reason: str = ""


class FaceAuthenticator:
    def __init__(self, config: AuthenticationConfig) -> None:
        self.config = config
        self._known_face_encoding = None

    def preload(self) -> None:
        import face_recognition

        face_file = Path(self.config.face_image_path)
        if not face_file.exists():
            raise FileNotFoundError(f"Face reference image not found: {face_file}")

        image = face_recognition.load_image_file(str(face_file))
        encodings = face_recognition.face_encodings(image)
        if not encodings:
            raise ValueError("No face found in the reference image.")
        self._known_face_encoding = encodings[0]

    def authenticate(self) -> AuthResult:
        if not self.config.enabled:
            return AuthResult(success=True, attempts=0, reason="Authentication disabled.")

        import cv2
        import face_recognition

        if self._known_face_encoding is None:
            self.preload()

        attempts = 0
        while attempts < self.config.max_attempts:
            attempts += 1
            camera = cv2.VideoCapture(0)
            ok, frame = camera.read()
            camera.release()
            if not ok:
                continue

            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)
            for current in face_encodings:
                matches = face_recognition.compare_faces(
                    [self._known_face_encoding],
                    current,
                    tolerance=self.config.acceptance_tolerance,
                )
                if True in matches:
                    return AuthResult(success=True, attempts=attempts)

        return AuthResult(success=False, attempts=attempts, reason="No matching face.")

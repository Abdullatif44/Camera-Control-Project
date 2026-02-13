import cv2
import mediapipe as mp
import pyautogui
import speech_recognition as sr
import tkinter as tk
from tkinter import messagebox
from camera import CameraHandler
from gestures import GestureRecognition
from voice import VoiceControl
from auth import FaceAuthentication
import threading

class PCControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PC Control Using Camera")
        self.root.geometry("500x300")

        # UI Components
        self.label = tk.Label(self.root, text="PC Control Using Camera", font=("Arial", 20))
        self.label.pack(pady=20)

        self.start_button = tk.Button(self.root, text="Start Control", command=self.start_control)
        self.start_button.pack(pady=10)

        self.quit_button = tk.Button(self.root, text="Quit", command=self.quit_app)
        self.quit_button.pack(pady=10)

        # Camera, Gestures, Voice, and Authentication
        self.camera = CameraHandler()
        self.gesture_recognition = GestureRecognition()
        self.voice_control = VoiceControl()
        self.face_auth = FaceAuthentication()

    def start_control(self):
        def run_after_auth():
            authenticated = self.face_auth.authenticate_user()
            if not authenticated:
                self.root.after(0, lambda: messagebox.showerror("Authentication", "Face not recognized! Access denied."))
                return
            self.root.after(0, self.run_control)

            # Start voice listener in background
            threading.Thread(target=self.voice_control.listen_for_commands, daemon=True).start()

        threading.Thread(target=run_after_auth, daemon=True).start()

    def run_control(self):
        while True:
            frame = self.camera.get_frame()
            if frame is None:
                break

            frame = self.gesture_recognition.detect_gestures(frame)
            cv2.imshow("PC Control Feed", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.camera.release()
        cv2.destroyAllWindows()

    def quit_app(self):
        self.root.quit()


# Initialize the UI
if __name__ == "__main__":
    root = tk.Tk()
    app = PCControlApp(root)
    root.mainloop()

import speech_recognition as sr
import pyautogui
import threading

class VoiceControl:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.active = True

    def listen_for_commands(self):
        def loop():
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                while self.active:
                    try:
                        audio = self.recognizer.listen(source, phrase_time_limit=4)
                        command = self.recognizer.recognize_google(audio).lower()
                        self.execute_command(command)
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError:
                        print("API error")

        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self.active = False

    def execute_command(self, command):
        if "volume up" in command:
            pyautogui.press("volumeup")
        elif "volume down" in command:
            pyautogui.press("volumedown")
        elif "right click" in command:
            pyautogui.click(button='right')
        elif "left click" in command:
            pyautogui.click()

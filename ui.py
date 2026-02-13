import tkinter as tk

class PCControlUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PC Control Settings")
        self.root.geometry("600x400")

        # Title Label
        self.label = tk.Label(self.root, text="Control Your PC with Camera", font=("Arial", 18))
        self.label.pack(pady=20)

        # Buttons to control the application
        self.start_button = tk.Button(self.root, text="Start Control", command=self.start_control)
        self.start_button.pack(pady=10)

        self.quit_button = tk.Button(self.root, text="Quit", command=self.quit_app)
        self.quit_button.pack(pady=10)

        # Adding settings for gesture customization
        self.gesture_label = tk.Label(self.root, text="Customize Gestures", font=("Arial", 14))
        self.gesture_label.pack(pady=10)

        self.gesture_listbox = tk.Listbox(self.root)
        self.gesture_listbox.pack(pady=20)

    def start_control(self):
        print("Starting the control...")

    def quit_app(self):
        self.root.quit()

# Usage example:
if __name__ == "__main__":
    root = tk.Tk()
    app = PCControlUI(root)
    root.mainloop()

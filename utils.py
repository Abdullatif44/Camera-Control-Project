import pyautogui

def move_mouse_to_coordinates(x, y):
    """Maps coordinates to the screen resolution and moves the mouse."""
    screen_width, screen_height = pyautogui.size()
    x = int(x * screen_width)
    y = int(y * screen_height)
    pyautogui.moveTo(x, y)

def log_action(action):
    """Log actions to a file for debugging."""
    with open("actions.log", "a") as log_file:
        log_file.write(action + "\n")

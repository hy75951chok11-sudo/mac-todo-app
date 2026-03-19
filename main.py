import sys
import threading
from todo_manager import TodoManager
from gui import TodoApp
from pynput import keyboard

# Global references
app = None
is_visible = True

def toggle_window():
    global is_visible
    if is_visible:
        app.withdraw()
        is_visible = False
    else:
        app.deiconify()
        app.attributes("-topmost", True)
        app.lift()
        app.attributes("-topmost", False) # Release topmost so it behaves normally after coming to front
        app.focus_force()
        is_visible = True

def on_activate_h():
    # This runs in a background thread of pynput.
    # Schedule UI toggling on the main tkinter thread safely.
    if app:
        app.after(0, toggle_window)

def setup_hotkey():
    # Define the hotkey combination. <cmd> is Command, <alt> is Option on Mac.
    hotkey = keyboard.GlobalHotKeys({
        '<cmd>+<alt>+t': on_activate_h
    })
    hotkey.start()
    return hotkey

def main():
    global app
    manager = TodoManager()
    app = TodoApp(manager)
    
    # Intercept the OS close button (red X) to just hide the window instead of quitting
    def on_closing():
        global is_visible
        app.withdraw()
        is_visible = False
        
    app.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start listening for the global hotkey
    hotkey_listener = setup_hotkey()
    
    # Start the main UI loop
    try:
        app.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        # Ensure the listener stops when the app fully exits
        hotkey_listener.stop()

if __name__ == "__main__":
    main()

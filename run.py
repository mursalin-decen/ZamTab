import sys
if sys.platform == "win32":                     # crisp text on Windows high-DPI screens
    try:
        import ctypes; ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
from zamtab.ui import App

if __name__ == "__main__":
    App().mainloop()

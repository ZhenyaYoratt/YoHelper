import tkinter as tk
from tkinter import ttk
import ctypes

class SystemDraggableSplash:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='white')
        
        self.is_window_active = True

        try:
            self.splash_image = tk.PhotoImage(file="splash.png")
            img_width = self.splash_image.width()
            img_height = self.splash_image.height()
        except Exception as e:
            self.root.destroy()
            return

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - img_width) // 2
        y = (screen_height - (img_height)) // 2
        self.root.geometry(f"{img_width}x{img_height}+{x}+{y}")

        self.label = tk.Label(self.root, image=self.splash_image, bd=0, highlightthickness=0)
        self.label.place(x=0, y=0)

        self.progress = ttk.Progressbar(self.root, length=img_width - 30, mode='indeterminate', style='red.Horizontal.TProgressbar')
        self.progress.place(x=15, y=img_height - 60, height=10)
        self.progress.start(10)

        self.setup_system_drag()

        self.root.protocol("WM_DELETE_WINDOW", self.close_splash)
        self.close_after_id = self.root.after(3000, self.close_splash) # for example 3 seconds.

    def setup_system_drag(self):
        self.root.bind("<Button-1>", self.start_system_move)

    def start_system_move(self, event):
        if not self.is_window_active:
            return
            
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            ctypes.windll.user32.ReleaseCapture()
            ctypes.windll.user32.SendMessageW(hwnd, 0x0112, 0xF012, 0)
        except:
            pass

    def close_splash(self):
        if not self.is_window_active:
            return
            
        self.is_window_active = False
        self.root.after_cancel(self.close_after_id)
        self.root.quit()

    def run(self):
        try:
            self.root.mainloop()
        except:
            pass

if __name__ == "__main__":
    app = SystemDraggableSplash()
    app.run()

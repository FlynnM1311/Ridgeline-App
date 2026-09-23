#M
import ctypes
 
from gui.main_window import MainWindow
 
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # DPI_AWARENESS_SYSTEM_AWARE
except Exception:
    pass

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
 
#from gui.main_window import MainWindow
#def run_app() -> None:
    #from tkwebview2.tkwebview2 import have_runtime, install_runtime
 
    #if not have_runtime():
        #install_runtime()

    #app = MainWindow()
    #app.mainloop()
 
 
#if __name__ == "__main__":
    #thread = Thread(ThreadStart(run_app))
    #thread.ApartmentState = ApartmentState.STA
    #thread.Start()
    #thread.Join()
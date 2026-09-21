#M
import clr
 
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Threading")
 
from System.Threading import ApartmentState, Thread, ThreadStart
 
from gui.main_window import MainWindow
def run_app() -> None:
    from tkwebview2.tkwebview2 import have_runtime, install_runtime
 
    if not have_runtime():
        install_runtime()

            app = MainWindow()
    app.mainloop()
 
 
if __name__ == "__main__":
    thread = Thread(ThreadStart(run_app))
    thread.ApartmentState = ApartmentState.STA
    thread.Start()
    thread.Join()
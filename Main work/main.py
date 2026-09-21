#M
import clr
 
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Threading")
 
from System.Threading import ApartmentState, Thread, ThreadStart
 
from gui.main_window import MainWindow
def run_app() -> None:
    from tkwebview2.tkwebview2 import have_runtime, install_runtime
 
    if not have_runtime():
        # Pops up Microsoft's installer; on modern Windows 10/11 this
        # runtime is usually already present since Edge ships with it.
        install_runtime()
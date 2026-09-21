#M
import clr
 
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Threading")
 
from System.Threading import ApartmentState, Thread, ThreadStart
 
from gui.main_window import MainWindow
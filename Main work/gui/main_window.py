import tkinter as tk
import webbrowser
from tkinter import ttk
#Created main window
class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ridgeline")
        self.geometry("360x220")
        self.resizable(False, False)

        init_db()
        self._build_ui()

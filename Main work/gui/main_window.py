import tkinter as tk
from tkinter import ttk
 
from tkwebview2.tkwebview2 import WebView2
 
from data.storage import get_all_listings, init_db
from gui.add_listing_form import AddListingForm
from mapping.map_builder import build_map
#Created main window

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ridgeline")
        self.geometry("1100x700")
        self.minsize(700, 500)
 
        init_db()
        self._build_ui()
        self._refresh_map()
 
    def _build_ui(self) -> None:
        sidebar = ttk.Frame(self, padding=16, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)  # keep sidebar width fixed regardless of content
 
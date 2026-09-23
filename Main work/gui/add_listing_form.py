import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable
 
from data.storage import Listing, add_listing

class AddListingForm(tk.Toplevel):
    def __init__(self, parent: tk.Tk, on_saved: Callable[[], None]):
        super().__init__(parent)
        self.title("Add land listing")
        self.on_saved = on_saved
        self.resizable(False, False)
 
        self.fields: dict[str, tk.Entry] = {}
        self._build_form()

        
    def _build_form(self) -> None:
        labels = [
            ("address", "Address"),
            ("email", "Contact email"),
            ("latitude", "Latitude"),
            ("longitude", "Longitude"),
            ("acreage", "Acreage (optional)"),
        ]
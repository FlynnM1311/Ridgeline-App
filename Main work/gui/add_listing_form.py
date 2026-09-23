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

                for row, (key, label) in enumerate(labels):
            ttk.Label(self, text=label).grid(
                row=row, column=0, sticky="w", padx=10, pady=6
            )
            entry = ttk.Entry(self, width=35)
            entry.grid(row=row, column=1, padx=10, pady=6)
            self.fields[key] = entry
 
        ttk.Label(self, text="Description").grid(
            row=len(labels), column=0, sticky="nw", padx=10, pady=6
        )
        self.description_text = tk.Text(self, width=27, height=4)
        self.description_text.grid(
            row=len(labels), column=1, padx=10, pady=6
        )
 
        button_row = len(labels) + 1
        ttk.Button(self, text="Save listing", command=self._save).grid(
            row=button_row, column=0, columnspan=2, pady=12
        )
 
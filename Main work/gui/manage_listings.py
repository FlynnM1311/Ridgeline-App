import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable
 
from data.storage import Listing, delete_listing, get_all_listings


class ManageListingsWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk, on_changed: Callable[[], None]):
        super().__init__(parent)
        self.title("Manage listings")
        self.geometry("420x360")
        self.on_changed = on_changed
 
        self._listings: list[Listing] = []
        self._build_ui()
        self._reload_listbox()

    def _build_ui(self) -> None:
        ttk.Label(
            self, text="Select a listing to delete it", padding=(10, 10, 10, 0)
        ).pack(anchor="w")

        list_frame = ttk.Frame(self, padding=10)
        list_frame.pack(fill="both", expand=True)
 
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.listbox = tk.Listbox(
            list_frame, yscrollcommand=scrollbar.set, activestyle="none"
        )
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
 
        ttk.Button(
            self, text="Delete selected", command=self._delete_selected
        ).pack(pady=10)
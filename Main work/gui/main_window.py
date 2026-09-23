import tkinter as tk
from tkinter import ttk
 
from tkwebview import TkWebview
 
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

        self.bind_all("<Button-1>", lambda e: e.widget.focus_force())
 
        init_db()
        self._build_ui()
        self._refresh_map()
 
    def _build_ui(self) -> None:
        sidebar = ttk.Frame(self, padding=16, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)  # keep sidebar width fixed
 
        ttk.Label(
            sidebar, text="Ridgeline", font=("Helvetica", 18, "bold")
        ).pack(pady=(0, 4), anchor="w")
        ttk.Label(
            sidebar,
            text="Connect farmers and hunters\nthrough land listings",
            justify="left",
        ).pack(pady=(0, 20), anchor="w")

        ttk.Button(
            sidebar, text="Add land listing", command=self._open_add_form
        ).pack(fill="x", pady=4)
        ttk.Button(
            sidebar, text="Refresh map", command=self._refresh_map
        ).pack(fill="x", pady=4)

        # The embedded map fills the rest of the window.
        self.map_view = TkWebview(master=self)
        self.map_view.pack(side="right", fill="both", expand=True)

    def _open_add_form(self) -> None:
        AddListingForm(self, on_saved=self._refresh_map)
 
    def _refresh_map(self) -> None:
        """Rebuild the map from current listings and reload it in place."""
        listings = get_all_listings()
        map_path = build_map(listings)
        self.map_view.navigate(map_path.resolve().as_uri())
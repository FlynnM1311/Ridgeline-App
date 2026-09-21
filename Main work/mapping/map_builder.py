import html
import json
import os
import re
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

from pathlib import Path
 
import folium
 
from data.storage import Listing
 
DEFAULT_OUTPUT = Path(__file__).parent.parent / "assets" / "map.html"
DEFAULT_CENTER = (39.8283, -98.5795)  # roughly the center of the US
DEFAULT_ZOOM = 5
 
 
def _popup_html(listing: Listing) -> str:
    """Build the popup HTML for a single listing, including a mailto link.
 
    
    subject = "Interested in hunting your land"
    acreage_line = f"<p>{listing.acreage} acres</p>" if listing.acreage else ""
    description_line = f"<p>{listing.description}</p>" if listing.description else ""
 
    return f"""
    <div style="font-family: sans-serif; min-width: 200px;">
        <b>{listing.address}</b>
        {acreage_line}
        {description_line}
        <p>
            <a href="mailto:{listing.email}?subject={subject}">
                Contact landowner
            </a>
        </p>
    </div>
    """
 def build_map(
    listings: list[Listing],
    output_path: Path = DEFAULT_OUTPUT,
) -> Path:
    """Generate the folium map HTML file from the given listings.
 
    Returns the path to the generated file so the caller can open it
    (e.g. via webbrowser.open) or load it into an embedded webview.
    """
    if listings:
        center = (listings[0].latitude, listings[0].longitude)
    else:
        center = DEFAULT_CENTER
 
    fmap = folium.Map(location=center, zoom_start=DEFAULT_ZOOM, tiles="Esri.WorldStreetMap")
 
     for listing in listings:
        folium.Marker(
            location=(listing.latitude, listing.longitude),
            popup=folium.Popup(_popup_html(listing), max_width=300),
            tooltip=listing.address,
            icon=folium.Icon(color="green", icon="tree", prefix="fa"),
        ).add_to(fmap)
 
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(str(output_path))
    return output_path
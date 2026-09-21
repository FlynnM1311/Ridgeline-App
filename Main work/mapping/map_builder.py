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
 
 
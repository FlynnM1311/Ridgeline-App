"""
Marker Map App (pure Tkinter Canvas edition -- no browser engine, no
third-party dependencies)
--------------------------------------------------------------------------
This version draws the map itself on a plain tkinter.Canvas using real
OpenStreetMap tile images. There is NO Folium, NO Leaflet/JavaScript, NO
WebView2, and NO Pillow -- everything is standard library:
 
    tkinter    - UI + canvas + PNG decoding (tkinter.PhotoImage supports
                 PNG natively since Tk 8.6, so no Pillow is needed)
    urllib     - downloading map tiles over HTTP
    threading  - downloading tiles in the background so the UI never
                 freezes
    math/json/os/re - projection math + marker persistence
 
Requirements:
    Nothing beyond Python itself (3.8+, with a Tk 8.6+ install, which is
    what ships with the standard python.org installers).
 
Internet connection is required to download map tiles the first time you
view an area; tiles are cached to a local "tile_cache" folder next to this
script so re-visiting the same area is instant and works offline
afterwards.
 
Controls:
    - Add Marker: fill Name / Email / Lat / Lon, click "Add Marker".
    - Click a marker on the map: shows a popup with its name + email.
    - Click empty map: records that point's lat/lon (shown in the status
      bar) -- click "Use Last Clicked" to copy it into the Lat/Lon fields.
    - "Center Map Here": recenters the view on whatever's in the Lat/Lon
      fields, without adding a marker.
    - Zoom +/-, arrow pan buttons, and mouse wheel all navigate the map.
    - "Fit All Markers" zooms/centers to show every marker at once.
 
Data is saved to markers.json next to this script, so markers persist
between runs.
--------------------------------------------------------------------------
"""
 
import json
import math
import os
import re
import threading
import tkinter as tk
import urllib.request
from tkinter import ttk, messagebox
 
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "markers.json")
TILE_CACHE_DIR = os.path.join(APP_DIR, "tile_cache")
os.makedirs(TILE_CACHE_DIR, exist_ok=True)
 
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
 
TILE_SIZE = 256
MIN_ZOOM = 1
MAX_ZOOM = 18
TILE_URL_TEMPLATE = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
# OpenStreetMap's tile usage policy asks for a descriptive User-Agent and
# reasonable request volume -- we identify ourselves and cache to disk.
HTTP_HEADERS = {"User-Agent": "TkinterCanvasMarkerMapApp/1.0 (demo app)"}
 
 
# ---------------------------------------------------------------------
# Web Mercator projection helpers (the same math behind every OSM/Google
# Maps-style "slippy map").
# ---------------------------------------------------------------------
 
def lonlat_to_global_pixel(lon, lat, zoom):
    """Convert (lon, lat) to continuous pixel coordinates on the full
    world map image at the given zoom level."""
    lat = max(min(lat, 85.05112878), -85.05112878)  # Mercator's valid range
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = (lon + 180.0) / 360.0 * n * TILE_SIZE
    y = (
        (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi)
        / 2.0
        * n
        * TILE_SIZE
    )
    return x, y
 
 
def global_pixel_to_lonlat(x, y, zoom):
    """Inverse of lonlat_to_global_pixel."""
    n = 2.0 ** zoom
    lon = x / (n * TILE_SIZE) * 360.0 - 180.0
    y_frac = y / (n * TILE_SIZE)
    lat_rad = math.atan(math.sinh(math.pi * (1.0 - 2.0 * y_frac)))
    lat = math.degrees(lat_rad)
    return lon, lat
 
 
def fetch_tile_bytes(zoom, x, y):
    """Download (or read from cache) a single PNG tile. Returns raw bytes
    or None on failure."""
    n = 2 ** zoom
    if y < 0 or y >= n:
        return None
    x = x % n  # the world wraps horizontally
 
    cache_path = os.path.join(TILE_CACHE_DIR, f"{zoom}_{x}_{y}.png")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                return f.read()
        except OSError:
            pass
 
    url = TILE_URL_TEMPLATE.format(z=zoom, x=x, y=y)
    try:
        req = urllib.request.Request(url, headers=HTTP_HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
        try:
            with open(cache_path, "wb") as f:
                f.write(data)
        except OSError:
            pass
        return data
    except Exception:
        return None
 
 
class MarkerMapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Marker Map App (Canvas, no dependencies)")
        self.root.geometry("1020x640")
        self.root.minsize(760, 480)
 
        self.markers = self.load_markers()
 
        # View state
        if self.markers:
            self.center_lat = sum(m["lat"] for m in self.markers) / len(self.markers)
            self.center_lon = sum(m["lon"] for m in self.markers) / len(self.markers)
        else:
            self.center_lat, self.center_lon = 20.0, 0.0
        self.zoom = 3
 
        self.last_clicked_lat = None
        self.last_clicked_lon = None
 
        self._tile_images = []          # keep PhotoImage refs alive
        self._marker_items = {}         # canvas item id -> marker index
        self._view_left = 0.0
        self._view_top = 0.0
        self._view_zoom = self.zoom
        self._redraw_counter = 0
 
        self._build_ui()
        self._refresh_listbox()
 
        self.canvas.bind("<Configure>", lambda e: self.redraw())
 
    # ---------- Data ----------
 
    def load_markers(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                messagebox.showwarning(
                    "Warning", "Could not read markers.json, starting fresh."
                )
        return []
 
    def save_markers(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.markers, f, indent=2)
 
    # ---------- UI ----------
 
    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}
 
        controls = ttk.Frame(self.root)
        controls.pack(side="left", fill="y", padx=(10, 5), pady=10)
 
        form = ttk.LabelFrame(controls, text="Add / Locate Marker")
        form.pack(fill="x")
 
        ttk.Label(form, text="Name:").grid(row=0, column=0, sticky="e", **pad)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=22).grid(
            row=0, column=1, columnspan=3, sticky="ew", **pad
        )
 
        ttk.Label(form, text="Email:").grid(row=1, column=0, sticky="e", **pad)
        self.email_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.email_var, width=22).grid(
            row=1, column=1, columnspan=3, sticky="ew", **pad
        )
 
        ttk.Label(form, text="Lat:").grid(row=2, column=0, sticky="e", **pad)
        self.lat_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.lat_var, width=10).grid(
            row=2, column=1, sticky="ew", **pad
        )
 
        ttk.Label(form, text="Lon:").grid(row=2, column=2, sticky="e", **pad)
        self.lon_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.lon_var, width=10).grid(
            row=2, column=3, sticky="ew", **pad
        )
 
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)
 
        ttk.Button(form, text="Add Marker", command=self.add_marker).grid(
            row=3, column=0, columnspan=4, sticky="ew", padx=8, pady=(4, 2)
        )
        btn_row = ttk.Frame(form)
        btn_row.grid(row=4, column=0, columnspan=4, sticky="ew", padx=8, pady=(0, 8))
        ttk.Button(btn_row, text="Center Map Here", command=self.center_here).pack(
            side="left", expand=True, fill="x", padx=(0, 4)
        )
        ttk.Button(
            btn_row, text="Use Last Clicked", command=self.use_last_clicked
        ).pack(side="left", expand=True, fill="x")
 
        # Marker list
        list_frame = ttk.LabelFrame(controls, text="Markers")
        list_frame.pack(fill="both", expand=True, pady=(10, 0))
 
        list_inner = ttk.Frame(list_frame)
        list_inner.pack(fill="both", expand=True, padx=8, pady=8)
 
        scrollbar = ttk.Scrollbar(list_inner, orient="vertical")
        self.listbox = tk.Listbox(
            list_inner, yscrollcommand=scrollbar.set, activestyle="dotbox", width=30
        )
        scrollbar.config(command=self.listbox.yview)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
 
        self.detail_var = tk.StringVar(value="Select a marker to see its email.")
        ttk.Label(
            list_frame,
            textvariable=self.detail_var,
            wraplength=250,
            foreground="#333",
            justify="left",
        ).pack(fill="x", padx=8, pady=(0, 4))
 
        list_btn_row = ttk.Frame(list_frame)
        list_btn_row.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(
            list_btn_row, text="Delete Selected", command=self.delete_marker
        ).pack(side="left")
 
        # Map navigation controls
        nav_frame = ttk.LabelFrame(controls, text="Map Navigation")
        nav_frame.pack(fill="x", pady=(10, 0))
 
        zoom_row = ttk.Frame(nav_frame)
        zoom_row.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Button(zoom_row, text="Zoom -", command=self.zoom_out).pack(
            side="left", expand=True, fill="x", padx=(0, 4)
        )
        ttk.Button(zoom_row, text="Zoom +", command=self.zoom_in).pack(
            side="left", expand=True, fill="x"
        )
 
        pad_grid = ttk.Frame(nav_frame)
        pad_grid.pack(padx=8, pady=(0, 8))
        ttk.Button(pad_grid, text="\u2191", width=3, command=lambda: self.pan(0, -0.5)).grid(
            row=0, column=1
        )
        ttk.Button(pad_grid, text="\u2190", width=3, command=lambda: self.pan(-0.5, 0)).grid(
            row=1, column=0
        )
        ttk.Button(pad_grid, text="\u2192", width=3, command=lambda: self.pan(0.5, 0)).grid(
            row=1, column=2
        )
        ttk.Button(pad_grid, text="\u2193", width=3, command=lambda: self.pan(0, 0.5)).grid(
            row=2, column=1
        )
 
        ttk.Button(
            nav_frame, text="Fit All Markers", command=self.fit_to_markers
        ).pack(fill="x", padx=8, pady=(0, 8))
 
        self.status_var = tk.StringVar(value="")
        ttk.Label(
            controls,
            textvariable=self.status_var,
            wraplength=260,
            foreground="#666",
            justify="left",
        ).pack(fill="x", pady=(10, 0))
 
        # Map canvas
        map_panel = ttk.Frame(self.root)
        map_panel.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)
        self.canvas = tk.Canvas(map_panel, bg="#d9e6f2", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
 
        self.canvas.tag_bind("marker", "<Button-1>", self._on_marker_click)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        # Mouse wheel: Windows/Mac send <MouseWheel>, Linux sends Button-4/5
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
 
    # ---------- Marker actions ----------
 
    def add_marker(self):
        name = self.name_var.get().strip()
        email = self.email_var.get().strip()
        lat_raw = self.lat_var.get().strip()
        lon_raw = self.lon_var.get().strip()
 
        if not name:
            messagebox.showerror("Missing info", "Please enter a marker name.")
            return
        if not EMAIL_RE.match(email):
            messagebox.showerror("Invalid email", "Please enter a valid email address.")
            return
        try:
            lat = float(lat_raw)
            lon = float(lon_raw)
        except ValueError:
            messagebox.showerror(
                "Invalid coordinates", "Latitude and longitude must be numbers."
            )
            return
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            messagebox.showerror(
                "Invalid coordinates",
                "Latitude must be between -90 and 90, longitude between -180 and 180.",
            )
            return
 
        self.markers.append({"name": name, "email": email, "lat": lat, "lon": lon})
        self.save_markers()
        self._refresh_listbox()
 
        self.name_var.set("")
        self.email_var.set("")
        self.lat_var.set("")
        self.lon_var.set("")
 
        self._draw_markers(self._view_left, self._view_top, self._view_zoom)
 
    def delete_marker(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("No selection", "Select a marker to delete first.")
            return
        index = sel[0]
        marker = self.markers[index]
        if messagebox.askyesno("Confirm delete", f"Delete marker '{marker['name']}'?"):
            del self.markers[index]
            self.save_markers()
            self._refresh_listbox()
            self.detail_var.set("Select a marker to see its email.")
            self._draw_markers(self._view_left, self._view_top, self._view_zoom)
 
    def _refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for m in self.markers:
            self.listbox.insert(tk.END, f"{m['name']}  \u2014  {m['email']}")
 
    def _on_select(self, _event):
        sel = self.listbox.curselection()
        if not sel:
            return
        m = self.markers[sel[0]]
        self.detail_var.set(
            f"Name: {m['name']}\nEmail: {m['email']}\nLat/Lon: {m['lat']}, {m['lon']}"
        )
 
    # ---------- Map navigation ----------
 
    def center_here(self):
        try:
            lat = float(self.lat_var.get())
            lon = float(self.lon_var.get())
        except ValueError:
            messagebox.showerror(
                "Invalid coordinates", "Enter numeric Lat/Lon values first."
            )
            return
        self.center_lat, self.center_lon = lat, lon
        self.redraw()
 
    def use_last_clicked(self):
        if self.last_clicked_lat is None:
            messagebox.showinfo("No click yet", "Click on the map first.")
            return
        self.lat_var.set(f"{self.last_clicked_lat:.6f}")
        self.lon_var.set(f"{self.last_clicked_lon:.6f}")
 
    def zoom_in(self):
        self._set_zoom(self.zoom + 1)
 
    def zoom_out(self):
        self._set_zoom(self.zoom - 1)
 
    def _set_zoom(self, z):
        z = max(MIN_ZOOM, min(MAX_ZOOM, z))
        if z == self.zoom:
            return
        self.zoom = z
        self.redraw()
 
    def pan(self, dx_frac, dy_frac):
        w = self.canvas.winfo_width() or 700
        h = self.canvas.winfo_height() or 600
        cx, cy = lonlat_to_global_pixel(self.center_lon, self.center_lat, self.zoom)
        cx += dx_frac * w
        cy += dy_frac * h
        self.center_lon, self.center_lat = global_pixel_to_lonlat(cx, cy, self.zoom)
        self.redraw()
 
    def fit_to_markers(self):
        if not self.markers:
            messagebox.showinfo("No markers", "Add at least one marker first.")
            return
        lats = [m["lat"] for m in self.markers]
        lons = [m["lon"] for m in self.markers]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
 
        self.center_lat = (min_lat + max_lat) / 2
        self.center_lon = (min_lon + max_lon) / 2
 
        if len(self.markers) == 1:
            self.zoom = 10
            self.redraw()
            return
 
        w = self.canvas.winfo_width() or 700
        h = self.canvas.winfo_height() or 600
        best_zoom = MIN_ZOOM
        for z in range(MAX_ZOOM, MIN_ZOOM - 1, -1):
            x1, y1 = lonlat_to_global_pixel(min_lon, max_lat, z)
            x2, y2 = lonlat_to_global_pixel(max_lon, min_lat, z)
            if abs(x2 - x1) <= w * 0.85 and abs(y2 - y1) <= h * 0.85:
                best_zoom = z
                break
        self.zoom = best_zoom
        self.redraw()
 
    def _on_mousewheel(self, event):
        delta = 0
        if getattr(event, "num", None) == 4:
            delta = 1
        elif getattr(event, "num", None) == 5:
            delta = -1
        elif getattr(event, "delta", 0) > 0:
            delta = 1
        elif getattr(event, "delta", 0) < 0:
            delta = -1
        if delta == 0:
            return
        self._zoom_at(event.x, event.y, delta)
 
    def _zoom_at(self, canvas_x, canvas_y, delta):
        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.zoom + delta))
        if new_zoom == self.zoom:
            return
        w = self.canvas.winfo_width() or 700
        h = self.canvas.winfo_height() or 600
        cx, cy = lonlat_to_global_pixel(self.center_lon, self.center_lat, self.zoom)
        left = cx - w / 2
        top = cy - h / 2
        global_x = left + canvas_x
        global_y = top + canvas_y
        lon, lat = global_pixel_to_lonlat(global_x, global_y, self.zoom)
 
        self.zoom = new_zoom
        gx, gy = lonlat_to_global_pixel(lon, lat, self.zoom)
        new_center_x = gx - (canvas_x - w / 2)
        new_center_y = gy - (canvas_y - h / 2)
        self.center_lon, self.center_lat = global_pixel_to_lonlat(
            new_center_x, new_center_y, self.zoom
        )
        self.redraw()
 
    # ---------- Click handling ----------
 
    def _on_marker_click(self, _event):
        current = self.canvas.find_withtag("current")
        if not current:
            return
        idx = self._marker_items.get(current[0])
        if idx is None:
            return
        self._show_popup(idx)
        return "break"
 
    def _on_canvas_click(self, event):
        current = self.canvas.find_withtag("current")
        if current and current[0] in self._marker_items:
            return  # the marker's own binding handles this click
 
        global_x = self._view_left + event.x
        global_y = self._view_top + event.y
        lon, lat = global_pixel_to_lonlat(global_x, global_y, self._view_zoom)
        self.last_clicked_lat = lat
        self.last_clicked_lon = lon
        self.status_var.set(
            f"Last click: {lat:.5f}, {lon:.5f}\n"
            "Click 'Use Last Clicked' to fill the fields above."
        )
        self.canvas.delete("popup")
 
    def _show_popup(self, idx):
        self.canvas.delete("popup")
        m = self.markers[idx]
        gx, gy = lonlat_to_global_pixel(m["lon"], m["lat"], self._view_zoom)
        x = gx - self._view_left
        y = gy - self._view_top
 
        text_item = self.canvas.create_text(
            x,
            y - 34,
            text=f"{m['name']}\n{m['email']}",
            fill="black",
            font=("TkDefaultFont", 9),
            justify="center",
            tags=("popup",),
        )
        bbox = self.canvas.bbox(text_item)
        padding = 6
        rect_item = self.canvas.create_rectangle(
            bbox[0] - padding,
            bbox[1] - padding,
            bbox[2] + padding,
            bbox[3] + padding,
            fill="#fff9c4",
            outline="#999999",
            tags=("popup",),
        )
        self.canvas.tag_raise(text_item, rect_item)
 
        self.detail_var.set(
            f"Name: {m['name']}\nEmail: {m['email']}\nLat/Lon: {m['lat']}, {m['lon']}"
        )
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx)
        self.listbox.see(idx)
 
    # ---------- Rendering ----------
 
    def redraw(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return  # widget not laid out yet
 
        zoom = self.zoom
        cx, cy = lonlat_to_global_pixel(self.center_lon, self.center_lat, zoom)
        left = cx - w / 2
        top = cy - h / 2
 
        tile_x_min = int(left // TILE_SIZE)
        tile_x_max = int((left + w) // TILE_SIZE)
        tile_y_min = int(top // TILE_SIZE)
        tile_y_max = int((top + h) // TILE_SIZE)
 
        self._redraw_counter += 1
        request_id = self._redraw_counter
        self.status_var.set(f"Loading map tiles\u2026 (zoom {zoom})")
 
        def worker():
            tiles = []
            for tx in range(tile_x_min, tile_x_max + 1):
                for ty in range(tile_y_min, tile_y_max + 1):
                    data = fetch_tile_bytes(zoom, tx, ty)
                    if data:
                        tiles.append((tx, ty, data))
            self.root.after(0, self._apply_tiles, request_id, zoom, left, top, tiles)
 
        threading.Thread(target=worker, daemon=True).start()
 
    def _apply_tiles(self, request_id, zoom, left, top, tiles):
        if request_id != self._redraw_counter:
            return  # a newer redraw has since been requested; discard this one
 
        self._view_left, self._view_top, self._view_zoom = left, top, zoom
 
        self.canvas.delete("tile")
        self._tile_images = []
        for tx, ty, data in tiles:
            try:
                photo = tk.PhotoImage(data=data)
            except Exception:
                continue
            self._tile_images.append(photo)
            img_x = tx * TILE_SIZE - left
            img_y = ty * TILE_SIZE - top
            self.canvas.create_image(img_x, img_y, anchor="nw", image=photo, tags=("tile",))
 
        self.canvas.tag_lower("tile")
        self._draw_markers(left, top, zoom)
        self.status_var.set(
            f"Center: {self.center_lat:.4f}, {self.center_lon:.4f}   Zoom: {zoom}"
        )
 
    def _draw_markers(self, left, top, zoom):
        self.canvas.delete("marker")
        self.canvas.delete("popup")
        self._marker_items = {}
        for idx, m in enumerate(self.markers):
            gx, gy = lonlat_to_global_pixel(m["lon"], m["lat"], zoom)
            x = gx - left
            y = gy - top
            r = 7
            dot = self.canvas.create_oval(
                x - r, y - r, x + r, y + r,
                fill="#d9534f", outline="#7a2e2a", width=1.5, tags=("marker",),
            )
            label = self.canvas.create_text(
                x, y - r - 8, text=m["name"],
                fill="#222222", font=("TkDefaultFont", 9, "bold"), tags=("marker",),
            )
            self._marker_items[dot] = idx
            self._marker_items[label] = idx
 
 
def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except tk.TclError:
        pass
    app = MarkerMapApp(root)
    root.after(100, app.redraw)  # initial draw once the canvas has a real size
    root.mainloop()
 
 
if __name__ == "__main__":
    main()
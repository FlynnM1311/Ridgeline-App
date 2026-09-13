import tkinter
import folium

root = Tk(
    
)
# title
root.title("Ridgeline App")
# app dimentions
root.geometry("800x600")
#creating map
m = folium.Map(location=[45.5236, -122.6750], zoom_start=12)
m.save("map.html")

root.mainloop()

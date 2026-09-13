import folium
# Create a simple map
m = folium.Map(location=[-45.87, 170.5], zoom_start=12)
m.save("my_map.html")
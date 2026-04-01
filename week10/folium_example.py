import folium
# https://python-visualization.github.io/folium/latest/
# Define the starting coordinates (e.g., the center of Boston, MA)
# The default basemap is OpenStreetMap
m = folium.Map(location=[42.3601, -71.0589], zoom_start=12)

# Save the map as an HTML file
m.save("boston_map.html")

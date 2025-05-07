import folium
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from folium.plugins import MeasureControl

# Load full Kenya counties file (GeoJSON or SHP)
counties = gpd.read_file("gadm41_KEN_1.json")  # or .shp

# Filter for Turkana only
turkana = counties[counties['NAME_1'] == 'Turkana']
turkana.to_file("turkana_boundary.geojson", driver="GeoJSON")

Map = folium.Map(location = [3.2, 35.6], zoom_start= 7.2)

bordersStyle= {
    'color': 'black',
    'weight': 2,
    'fillColor': '#A67B5B',
    'fillOpacity': 0.6
}
folium.GeoJson("turkana_boundary.geojson", 
               name= "Turkana",
               style_function= lambda x:bordersStyle).add_to(Map)
folium.LayerControl().add_to(Map)

# Load real water data
df = pd.read_csv("Turkana_dry.csv")

# Drop rows with missing coordinates or key water quality data
df = df.dropna(subset=['Coord_Lat', 'Coord_Long', 'F', 'pH'])


# Define color scale based on Fluoride levels
def fluoride_color(value):
    if value < 1.5:
        return 'green'
    elif 1.5 <= value < 4:
        return 'orange'
    else:
        return 'red'


# Convert DataFrame to GeoDataFrame with geometry from lat/lon
geometry = [Point(xy) for xy in zip(df['Coord_Long'], df['Coord_Lat'])]
points_gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

# Reproject if needed
turkana = turkana.to_crs("EPSG:4326")

# Clip to Turkana boundary
points_in_turkana = gpd.clip(points_gdf, turkana)

# Add each site as a marker
for _, row in points_in_turkana.iterrows():
    folium.CircleMarker(
        location=[row['Coord_Lat'], row['Coord_Long']],
        radius=7,
        popup=folium.Popup(
            f"<b>{row['SampleID']}</b><br>"
            f"Fluoride: {row['F']} mg/L<br>"
            f"pH: {row['pH']}<br>"
            f"EC: {row['EC']} µS/cm",
            max_width=200
        ),
        tooltip=f"Site: {row['SampleID']}",
        color=fluoride_color(row['F']),
        fill=True,
        fill_color=fluoride_color(row['F']),
        fill_opacity=0.7
    ).add_to(Map)


# Add custom legend (Fluoride levels)
legend_html = """
<div style='position: fixed;
     bottom: 50px; left: 50px; width: 240px; height: 180px;
     border:2px solid grey; z-index:9999; font-size:14px;
     background-color:white; padding: 10px;'>
     <b>Fluoride Levels (mg/L)</b><br>
     <i style='background:green; width:10px; height:10px; display:inline-block'></i>&nbsp; Safe (&lt; 1.5)<br>
     <i style='background:orange; width:10px; height:10px; display:inline-block'></i>&nbsp; Risky (1.5 – 4)<br>
     <i style='background:red; width:10px; height:10px; display:inline-block'></i>&nbsp; Unsafe (&gt; 4)<br>
     <br>
     <b>pH Levels</b><br>
     <i style='background:green; width:10px; height:10px; display:inline-block'></i>&nbsp; Safe (6.5 – 8.5)<br>
     <i style='background:red; width:10px; height:10px; display:inline-block'></i>&nbsp; Unsafe (&lt; 6.5 or &gt; 8.5)<br>
</div>
'<a href="Turkana_dry.csv" download style="color:blue;">Download CSV Data</a><br>'
"""
Map.get_root().html.add_child(folium.Element(legend_html))

title_html = """
<div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
     z-index:9999; background-color:white; padding:10px; border:2px solid grey;
     font-size:20px; font-weight:bold;">
     Turkana County Water Quality Map (Fluoride & pH)
</div>
"""
Map.get_root().html.add_child(folium.Element(title_html))

# Add measurement control (scale bar included)
measure_control = MeasureControl(primary_length_unit='kilometers', secondary_length_unit='meters')
Map.add_child(measure_control)

# Save to HTML
Map.save("turkana_water_quality_map.html")

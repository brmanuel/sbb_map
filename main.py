import streamlit as st
import pandas as pd
import random
from streamlit_folium import folium_static
import folium

# using dummy data for each of the 9760 municipalities
municipalities = list(range(1, 9761))
data = pd.DataFrame({
    "id": municipalities,
    "value": [random.randint(1, 8) for _ in municipalities]
})

m = folium.Map(tiles="cartodb positron", location=(46.823673, 8.399077), zoom_start=8)

# ch-municipalities.geojson is lower resolution than municipalities.geojson
folium.Choropleth(
    geo_data="data/ch-municipalities.geojson",
    data=data,
    columns=["id", "value"],
    key_on="feature.id",
).add_to(m)

# streamlit-folium for integrating folium map with streamlit (https://folium.streamlit.app/)
# folium_static seems to work fine for our use-case
# st_folium allows bi-directional communication, but continuously reloaded the choropleth map
# using st.pydeck_chart didn't work at all
folium_static(m, width=900)

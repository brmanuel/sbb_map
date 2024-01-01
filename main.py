import datetime
import streamlit as st
import pandas as pd
import random
from streamlit_folium import folium_static
import folium


# The year of the gtfs data in the database
YEAR=2023

def compute_map(location, date, time):
    """
    Generate the map based on the current selection
    """
    print(location, date, time)
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

    return m


trainstations = list(range(1, 9761))
with st.sidebar.form("Selection", border=False):
    location = st.selectbox(
        label="Location", 
        options=trainstations,
        key="location",
        help="Select a destination. Start typing a trainstation name to narrow down the suggestions."
    )

    date = st.date_input(
        label="Date", 
        value=datetime.date(YEAR, 1, 1),
        key="date",
        min_value=datetime.date(YEAR, 1, 1),
        max_value=datetime.date(YEAR, 12, 31),
        help="Specify the date on which you want to reach your destination."
    )

    time = st.time_input(
        label="Time",
        value=datetime.time(8, 45),
        key="time",
        help="Specify the time before which you want to reach your destination."
    )

    submitted = st.form_submit_button("Submit")


m = compute_map(location, date, time)

# streamlit-folium for integrating folium map with streamlit (https://folium.streamlit.app/)
# folium_static seems to work fine for our use-case
# st_folium allows bi-directional communication, but continuously reloaded the choropleth map
# using st.pydeck_chart didn't work at all
folium_static(m, width=1000, height=700)

st.write("Querying:", location, date, time)





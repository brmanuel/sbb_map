import datetime
import streamlit as st
import pandas as pd
from streamlit_folium import folium_static
import folium
import json

from src.traversal.algorithm import compute_map, get_all_stop_names
from src.choropleth.distance_choropleth import create_choropleth


# The year of the gtfs data in the database
YEAR=2024
GEOJSON = "data/geojson/ch-municipalities.geojson"

def create_choropleth_folium(location : str, date : datetime.date, time : datetime.time, earliest_departure : datetime.time):
    """
    Generate the map based on the current selection
    """

    def parse_time(time : datetime.time):
        if time is None:
            return None
        return time.minute + time.hour * 60
    
    def time_to_iso(time : datetime.time):
        if time is None:
            return "NA"
        return time.isoformat()


    print(location, date, time)

    time_in_seconds = time.hour * 3600 + time.minute * 60
    earliest_departure_in_seconds = earliest_departure.hour * 3600 + earliest_departure.minute * 60
    mapping = compute_map(location, date, time_in_seconds, earliest_departure_in_seconds)

    print("computed map")
    coord_to_departure = {
        (val["lon"], val["lat"]): val["departure"]
        for val in mapping.values()
    }

    with open(GEOJSON, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    choropleth = create_choropleth(coord_to_departure, geojson)
    print(choropleth)
    data = pd.DataFrame({
        "id": choropleth.keys(),
        "value": map(parse_time, choropleth.values())
    })
    print("created choropleth")

    m = folium.Map(tiles="cartodb positron", location=(46.823673, 8.399077), zoom_start=8)

    # ch-municipalities.geojson is lower resolution than municipalities.geojson
    with open(GEOJSON, "r", encoding="utf-8") as f:
        geojson = json.load(f)
        for feature in geojson["features"]:
            feature["properties"]["id"] = feature["id"]
            feature["properties"]["departure"] = time_to_iso(choropleth[feature["id"]])

    choropleth = folium.Choropleth(
        geo_data=geojson,
        data=data,
        columns=["id", "value"],
        key_on="feature.id"
    ).add_to(m)

    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(["departure"])
    )

    return m


trainstations = get_all_stop_names()
st.set_page_config(layout="wide")
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

    earliest_departure = st.time_input(
        label="Earliest Departure",
        value=datetime.time(0, 0),
        key="earliest_departure",
        help="Specify the earliest departure time."
    )
    
    submitted = st.form_submit_button("Submit")


m = create_choropleth_folium(location, date, time, earliest_departure)

# streamlit-folium for integrating folium map with streamlit (https://folium.streamlit.app/)
# folium_static seems to work fine for our use-case
# st_folium allows bi-directional communication, but continuously reloaded the choropleth map
# using st.pydeck_chart didn't work at all
folium_static(m, width=1300, height=700)






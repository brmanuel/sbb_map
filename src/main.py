import datetime
import streamlit as st
import pandas as pd
from streamlit_folium import folium_static, st_folium
import folium
import json

from src.traversal.algorithm import compute_map, get_all_stop_names
from src.choropleth.distance_choropleth import create_choropleth
from src.choropleth.geojson import Geojson

# The year of the gtfs data in the database
YEAR=2024
GEOJSON = "data/geojson/ch-municipalities.geojson"
st.set_page_config(layout="wide")

def parse_time(time : datetime.time):
    if time is None:
        return None
    return time.minute + time.hour * 60

def time_to_iso(time : datetime.time):
    if time is None:
        return "NA"
    return time.isoformat()

@st.cache_data
def get_geojson() -> Geojson:
    with open(GEOJSON, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)
        return Geojson(geojson_data)


@st.cache_data
def compute_choropleth(location : str, date : datetime.date, time : datetime.time, earliest_departure : datetime.time):
    def aggregate_departures(departures, new_departure):
        """Aggregate the departure times of coords in the same polygon."""
        updated_departures = departures
        if departures is None:
            updated_departures = []
        updated_departures.append(new_departure)
        return updated_departures
    
    def get_latest_departure_time(stops):
        if stops is None:
            return None
        departure_times = [
            stop["departure"] for stop in stops 
            if stop["departure"] is not None
        ]
        if len(departure_times) == 0:
            return None
        return max(departure_times)


    time_in_seconds = time.hour * 3600 + time.minute * 60
    earliest_departure_in_seconds = earliest_departure.hour * 3600 + earliest_departure.minute * 60
    mapping = compute_map(location, date, time_in_seconds, earliest_departure_in_seconds)
    coord_to_information = {}
    for id, val in mapping.items():
        key = (val["lon"], val["lat"])
        value = {"id": id, **val}
        if key in coord_to_information:
            # There are multiple stations at the same coordinates, take the one with the latest departure
            other_value = coord_to_information[key]
            if value["departure"] is None or (
                other_value["departure"] is not None 
                and value["departure"] < other_value["departure"]
            ):
                value = other_value
        coord_to_information[key] = value

    geojson = get_geojson().get_geojson()
    choropleth = create_choropleth(coord_to_information, geojson, aggregate=aggregate_departures)

    data = pd.DataFrame({
        "id": choropleth.keys(),
        "values": choropleth.values()
    })
    data["latest_departure_time"] = data["values"].map(get_latest_departure_time)
    data["latest_departure_seconds"] = data["latest_departure_time"].map(parse_time)
    data["latest_departure_string"] = data["latest_departure_time"].map(time_to_iso)
    data.set_index("id", drop=False, inplace=True)
    print(data)

    for feature in geojson["features"]:
        feature["properties"]["id"] = feature["id"]
        feature["properties"]["departure"] = data.loc[feature["id"]]["latest_departure_string"]

    return data, geojson


@st.cache_data
def get_stop_names():
    all_stop_names = get_all_stop_names()
    return sorted(set(all_stop_names))


trainstations = get_stop_names()
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


print(location, date, time)

m = folium.Map(tiles="cartodb positron", location=(46.823673, 8.399077), zoom_start=8)

data, geojson_data = compute_choropleth(location, date, time, earliest_departure)
choropleth = folium.Choropleth(
    geo_data=geojson_data,
    data=data,
    columns=["id", "latest_departure_seconds"],
    key_on="feature.id"
).add_to(m)

choropleth.geojson.add_child(
    folium.features.GeoJsonTooltip(["departure"])
)


col1, col2 = st.columns([0.7, 0.3])
with col1:
    st_data = st_folium(m, width=900, height=600)

with col2:
    geojson = get_geojson()
    last_clicked = st_data["last_clicked"]
    if last_clicked is not None:
        feature_clicked = geojson.get_feature_covering_lat_lon(last_clicked["lat"], last_clicked["lng"])
        id = feature_clicked["id"]
        d = pd.DataFrame(data.loc[id]["values"]).sort_values("departure", ascending=False)
        st.write(d[["name", "departure", "id"]])







import datetime
import streamlit as st
import pandas as pd
from streamlit_folium import folium_static, st_folium
import folium
import json
from itertools import groupby

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
def group_stops_by_feature(coord_to_stops, geojson):
    def aggregate_stops(stops, new_stops):
        """Aggregate the departure times of coords in the same polygon."""
        updated_stops = stops or []
        return updated_stops + new_stops
    
    geojson = get_geojson().get_geojson()
    choropleth = create_choropleth(coord_to_stops, geojson, aggregate=aggregate_stops)
    return choropleth


@st.cache_data
def compute_choropleth(location : str, date : datetime.date, time : datetime.time, earliest_departure : datetime.time):
    
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
    stop_to_journey_information = compute_map(location, date, time_in_seconds, earliest_departure_in_seconds)
    coord_to_stops = {}
    for id,val in stop_to_journey_information.items():
        key = (val["lon"], val["lat"])
        if key not in coord_to_stops:
            coord_to_stops[key] = []
        coord_to_stops[key].append(id)
    
    geojson = get_geojson().get_geojson()
    feature_id_to_stops = group_stops_by_feature(coord_to_stops, geojson)

    data = pd.DataFrame({
        "id": feature_id_to_stops.keys(),
        "values": [
            [{"id": stop_id, **stop_to_journey_information[stop_id]} for stop_id in (stop_ids or [])]
            for stop_ids in feature_id_to_stops.values()
        ]
    })
    data["latest_departure_time"] = data["values"].map(get_latest_departure_time)
    data["latest_departure_seconds"] = data["latest_departure_time"].map(parse_time)
    data["latest_departure_string"] = data["latest_departure_time"].map(time_to_iso)
    data.set_index("id", drop=False, inplace=True)
    print(data)

    for feature in geojson["features"]:
        feature["properties"]["id"] = feature["id"]
        feature["properties"]["departure"] = data.loc[feature["id"]]["latest_departure_string"]

    return data, stop_to_journey_information, geojson




@st.cache_data
def get_stop_names():
    all_stop_names = get_all_stop_names()
    return sorted(set(all_stop_names))


trainstations = get_stop_names()
st.header("Public Transport Map")
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

data, mapping, geojson_data = compute_choropleth(location, date, time, earliest_departure)
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

edited_df = None
with col2:
    geojson = get_geojson()
    last_clicked = st_data["last_clicked"]
    if last_clicked is not None:
        st.subheader("Stations")
        feature_clicked = geojson.get_feature_covering_lat_lon(last_clicked["lat"], last_clicked["lng"])
        if feature_clicked is not None:
            id = feature_clicked["id"]
            d = pd.DataFrame(data.loc[id]["values"]).sort_values("departure", ascending=False)
            d["select_stop"] = False
            edited_df = st.data_editor(
                d[["name", "departure", "select_stop", "id"]], 
                hide_index=True,
                disabled=("departure", "name", "id"),
                column_config={
                    "id": None
                }
            )

    if edited_df is not None:
        first_selected_row = edited_df.loc[edited_df["select_stop"]]
        if len(first_selected_row) > 0:
            st.subheader("Itinerary")
            values = []
            current_stop_id = first_selected_row.iloc[0]["id"]
            while True:
                value = mapping[current_stop_id]
                values.append(value)
                if value["name"] == location:
                    break
                current_stop_id = value["pred"]
            table = []
            groups = [(k, list(v)) for k,v in groupby(values, key=lambda v: v["trip_id"])]
            for (trip_id1, grp1), (trip_id2, grp2) in zip(groups, groups[1:]):
                type = "walk" if trip_id1 == "transfer" else "ride"
                start = list(grp1)[0]
                end = list(grp2)[0]
                table.append({
                    "departure": start["departure"],
                    "from": start["name"],
                    "type": type,
                    "to": end["name"],
                })

            st.dataframe(pd.DataFrame(table), hide_index=True)










import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.main import compute_choropleth, parse_time



if "queries" not in st.session_state:
    st.session_state["queries"] = set()
    

queries = st.session_state["queries"]
query_table = pd.DataFrame(queries, columns=["location", "date", "time", "earliest_departure"])

accumulation_table = None
with st.sidebar.form("Accumulation", border=False):    
    st.header("Create Accumulation")
    query_table = query_table.assign(count = 0)
    accumulation_table = st.data_editor(
        query_table, 
        hide_index=True,
        column_config={
            "location": st.column_config.TextColumn(disabled=True),
            "date": st.column_config.DateColumn(disabled=True),
            "time": st.column_config.TimeColumn(disabled=True),
            "earliest_departure": st.column_config.TimeColumn(disabled=True),
            "count": st.column_config.NumberColumn(
                min_value=0,
                max_value=1000,
                step=1
            )
        })
    submitted = st.form_submit_button("Submit")

if accumulation_table is not None:
    num = accumulation_table["count"].sum()
    if num == 0:
        st.write("No queries selected. Increase the count of queries to show an accumulation map.")
    else:
        accumulated_data = None
        for _, row in accumulation_table.iterrows():
            if row["count"] > 0:
                print(f"Computing: {row['location']}, {row['date']}, {row['time']}, {row['earliest_departure']}")
                data, _, geojson_data = compute_choropleth(
                    row["location"], row["date"], row["time"], row["earliest_departure"]
                )
                if accumulated_data is None:
                    accumulated_data = pd.DataFrame({"id": data["id"], "commute": 0})    
                accumulated_data["commute"] += row["count"] * (parse_time(row["time"]) - data["latest_departure_minutes"])
                
        print(accumulated_data)
        m = folium.Map(tiles="cartodb positron", location=(46.823673, 8.399077), zoom_start=8)
        choropleth = folium.Choropleth(
            geo_data=geojson_data,
            data=accumulated_data,
            columns=["id", "commute"],
            key_on="feature.id"
        ).add_to(m)

        st_data = st_folium(m, width=900, height=600)


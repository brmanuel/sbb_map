

# SBB Map

## Overview

A python streamlit app to visualize the "public-transportation distance" between different locations in switzerland.

Concretely, specifying a destination (a public transportation stop), a date, and a time a [choropleth map](https://datavizcatalogue.com/methods/choropleth.html) of the country is generated where each municipality is colored according to the latest departure time necessary to arrive in time at the specified destination.
Different stops in the same municipality are aggregated by the minimum function.

Granularity of aggregation depends on the "features" in the geojson data. E.g. given a geojson file containing a voronoi diagram of all public transportation stops in the country, there would be no aggregation at all.

The implementation is generic - providing the following data should suffice to "port" the app to other countries
- [GTFS Data](https://developers.google.com/transit/gtfs/reference) about the public transportation of the country
- Geojson file with a partition of the country specifying the granularity of the choropleth map


## Major Components

- A relational database is populated with the GTFS data using the init_db.sql script
- A simple [Streamlit](https://streamlit.io/) app allows the user to specify a destination station, date and time and displays the resulting map using the [Folium](https://python-visualization.github.io/folium/latest/) library.
- A BFS algorithm traverses the "connection graph" of the public transportation network



## How to run

Needs to be cleaned-up. Documentation will follow.

### Get the necessary data

### Generate the database

### Install the dependencies

### Run the application


## TODOs

- Add [tooltip](https://stackoverflow.com/questions/70471888/text-as-tooltip-popup-or-labels-in-folium-choropleth-geojson-polygons) to the choropleth to get exact values for each municipality 
- paths currently don't distinguish between connections (i.e. there is a change between two consecutive edges) or staying on the same train 
  - we need to consider the time it takes to change trains within the same stop.
  - we need to detect when such a change happens (as compared to staying on the train)
  - we need to remember not only the latest departure for each stop but all departures at most X minutes earlier than the latest departure, where X is the duration it takes to change at this location
  

## Possible Extensions

- Visualization:
  - Add code to generate a Voronoi-diagram based geojson
  - "deformed" maps
- Streamline the "building" of the application (database construction, installation of dependencies etc.)
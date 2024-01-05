

# SBB Map

## Overview

A python streamlit app to visualize the "public-transportation distance" between different locations in switzerland.

Concretely, specifying a destination (a public transportation stop), a date, and a time a [choropleth map](https://datavizcatalogue.com/methods/choropleth.html) of the country is generated where each municipality is colored according to the latest departure time necessary to arrive in time at the specified destination.
Different stops in the same municipality are aggregated by the minimum function.


![Example](/images/screenshot_4_jan_zurich.png)
The image above shows a screenshot from the app: In this example, we want to get to Zürich by 9 AM while limiting the departure time to be after 7:30 AM. Hovering over Aarau shows that from Aarau we need to leave by 8:23. Municipalities from which Zürich cannot be reached in time when leaving after 7:30 AM are shown in black.

Granularity of aggregation depends on the "features" in the geojson data. E.g. given a geojson file containing a voronoi diagram of all public transportation stops in the country, there would be no aggregation at all.

The implementation is generic - providing the following data should suffice to "port" the app to other countries
- [GTFS Data](https://developers.google.com/transit/gtfs/reference) about the public transportation of the country
- Geojson file with a partition of the country specifying the granularity of the choropleth map


## Major Components

- A relational database is populated with the GTFS data using the init_db.sql script
- A simple [Streamlit](https://streamlit.io/) app allows the user to specify a destination station, date and time and displays the resulting map using the [Folium](https://python-visualization.github.io/folium/latest/) library.
- A BFS algorithm traverses the "connection graph" of the public transportation network



## How to run

### Get the necessary data

The data source depends on the country. For Switzerland we can get the relevant data from
- GTFS: [Open Transport Data](https://opentransportdata.swiss/dataset)
- Geojson: [Datahub](https://datahub.io/cividi/ch-municipalities)

The code currently requires that each feature in the geojson file specifies an "id" in properties

### Generate the database

Setup a database and a database user if necessary. 
You can use Postgres for instance, but any relational database will do. 
For a postgres on Linux setup you can follow the [Arch Linux documentation](https://wiki.archlinux.org/title/PostgreSQL).

After initial setup is done, create an empty database (see also the [documentation](https://www.postgresql.org/docs/current/sql-createdatabase.html))

```sql
CREATE DATABASE sbb_map WITH OWNER <user>;
```

Initialize the database using the GTFS data and the initialization script

```bash
# Inside the directory with the GTFS data
psql -d sbb_map -U <user> -W -f ./<path-to-src>/init_db.sql -1
```

In order for python to be able to access the database we need to ensure that the correct environment variables are set. This is best achieved by using [direnv](https://direnv.net/).

```bash
# Inside the root directory of the project and after installing direnv
direnv allow .
echo "export DBUSER=<user>" > .envrc
echo "export DBPASS=<password>" >> .envrc
echo "export DBPORT=5432" >> .envrc
echo "export DBHOST=localhost" >> .envrc
echo "export DBNAME=sbb_map" >> .envrc
```

### Install the dependencies

```bash
python -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```

### Run the application

```bash
# Inside the root directory of the project with virtual environment enabled
python -m streamlit run main.py
```


## TODOs

- Streamline setup of application
- Allow for geojsons without properties.id
- paths currently don't distinguish between connections (i.e. there is a change between two consecutive edges) or staying on the same train 
  - we need to consider the time it takes to change trains within the same stop.
  - we need to detect when such a change happens (as compared to staying on the train)
  - we need to remember not only the latest departure for each stop but all departures at most X minutes earlier than the latest departure, where X is the duration it takes to change at this location
  

## Possible Extensions

- Visualization:
  - Add code to generate a Voronoi-diagram based geojson
  - "deformed" maps
- Streamline the "building" of the application (database construction, installation of dependencies etc.)
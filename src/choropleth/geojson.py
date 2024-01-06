import json
from typing import Dict
from shapely import *

class Geojson:

    def __init__(self, json_data):
        self._json_data = json_data
        self._geometry_collection = from_geojson(json.dumps(json_data))

        for geometry, feature in zip(self._geometry_collection.geoms, json_data["features"]):
            assert "id" in feature
            assert feature["geometry"]["type"] == geometry.geom_type

    def get_geojson(self):
        return self._json_data
    
    def get_geometry_collection(self):
        return self._geometry_collection

    def get_feature_covering_lat_lon(self, lat : float, lon : float):
        p = Point(lon, lat)
        geometry_collection = self.get_geometry_collection()
        for idx, geometry in enumerate(geometry_collection.geoms):
            if geometry.contains(p):
                geojson = self.get_geojson()
                return geojson["features"][idx]
        return None

    


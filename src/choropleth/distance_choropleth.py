
from shapely import *
import json

SUBPROBLEM_LIMIT = 1000

def create_choropleth(coord_to_departure, geojson):
    """Creates a mapping from geojson feature id to departure time.
    The departure time of feature f is taken as the minimum departure time 
    of coordinates that lie within f.
    
    Assumes that each geojson feature contains the path "id" 
    where id is a unique id of the feature.

    Uses shapely to perform the geometric operations on the geojson features.
    """

    def aggregate(x,y):
        """Aggregate the departure times using the max operation.
        Thus, every geometry is mapped to the latest departure time of any coord contained in it."""
        if x is None:
            return y
        if y is None:
            return x
        return max(x,y)


    def create_choropleth_rec(coords, features : GeometryCollection):

        def partition_geometries_on_polytope(geometries, polytope):
            inside = []
            outside = []
            for feature in geometries:
                if polytope.contains(feature):
                    inside.append(feature)
                elif polytope.intersects(feature):
                    inside.append(feature)
                    outside.append(feature)
                else:
                    outside.append(feature)
            return inside, outside

        print("called with coords: ", len(coords), "and features", len(features.geoms))  
        if len(coords) * len(features.geoms) < SUBPROBLEM_LIMIT:
            choropleth = {}
            # check inclusion of each coord in each feature
            for x,y in coords:
                for geometry in features.geoms:
                    if geometry.contains(Point(x,y)):
                        if geometry not in choropleth:
                            choropleth[geometry] = coord_to_departure[(x,y)]
                        choropleth[geometry] = aggregate(
                            coord_to_departure[(x,y)],
                            choropleth[geometry]
                        )
            return choropleth
        
        # split both coords and features along one axis and solve the two resulting subproblems
        x_min, y_min, x_max, y_max = features.bounds
        if x_max - x_min > y_max - y_min:
            x_half = x_min + x_max / 2
            half = Polygon([(x_min, y_min), (x_half, y_min), (x_half, y_max), (x_min, y_max)])
        else:
            y_half = y_min + y_max / 2
            half = Polygon([(x_min, y_min), (x_max, y_min), (x_max, y_half), (x_min, y_half)])
        coords1, coords2 = partition_geometries_on_polytope([Point(x,y) for x,y in coords], half)
        features1, features2 = partition_geometries_on_polytope(features.geoms, half)

        choropleth = create_choropleth_rec(coords1, GeometryCollection(features1))
        choropleth_other = create_choropleth_rec(coords2, GeometryCollection(features2))
        for geometry in choropleth_other:
            if geometry in choropleth:
                choropleth[geometry] = aggregate(
                    choropleth[geometry],
                    choropleth_other[geometry]
                )
            else:
                choropleth[geometry] = choropleth_other[geometry]
        
        return choropleth

    geometry_collection = from_geojson(json.dumps(geojson))
    assert geometry_collection.geom_type == "GeometryCollection"
    valid_geometries = GeometryCollection([
        geometry for geometry in geometry_collection.geoms
        if geometry.geom_type in ["Polygon", "MultiPolygon"]
    ])
    valid_coords = [
        (x,y) for x,y in coord_to_departure
        if valid_geometries.contains(Point(x,y))
    ]

    for geometry, feature in zip(valid_geometries.geoms, geojson["features"]):
        assert "id" in feature
        assert feature["geometry"]["type"] == geometry.geom_type


    choropleth = create_choropleth_rec(valid_coords, valid_geometries)
    return {
        feature["id"]: choropleth.get(geometry)
        for geometry, feature in zip(valid_geometries.geoms, geojson["features"])
    }





        
        

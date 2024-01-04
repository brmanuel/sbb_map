
from shapely import *
import json
import click

SUBPROBLEM_LIMIT = 10000

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


    def create_choropleth_rec(coords, features : GeometryCollection, bounds):

        def partition_geometries_on_polytope(geometries, bounds):
            x_min, y_min, x_max, y_max = bounds
            polytope = Polygon([(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)])
            inside = []
            outside = []
            for feature in geometries.geoms:
                if polytope.contains(feature):
                    inside.append(feature)
                elif polytope.intersects(feature):
                    inside.append(feature)
                    outside.append(feature)
                else:
                    outside.append(feature)
            return inside, outside

        print("called with coords", len(coords.geoms), "and features", len(features.geoms))  
        if len(coords.geoms) * len(features.geoms) < SUBPROBLEM_LIMIT:
            choropleth = {}
            # check inclusion of each coord in each feature
            for p in coords.geoms:
                x, y = p.x, p.y
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
        x_min, y_min, x_max, y_max = bounds
        if x_max - x_min > y_max - y_min:
            x_half = (x_min + x_max) / 2
            bounds1 = (x_min, y_min, x_half, y_max)
            bounds2 = (x_half, y_min, x_max, y_max)
        else:
            y_half = (y_min + y_max) / 2
            bounds1 = (x_min, y_min, x_max, y_half)
            bounds2 = (x_min, y_half, x_max, y_max)
        print(f"features are bounded by {bounds} splitting on {bounds1}")
        coords1, coords2 = partition_geometries_on_polytope(coords, bounds1)
        features1, features2 = partition_geometries_on_polytope(features, bounds1)

        choropleth = create_choropleth_rec(GeometryCollection(coords1), GeometryCollection(features1), bounds1)
        choropleth_other = create_choropleth_rec(GeometryCollection(coords2), GeometryCollection(features2), bounds2)
        for geometry in choropleth_other:
            if geometry in choropleth:
                choropleth[geometry] = aggregate(
                    choropleth[geometry],
                    choropleth_other[geometry]
                )
            else:
                choropleth[geometry] = choropleth_other[geometry]
        
        return choropleth

    print("called")
    geometry_collection = from_geojson(json.dumps(geojson))
    print("loaded geometry")
    assert geometry_collection.geom_type == "GeometryCollection"
    valid_geometries = GeometryCollection([
        geometry for geometry in geometry_collection.geoms
        if geometry.geom_type in ["Polygon", "MultiPolygon"]
    ])
    print("filtered geometry")
    valid_coords = MultiPoint([[x,y] for x,y in coord_to_departure])
        
    print("filtered coords")

    for geometry, feature in zip(valid_geometries.geoms, geojson["features"]):
        assert "id" in feature
        assert feature["geometry"]["type"] == geometry.geom_type

    print("validated geometry and coords")

    geoms_bounds = valid_geometries.bounds
    coord_bounds = valid_coords.bounds
    bounds = (
        min(geoms_bounds[0], coord_bounds[0]),
        min(geoms_bounds[1], coord_bounds[1]),
        max(geoms_bounds[2], coord_bounds[2]),
        max(geoms_bounds[3], coord_bounds[3]),
    )

    choropleth = create_choropleth_rec(valid_coords, valid_geometries, bounds)
    return {
        feature["id"]: choropleth.get(geometry)
        for geometry, feature in zip(valid_geometries.geoms, geojson["features"])
    }


@click.command()
@click.argument("mapping_file")
def main(mapping_file):
    GEOJSON = "data/geojson/rothrist-municipalities.geojson"
    with open(mapping_file, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    coord_to_departure = {
        (val["lon"], val["lat"]): val["departure"]
        for val in mapping.values()
    }

    with open(GEOJSON, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    choropleth = create_choropleth(coord_to_departure, geojson)



if __name__ == "__main__":
    main()


        
        

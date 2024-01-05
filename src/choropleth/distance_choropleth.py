
from shapely import *
import json
import click
import time

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

    choropleth = {}

    def create_choropleth_rec(
        geometries_list, 
        geometries_idxs, 
        coords_list, 
        coords_idxs, 
        bounds
    ):
        nonlocal choropleth
        
        def partition_geometries_on_x_axis(feature_list, feature_idxs, x):
            left = []
            right = []
            for idx in feature_idxs:
                feature = feature_list[idx]
                x_min, _, x_max, _ = feature.bounds
                if x_min <= x:
                    left.append(idx)
                if x_max >= x:
                    right.append(idx)
            return left, right
        
        def partition_geometries_on_y_axis(feature_list, feature_idxs, y):
            top = []
            bottom = []
            for idx in feature_idxs:
                feature = feature_list[idx]
                _, y_min, _, y_max = feature.bounds
                if y_min <= y:
                    bottom.append(idx)
                if y_max >= y:
                    top.append(idx)
            return bottom, top

        print("called with coords", len(coords_idxs), "and features", len(geometries_idxs))  
        if len(coords_idxs) * len(geometries_idxs) < SUBPROBLEM_LIMIT:
            # Base case: check inclusion of each coord in each feature
            for p_idx in coords_idxs:
                p = coords_list[p_idx]
                x, y = p.x, p.y
                for geometry_idx in geometries_idxs:
                    geometry = geometries_list[geometry_idx]
                    if geometry.contains(p):
                        choropleth[geometry_idx] = aggregate(
                            coord_to_departure[(x,y)],
                            choropleth.get(geometry_idx)
                        )
                        break
        else:
            # Recursive case: split both coords and features along one axis and recurse
            x_min, y_min, x_max, y_max = bounds
            if x_max - x_min > y_max - y_min:
                half = (x_min + x_max) / 2
                bounds1 = (x_min, y_min, half, y_max)
                bounds2 = (half, y_min, x_max, y_max)
                coords_idxs1, coords_idxs2 = partition_geometries_on_x_axis(coords_list, coords_idxs, half)
                geometries_idxs1, geometries_idxs2 = partition_geometries_on_x_axis(geometries_list, geometries_idxs, half)
            else:
                half = (y_min + y_max) / 2
                bounds1 = (x_min, y_min, x_max, half)
                bounds2 = (x_min, half, x_max, y_max)    
                coords_idxs1, coords_idxs2 = partition_geometries_on_y_axis(coords_list, coords_idxs, half)
                geometries_idxs1, geometries_idxs2 = partition_geometries_on_y_axis(geometries_list, geometries_idxs, half)

            create_choropleth_rec(geometries_list, geometries_idxs1, coords_list, coords_idxs1, bounds1)
            create_choropleth_rec(geometries_list, geometries_idxs2, coords_list, coords_idxs2, bounds2)

    geometry_collection = from_geojson(json.dumps(geojson))

    assert geometry_collection.geom_type == "GeometryCollection"
    valid_geometries = GeometryCollection([
        geometry for geometry in geometry_collection.geoms
        if geometry.geom_type in ["Polygon", "MultiPolygon"]
    ])

    valid_coords = MultiPoint([[x,y] for x,y in coord_to_departure])
        
    for geometry, feature in zip(valid_geometries.geoms, geojson["features"]):
        assert "id" in feature
        assert feature["geometry"]["type"] == geometry.geom_type

    geoms_bounds = valid_geometries.bounds
    coord_bounds = valid_coords.bounds
    bounds = (
        min(geoms_bounds[0], coord_bounds[0]),
        min(geoms_bounds[1], coord_bounds[1]),
        max(geoms_bounds[2], coord_bounds[2]),
        max(geoms_bounds[3], coord_bounds[3]),
    )

    geometries_list = list(valid_geometries.geoms)
    coords_list = list(valid_coords.geoms)
    geometries_idxs = list(range(len(geometries_list)))
    coords_idxs = list(range(len(coords_list)))
    create_choropleth_rec(geometries_list, geometries_idxs, coords_list, coords_idxs, bounds)
    return {
        feature["id"]: choropleth.get(idx)
        for idx, feature in zip(geometries_idxs, geojson["features"])
    }


@click.command()
@click.argument("mapping_file")
def main(mapping_file):
    GEOJSON = "data/geojson/ch-municipalities.geojson"
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


        
        


from shapely import *

SUBPROBLEM_LIMIT = 1000

def create_choropleth(coord_to_departure, geojson):
    """Creates a mapping from geojson feature id to departure time.
    The departure time of feature f is taken as the minimum departure time 
    of coordinates that lie within f.
    
    Assumes that each geojson feature contains the path "properties.id" 
    where id is a unique id of the feature.

    Uses shapely to perform the geometric operations on the geojson features.
    """

    def aggregate(x,y):
        """Aggregate the departure times using the max operation.
        Thus, every geometry is mapped to the latest departure time of any coord contained in it."""
        return max(x,y)


    id_map = {} # mapping from shapely geometry to feature.properties.id


    def create_choropleth_rec(coords, features : GeometryCollection):
        if len(coords) * len(features) < SUBPROBLEM_LIMIT:
            choropleth = {}
            # check inclusion of each coord in each feature
            for x,y in coords:
                for geometry in features.geoms:
                    if geometry.contains(Point(x,y)):
                        geometry_id = id_map[geometry]
                        if geometry_id not in choropleth:
                            choropleth[geometry_id] = coord_to_departure[(x,y)]
                        choropleth[geometry_id] = aggregate(
                            coord_to_departure[(x,y)],
                            choropleth[geometry_id]
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
        coords1 = []
        coords2 = []
        features1 = []
        features2 = []
        for x,y in coords:
            if half.contains(Point(x,y)):
                coords1.append((x,y))
            else:
                coords2.append((x,y))
        for feature in features.geoms:
            if half.contains(feature):
                features1.append(feature)
            elif half.intersects(feature):
                features1.append(feature)
                features2.append(feature)
            else:
                features2.append(feature)

        choropleth = create_choropleth_rec(coords1, GeometryCollection(features1))
        choropleth_other = create_choropleth_rec(coords2, GeometryCollection(features2))
        for geometry_id in choropleth_other:
            if geometry_id in choropleth:
                choropleth[geometry_id] = aggregate(
                    choropleth[geometry_id],
                    choropleth_other[geometry_id]
                )
            else:
                choropleth[geometry_id] = choropleth_other[geometry_id]
        
        return choropleth

        
        

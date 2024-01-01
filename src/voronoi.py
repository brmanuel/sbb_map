
import click
import random
import math
import csv



def read_stops(infile):
    stops = {}
    with open(infile, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=",")
        next(reader) # skip header line
        for line in reader:
            name, lat, lon = line[1:4]
            if name not in stops:
                stops[name] = (float(lat), float(lon))
    return stops


def find_bounding_triangle(stops):
    # find minimum area equilateral triangle 
    # containing all stops
    def find_intersection(a, dir_a, b, dir_b):
        # s = (a[1] - b[1]) / ((dir_a[1] / dir_a[0]) * dir_b[0] - dir_b[1])
        pass

    dir_a = (0, -1)
    dir_b = (math.cos(math.pi / 6), math.sin(math.pi / 6))
    dir_c = (math.cos(5*math.pi / 6), math.sin(5*math.pi / 6))
    bounding_points = []
    line_vectors = []
    for dx, dy in [dir_a, dir_b, dir_c]:
        max_point_dir = max(stops, key=lambda x: dx*x[0]+dy*x[1])
        bounding_points.append(max_point_dir)
        line_vectors.append((-dy, dx))
    p_a, p_b, p_c = bounding_points
    dir_at, dir_bt, dir_ct = line_vectors
    p_x = find_intersection(p_a, dir_at, p_b, dir_bt)
    p_y = find_intersection(p_a, dir_at, p_c, dir_ct)
    p_z = find_intersection(p_b, dir_bt, p_c, dir_ct)
    return (p_x, p_y, p_z)

class Triangle:
    def __init__(self, a, b, c):
        self._a = a
        self._b = b
        self._c = c
        self._replacement = None

    def __hash__(self):
        return sorted(self._a, self._b, self._c)

    @property
    def a(self):
        return self._a

    @property
    def b(self):
        return self._b

    @property
    def c(self):
        return self._c

    @property
    def ab(self):
        return sorted(self._a, self._b)

    @property
    def bc(self):
        return sorted(self._b, self._c)

    @property
    def ca(self):
        return sorted(self._c, self._a)

    def contains(self, point): 
        pass

    def is_replaced(self):
        return self._replacement is not None

    def replacement(self):
        assert self._replacement is not None
        return self._replacement

    def set_replacement(self, triangles):
        assert self._replacement is None
        self._replacement = set()
        for t in triangles:
            self._replacement.add(t)

    @staticmethod
    def delaunay_condition(t1 : "Triangle", t2 : "Triangle"):
        # for two triangles t1 = (a,b,c), t2 = (a,b,d) sharing one side
        # ab, we check if d is contained in circumcircle of t1 and return
        # false if it is and true otherwise
        def before(root, p1, p2):
            det = (
                (p1[0] - root[0]) * (p2[1] - root[1]) - 
                (p2[0] - root[0]) * (p1[1] - root[1])
            )
            return det < 0

        # sort a,b,c in counterclockwise order
        points = [t1.a, t1.b, t1.c]
        ds = set([t2.a, t2.b, t2.c]) - set(points)
        assert len(ds) == 1
        d = list(ds)[0]
        sorted_points = {}
        for point in points:
            idx = 0
            for other in points:
                if before((0,0), other, point):
                    idx += 1
            sorted_points[idx] = point

        # compute the determinant (-> delaunay condition)
        # https://en.wikipedia.org/wiki/Delaunay_triangulation
        matrix = []
        for idx in range(3):
            x, y = sorted_points[idx]
            matrix.append([x, y, x*x+y*y, 1])
        matrix.append([d[0], d[1], d[0]*d[0]+d[1]*d[1], 1])

        # compute all permuations of [0,1,2,3] with their sgn
        permutations = {0: [[0,1,2,3]]}
        created_permutations = {}
        seen = set()
        replacements = 0
        while replacement in permutations:
            while len(permutations[replacements]) > 0:
                p = permutations[replacements].pop(0)
                if p in seen:
                    continue
                seen.add(p)
                if replacement not in created_permutations:
                    created_permutations[replacement] = []
                created_permutations[replacement].append(p)
                if replacement+1 not in permutations:
                    permutations[replacement+1] = []
                for i in range(len(p)):
                    for j in range(i+1, len(p)):
                        new_p = [x for x in p]
                        new_p[i] = p[j]
                        new_p[j] = p[i]
                        permutations[replacement+1].append(new_p)
            replacement += 1


        det = 0
        for replacement in created_permutations:
            sgn = 1 if (replacement % 2) == 0 else -1
            for p in created_permutations[replacement]:
                prod = sgn
                for i in range(4):
                    prod *= matrix[i][p[i]]
                det += prod

        # det is > 0 if d lies in the circumcircle of (a,b,c)
        return det <= 0



def compute_delaunay(points):
    root_triangle = find_bounding_triangle(points)
    
    # Contract: only contains triangles that have not been replaced
    arc_to_triangles = {
        root_triangle.ab: set([root_triangle, None]),
        root_triangle.bc: set([root_triangle, None]),
        root_triangle.ca: set([root_triangle, None])
    } # :: Map[(point, point), Set[triangle]]
    
    random.shuffle(points)
    for point in points:
        # find containing triangle
        triangle = root_triangle
        while triangle.is_replaced():
            for candidate_triangle in triangle.replacement():
                if candidate_triangle.contains(point):
                    triangle = candidate_triangle
                    break

        # split triangle into 3 new triangles
        triangle_ab = Triangle(triangle.a, triangle.b, point)
        triangle_bc = Triangle(triangle.b, triangle.c, point)
        triangle_ca = Triangle(triangle.c, triangle.a, point)
        triangle.set_replacement([
            triangle_ab, triangle_bc, triangle_ca
        ])
        arc_to_triangles[sorted(triangle.b, point)] = set([triangle_ab, triangle_bc])
        arc_to_triangles[sorted(triangle.c, point)] = set([triangle_bc, triangle_ca])
        arc_to_triangles[sorted(triangle.a, point)] = set([triangle_ca, triangle_ab])
        
        triangle_pairs_to_check = []
        for side, new_triangle in [
            (triangle.ab, triangle_ab), 
            (triangle.bc, triangle_bc), 
            (triangle.ca, triangle_ca)
        ]:
            pair = arc_to_triangles[side]
            pair.remove(triangle)
            pair.add(new_triangle)
            triangle_pairs_to_check.append(pair)
        

        while len(triangle_pairs_to_check) > 0:
            pair = triangle_pairs_to_check.pop(0)
            t1, t2 = list(pair)
            if (
                not Triangle.delaunay_condition(t1, t2)
                or not Triangle.delaunay_condition(t2, t1)
            ):
                points_t1 = set([t1.a, t1.b, t1.c])
                points_t2 = set([t2.a, t2.b, t2.c])
                common = points_t1 & points_t2
                assert len(common) == 2
                common_a, common_b = list(common)
                uncommon_c1 = list(points_t1 - common)[0]
                uncommon_c2 = list(points_t2 - common)[0]
                common_side = sorted(common_a, common_b)
                uncommon_side = sorted(uncommon_c1, uncommon_c2)

                new_t1 = Triangle(common_a, common_b, uncommon_c1)
                new_t2 = Triangle(common_a, common_b, uncommon_c2)
                t1.set_replacement([new_t1, new_t2])
                t2.set_replacement([new_t1, new_t2])

                del arc_to_triangles[common_side]
                arc_to_triangles[uncommon_side] = set([new_t1, new_t2])

                for triangle in [new_t1, new_t2]:
                    for side in [triangle.ab, triangle.bc, triangle.ca]:
                        if side != uncommon_side:
                            pair = arc_to_triangles[side]
                            pair -= set([t1, t2])
                            pair.add(triangle)
                            triangle_pairs_to_check.append(pair)

    return root_triangle

        
def compute_dual(delaunay):
    pass


def compute_voronoi(stops):
    points_to_stops = {
        point: stop
        for stop, point in stops.items()
    }
    delaunay = compute_delaunay(stops.values())
    voronoi = compute_dual(delaunay)
    return voronoi


@click.command()
@click.argument("infile")
@click.argument("outfile")
def main(infile, outfile):
    stops = read_stops(infile)
    voronoi = compute_voronoi(stops)
    write_stops(outfile)


if __name__ == "__main__":
    main()
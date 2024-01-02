from sqlalchemy import create_engine, text
from config import DATABASE_URI
from datetime import date, timedelta
from priority_queue import PriorityQueue
from pprint import pprint
import json
import click

NEG_INFTY = -1

engine = create_engine(DATABASE_URI)
conn = engine.connect()


def parse_date(datestr):
    """
    Assumes datestr is given in format YYYY-MM-DD.
    """
    dt = date.fromisoformat(datestr)
    return dt

def parse_time(timestr):
    """
    Assumes timestr is given in format hh:mm.
    Returns the number of seconds since midnight.
    """
    hh, mm = timestr.split(":")
    return 3600 * int(hh) + 60 * int(mm)

def print_time(seconds):
    hh = seconds // 3600
    mm = (seconds % 3600) // 60
    return f"{hh}:{mm}"

def seconds_to_interval(seconds):
    """Database represents times as intervals."""
    return timedelta(seconds=seconds)

def interval_to_seconds(interval : timedelta):
    """We represent times as integers in seconds after midnight."""
    return int(interval.total_seconds())
    

def get_edges_in_timerange(date, start_time, end_time):
    '''
    assumes date is given in format YYYY-MM-DD
    and start_time, end_time are given in format hh:mm:ss
    '''
    print(f"Query edges: {start_time} - {end_time}")
    day = [
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
    ][date.weekday()]
    start_time_interval = seconds_to_interval(start_time)
    end_time_interval = seconds_to_interval(end_time)
    
    query = """
    SELECT from_stop_id, to_stop_id, departure, arrival
    FROM edges
    WHERE departure >= INTERVAL '{}'
    AND departure <= INTERVAL '{}'
    AND {} = 1
    AND start_date <= '{}'::date
    AND end_date >= '{}'::date;
    """.format(start_time_interval, end_time_interval, day, date, date)

    stmt = text(query)
    edges = [
        (src, dst, interval_to_seconds(dep), interval_to_seconds(arr))
        for src, dst, dep, arr in conn.execute(stmt).fetchall()
    ]
    return edges

def get_in_edges_in_timerange(date, start_time, end_time):
    in_edges = {}
    edges = get_edges_in_timerange(date, start_time, end_time)
    for src, dst, dep, arr in edges:
        if dst not in in_edges:
            in_edges[dst] = set()
        in_edges[dst].add((src, dep, arr))
    return in_edges

def get_transfers():
    query = """
    SELECT from_stop_id, to_stop_id, min_transfer_time
    FROM transfer
    WHERE transfer_type = 2;
    """
    stmt = text(query)
    transfers = conn.execute(stmt).fetchall()
    return transfers

def get_in_transfers():
    transfers = get_transfers()
    in_transfers = {}
    for src, dst, transfer_time in transfers:
        if dst not in in_transfers:
            in_transfers[dst] = []
        in_transfers[dst].append((src, transfer_time))
    return in_transfers

def get_locations():
    query = """
    SELECT stop_id, stop_name, stop_lat, stop_lon
    FROM stop;
    """
    stmt = text(query)
    stops = conn.execute(stmt).fetchall()
    return stops


def traverse(location_dict, start_id, date, earliest_departure):
    def update_neighbors(node):
        departure = location_dict[node]["departure"]
        for src, dep, arr in in_edges.get(node, []):
            if src not in fixed and src in location_dict and arr <= departure:
                updated = q.update(src, dep)
                if updated:
                    location_dict[src]["pred"] = node
                    location_dict[src]["departure"] = dep
        for src, transfer_time in in_transfers.get(node, []):
            if src not in fixed and src in location_dict:
                updated = q.update(src, departure-transfer_time)
                if updated:
                    location_dict[src]["pred"] = node
                    location_dict[src]["departure"] = departure-transfer_time

    q = PriorityQueue(lambda x: -x)
    fixed = set([start_id])
    for id, location in location_dict.items():
        q.add(id, location["departure"])
    time_increment = 3600
    time_ub = location_dict[start_id]["departure"]
    time_lb = max(time_ub - time_increment, earliest_departure)
    in_edges = get_in_edges_in_timerange(date, time_lb, time_ub)
    in_transfers = get_in_transfers()
    while q.size() > 0 and time_ub > earliest_departure:
        id, departure = q.peek()
        if departure == NEG_INFTY:
            time_lb = max(time_lb - time_increment, earliest_departure)
            time_ub = max(time_ub - time_increment, earliest_departure)
            in_edges = get_in_edges_in_timerange(date, time_lb, time_ub)
            for dst in fixed:
                update_neighbors(dst)
        else:
            q.pop()
            fixed.add(id)
            update_neighbors(id)

    return location_dict


def compute_map(location, date, time, earliest_departure=0):
    locations = get_locations()
    location_dict = {}
    start_id = None
    for id, name, lat, lon in locations:
        location_dict[id] = {"name": name, "lat": lat, "lon": lon, "departure": NEG_INFTY, "pred": None}
        if name == location:
            start_id = id
            location_dict[id]["departure"] = time
    if start_id is None:
        print(f"Location {location} not in database. Exiting.")
        exit(1)
        
    traverse(location_dict, start_id, date, earliest_departure)
    return location_dict


@click.command()
@click.argument("location")
@click.argument("datestr")
@click.argument("timestr")
def main(location, datestr, timestr):
    date = parse_date(datestr)
    time = parse_time(timestr)
    mapping = compute_map(location, date, time)
    for id in mapping.keys():
        seconds = mapping[id]["departure"]
        if seconds >= 0:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            mapping[id]["departure"] = f"{hours}:{minutes}:{seconds}"
        else:
            mapping[id]["departure"] = None
    print(json.dumps(mapping, indent=4))
    

if __name__ == "__main__":
    main()
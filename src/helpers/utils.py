import datetime

def parse_time(time : datetime.time):
    if time is None:
        return None
    return time.minute + time.hour * 60
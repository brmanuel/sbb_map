

/*
replicate relational model as described in 
https://opentransportdata.swiss/de/dataset/timetable-2021-gtfs2020

note that sbb data is incomplete, so we only implement the subset that exists in the data:

==> agency.txt <==
agency_id,agency_name,agency_url,agency_timezone,agency_lang,agency_phone

==> calendar_dates.txt <==
service_id,date,exception_type

==> calendar.txt <==
service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date

==> feed_info.txt <==
feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date,feed_version

==> routes.txt <==
route_id,agency_id,route_short_name,route_long_name,route_desc,route_type

==> stops.txt <==
stop_id,stop_name,stop_lat,stop_lon,location_type,parent_station

==> stop_times.txt <==
trip_id,arrival_time,departure_time,stop_id,stop_sequence,pickup_type,drop_off_type

==> transfers.txt <==
from_stop_id,to_stop_id,transfer_type,min_transfer_time

==> trips.txt <==
route_id,service_id,trip_id,trip_headsign,trip_short_name,direction_id
*/

create table route (
       route_id text primary key,
       agency_id text,
       route_short_name text,
       route_long_name text,
       route_desc text,
       route_type int
);

\copy route from 'routes.txt' delimiter ',' csv header;

create table stop (
       stop_id text primary key,
       stop_name text,
       stop_lat real,
       stop_lon real,
       location_type int,
       parent_station text references stop (stop_id)
);

-- copy over data from csv files
-- need to use temporary table to convert "" to null
create table stop_tmp as table stop limit 0;
alter table stop_tmp alter column location_type type text;
\copy stop_tmp from 'stops.txt' delimiter ',' csv header;
insert into stop select stop_id, stop_name, stop_lat, stop_lon, NULLIF(location_type, '')::int, NULLIF(parent_station, '') from stop_tmp;
drop table stop_tmp;


create table calendar (
       service_id text primary key,
       monday int,
       tuesday int,
       wednesday int,
       thursday int,
       friday int,
       saturday int,
       sunday int,
       start_date date,
       end_date date
);

\copy calendar from 'calendar.txt' delimiter ',' csv header;

create table trip (
       route_id text references route (route_id),
       service_id text references calendar (service_id),
       trip_id text primary key,
       trip_headsign text,
       trip_shortname text,
       direction_id int,
       block_id text
);

\copy trip from 'trips.txt' delimiter ',' csv header;

create table stoptime (
       trip_id text references trip (trip_id),
       arrival_time interval,
       departure_time interval,
       stop_id text references stop (stop_id),
       stop_sequence int,
       pickup_type int,
       dropoff_type int
);


create table stoptime_tmp as table stoptime limit 0;
alter table stoptime_tmp alter column stop_sequence type text;
alter table stoptime_tmp alter column pickup_type type text;
alter table stoptime_tmp alter column dropoff_type type text;
\copy stoptime_tmp from 'stop_times.txt' delimiter ',' csv header;
insert into stoptime select trip_id, arrival_time, departure_time, stop_id, NULLIF(stop_sequence, '')::int, NULLIF(pickup_type, '')::int, NULLIF(dropoff_type, '')::int from stoptime_tmp;
ALTER TABLE stoptime ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE stoptime ADD COLUMN rank INT;
UPDATE stoptime s SET rank = t.rank from (
       select id, rank() over (
              partition by trip_id order by stop_sequence
       ) from stoptime
) as t where s.id = t.id;

drop table stoptime_tmp;

create table transfer (
       from_stop_id text references stop (stop_id),
       to_stop_id text references stop (stop_id),
       transfer_type integer,
       min_transfer_time integer
);

\copy transfer from 'transfers.txt' delimiter ',' csv header;


create index trip_service_id on trip (service_id);
create index stoptime_trip_id on stoptime (trip_id);

create table edges (from_stop_id, to_stop_id, departure, arrival, trip_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date) as
       select lft.stop_id,
       	      rgt.stop_id,
	      lft.departure_time,
	      rgt.arrival_time,
	      lft.trip_id,
	      cal.monday,
	      cal.tuesday,
	      cal.wednesday,
	      cal.thursday,
	      cal.friday,
	      cal.saturday,
	      cal.sunday,
	      cal.start_date,
	      cal.end_date 
       from stoptime lft join stoptime rgt
       on lft.trip_id = rgt.trip_id and lft.rank + 1 = rgt.rank join trip
       on lft.trip_id = trip.trip_id join calendar cal
       on trip.service_id = cal.service_id;

create table test_stop (stop_id, stop_name, stop_lat, stop_lon, location_type, parent_station) as
    select * 
    from stop 
    where stop_lat - 47.378178 < 0.2
    and 47.378178 - stop_lat < 0.2
    and stop_lon - 8.540212 < 0.2 
    and 8.540212 - stop_lon < 0.2;


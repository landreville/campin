create user campin with password 'whatever you want';
create schema campin;
grant usage on schema campin to campin;


create table campin.parks(
  park_id serial primary key,
  park_name varchar not null unique,
  parent_park_id integer references campin.parks(park_id),
  address varchar,
  activities jsonb not null default '{}'::jsonb,
  facilities jsonb not null default '{}'::jsonb,
  usages jsonb not null default '[]'::jsonb,
  operating_date_from date,
  operating_date_to date,
  map_image varchar,
  map_width varchar,
  map_height varchar,
  last_modified_date timestamp with time zone not null default current_timestamp
);


create table campin.park_drive_hours(
  park_id integer not null references campin.parks(park_id),
  origin varchar not null,
  drive_hours interval not null,
  primary key (park_id, origin)
);


create table campin.campgrounds(
  camground_id serial primary key,
  campground_name varchar not null,
  park_id integer not null references campin.parks(park_id),
  map_image varchar,
  map_top varchar,
  map_left varchar,
  constraint campgrounds_park_uk unique(park_id, campground_name)
);


create table campin.campsites(
  campsite_id serial primary key,
  park_id integer not null references campin.parks(park_id),
  site_number varchar not null,
  parent_park_name varchar,
  park_name varchar not null,
  campground_name varchar,
  site_type varchar,
  fee_type varchar,
  restrictions jsonb not null default '[]'::jsonb,
  service_type varchar,
  site_shade varchar,
  quality varchar,
  privacy varchar,
  conditions varchar,
  ground_cover varchar,
  adjacent_to varchar,
  allowed_equipment jsonb not null default '[]'::jsonb,
  on_site_parking integer,
  off_site_parking integer,
  reservable_online boolean,
  details jsonb not null default '{}'::jsonb,
  last_modified_date timestamp with time zone not null default current_timestamp,
  constraint campsites_park_id_site_number_uk unique(park_id, site_number),
  constraint campsites_park_name_site_number_uk unique(park_name, site_number)
);


create table campin.campsite_images(
  campsite_image_id serial primary key,
  campsite_id integer references campin.campsites(campsite_id),
  image_name varchar not null unique
);

create index campsite_id_idx on campin.campsite_images(campsite_id);


create table campin.reservations(
  reservation_id serial primary key,
  campsite_id integer not null references campin.campsites(campsite_id),
  reserve_date date not null,
  reason varchar,
  last_modified_date timestamp with time zone not null default current_timestamp,
  constraint reservations_uk unique(campsite_id, reserve_date)
);

create index reservations_date_idx on campin.reservations(reserve_date);

grant select,insert,update,delete on all tables in schema campin to campin;
grant usage on all sequences in schema campin to campin;

create or replace function update_last_modified() returns trigger as $$
BEGIN
  NEW.last_modified_date := current_timestamp;
  RETURN NEW;
END; $$ language plpgsql;

create trigger campsites_last_modified
  BEFORE UPDATE
  on campin.campsites
  FOR EACH ROW
  execute procedure update_last_modified();

create trigger parks_last_modified
  BEFORE UPDATE
  on campin.parks
  FOR EACH ROW
  execute procedure update_last_modified();


create trigger reservations_last_modified
  BEFORE UPDATE
  on campin.reservations
  FOR EACH ROW
  execute procedure update_last_modified();


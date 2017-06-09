import asyncio
import json
import logging
import re
from datetime import timedelta

from aiopyramid.helpers import use_executor
from pyramid.view import view_config

from campin.api.forms import SearchSchema

log = logging.getLogger(__name__)


def includeme(config):
    config.add_route('campsites free', '/parks/{park_name}/campsites/free')
    config.add_route('parks free', '/parks/free')


# Query for finding campsites that are free.
# Note that asyncpg requires the $1 syntax for parameters.
_search_query = """
    SELECT
      parent_park_name as "parentParkName",
      park_name as "parkName",
      campground_name as "campgroundName",
      site_number as "siteNumber",
      details,
      ci.images
    FROM campin.campsites c
    LEFT OUTER JOIN (
      SELECT campsite_id, array_agg($4 || image_name) as images
      FROM campin.campsite_images
      GROUP BY 1
    ) as ci USING (campsite_id)
    WHERE
      c.campsite_id not in (
        SELECT campsite_id
        FROM campin.reservations r 
        WHERE r.reserve_date BETWEEN $1 and $2
      )
    AND park_name = $3 
    ORDER BY 
      park_name, 
      LPAD(site_number, 3, '0')
"""

# Query for finding parks that have campsites that are free.
_park_search_query = """
  SELECT DISTINCT
      c.park_id as "parkId",
      c.parent_park_name as "parentParkName",
      c.park_name as "parkName",
      c.url as "parkUrl",
      round(
        cast(extract(epoch from dh.drive_hours) / 3600 as numeric),
        1
      ) as "driveHours",
      count(c.campsite_id) as "freeSites"
    FROM campin.campsites c
      INNER JOIN campin.parks p USING(park_id)
      LEFT OUTER JOIN (
        SELECT 
          park_id,
          origin,
          drive_hours
        FROM campin.park_drive_hours
        WHERE origin = $3
      ) as dh
      ON p.park_id = dh.park_id
    WHERE
      c.campsite_id not in (
        SELECT campsite_id
        FROM campin.reservations r 
        WHERE r.reserve_date BETWEEN $1 and $2
      )
    AND (
      dh.drive_hours <= coalesce($4, dh.drive_hours)
      OR dh.drive_hours is NULL
    )     
    GROUP BY 1, 2, 3, 4, 5 
    ORDER BY 
      c.park_name
"""


@view_config(route_name='campsites free', request_method='GET', renderer='json')
async def free_campsites(request):
    """
    Return campites that have reservations available for the entire 
    duration between start_date and end_date parameters.
    
    Required parameters:
    
    * start_date --- Date arriving at campground. In format YYYY-MM-DD.
    * end_date --- Date leaving campground. In format YYYY-MM-DD.
    """
    # TODO: convert Invalid exception to a standard error JSON return value
    results = SearchSchema().to_python(request.params)

    park_name = request.matchdict['park_name']
    start_date = results['start_date']
    end_date = results['end_date'] - timedelta(days=1)

    db = await request.db()
    results = await db.fetch(
        _search_query,
        start_date,
        end_date,
        park_name,
        request.registry.settings['image_base_url']
    )

    sites = []
    for record in results:
        record = dict(record.items())
        # If psycopg (or aiopg) is used it should handle the JSONB columns without
        # needing this manual cast.
        # Asyncpg isn't so helpful.
        if record['details']:
            record['details'] = json.loads(record['details'])
        sites.append(record)

    return {
        'data': sites
    }


@view_config(route_name='parks free', request_method='GET', renderer='json')
async def free_parks(request):
    """
    Return parks that have reservations available for the entire 
    duration between start_date and end_date parameters.
    
    Required parameters:
    
    * start_date --- Date arriving at campground. In format YYYY-MM-DD.
    * end_date --- Date leaving campground. In format YYYY-MM-DD.   
    """
    results = SearchSchema().to_python(request.params)

    start_date = results['start_date']
    end_date = results['end_date'] - timedelta(days=1)
    # Convert "0" drive hours to None for db query
    drive_hours = results['drive_hours'] or None
    if drive_hours:
        log.debug('Max drive time: {} hours'.format(drive_hours))
        drive_hours = timedelta(hours=drive_hours)
    from_place = results['from_place']

    db = await request.db()
    results = await db.fetch(
        _park_search_query,
        start_date,
        end_date,
        from_place,
        drive_hours
    )

    parks = []
    find_times = []
    for record in results:
        record = dict(record.items())
        if record['driveHours']:
            # Convert decimal type to float for serialization
            record['driveHours'] = float(record['driveHours'])
        else:
            if from_place:
                find_times.append(find_and_save(
                    request,
                    from_place,
                    record,
                ))
                # Will be appended to parks when processing results
                # of find_times.
                continue

        parks.append(record)

    add_parks = await asyncio.gather(*find_times)
    parks.extend(
        filter(
            lambda el: el is not None and
                       drive_hours and
                       el['driveHours'] and
                       el['driveHours'] <= drive_hours.total_seconds() / 3600.0,
            add_parks
        )
    )
    parks.sort(key=lambda el: el['parkName'])

    # Cannot be gathered because they run on a single db connection.
    for add_park in add_parks:
        if add_park['driveHours']:
            await save_drive_time(
                db,
                from_place,
                add_park['parkId'],
                timedelta(hours=add_park['driveHours'])
            )

    return {
        'data': parks
    }


async def find_and_save(request, origin, record):
    """
    Set the drive time on the park record.
    
    :param request: Pyramid request.
    :param origin: Origin city to calculate drive time from.
    :param record: Database record with parkName key set. This is the destination 
        that will be used when calculating drive time.
    :return: record with driveHours key set to the number of hours to drive from
        origin to record['parkName']. If the drive time cannot be determined it will
        be set to None.
    """
    park_name = record['parkName']

    park_drive_hours = await find_drive_time(
        request,
        origin,
        park_name
    )
    if park_drive_hours:
        record['driveHours'] = round(park_drive_hours.total_seconds() / 3600.0, 1)
    else:
        record['driveHours'] = None
    return record


@use_executor
def find_drive_time(request, origin, park_name):
    """
    Return the drive time in hours from origin to the provincial park. 
    
    :param request: Pyramid request.
    :param origin: Origin city to calculate drive time from.
    :param park_name: This is the destination that will be used when calculating drive 
        time.
    :return: Drive time in hours. Returns None if drive time could not be determined.
    """
    gmaps = request.gmaps()
    distance = gmaps.distance_matrix(
        units='metric',
        origins=origin,
        destinations='{} Provincial Park, Ontario, Canada'.format(park_name)
    )

    try:
        distance = (distance['rows'][0]['elements'][0]['duration']['text'])
    except (IndexError, KeyError):
        log.info(
            'Could not find distance from {}. Park: {}'.format(
                origin, park_name
            )
        )
        distance = None
    else:
        match = re.match(
            r'(?:(?P<hours>\d+) hours? )?(?:(?P<minutes>\d+) mins?)?',
            distance
        )
        if match:
            distance = timedelta(
                hours=int(match.group('hours')) if match.group('hours') else 0,
                minutes=int(match.group('minutes') if match.group('minutes') else 0)
            )
        else:
            log.debug(
                'Could not match regex for interval. Distance string: "{}"'.format(
                    distance
                )
            )
            distance = None
    return distance


async def save_drive_time(db, origin, park_id, drive_hours):
    """Save the drive time from origin to the provincial park in the database."""
    await db.execute("""
        INSERT INTO campin.park_drive_hours(park_id, origin, drive_hours)
        VALUES($1, $2, $3)
    """, park_id, origin, drive_hours)


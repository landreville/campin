"""Pipeline for storing park information."""
import logging

import googlemaps
from psycopg2._json import Json
from psycopg2.extensions import register_adapter
from txpostgres import txpostgres

register_adapter(dict, Json)
log = logging.getLogger(__name__)


class ParkPipeline(object):
    """
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )
    """

    def open_spider(self, spider):
        # Assigning instance attribute here because this method is called
        # when the spider opens and will always called before process_item.
        self._gmaps = googlemaps.Client(spider.gmaps_apikey)
        self._conn = txpostgres.Connection()
        self._db = self._conn.connect(**spider.db_settings)

    def process_item(self, item, spider):
        log.debug('Processing item: {}'.format(item['park_name']))
        d = self._update_park(item)

        return d

    def _update_park(self, item):
        d = self._exists(item)
        d.addCallback(self._update_distance)
        d.addCallback(self._update_or_insert)
        return d

    def _exists(self, item):
        log.debug('Checking if park exists. {}'.format(item['park_name']))
        d = self._conn.runQuery(
            """
            SELECT count(park_name)
            FROM campin.parks
            WHERE park_name = %(park_name)s
        """, {'park_name': item['park_name']}
        )

        d.addCallback(lambda results: results[0][0] > 0)
        d.addCallback(lambda results: (results, item))
        return d

    def _update_or_insert(self, exists_item):
        exists, item = exists_item
        if exists:
            log.debug('Updating existing park. {}'.format(item['park_name']))
            query = """
                UPDATE campin.parks
                SET activities = %(activities)s,
                    facilities = %(facilities)s,
                    usages = %(usages)s,
                    operating_date_from = %(operating_date_from)s,
                    operating_date_to = %(operating_date_to)s,
                  WHERE park_name = %(park_name)s
            """
        else:
            log.debug('Inserting new park. {}'.format(item['park_name']))
            query = """
                INSERT INTO campin.parks(
                    park_name,
                    activities,
                    facilities,
                    travel_times,
                    usages,
                    operating_date_from,
                    operating_date_to,
                    parent_park_id
                )VALUES(
                    %(park_name)s,
                    %(activities)s,
                    %(facilities)s,
                    %(travel_times)s,
                    %(usages)s,
                    %(operating_date_from)s,
                    %(operating_date_to)s,
                    %(parent_park_id)s
                )
            """
        d = None
        if item.get('parent_park_name'):
            d = self._park_id(item['parent_park_name'])

            def set_park_id(park_id):
                item['parent_park_id'] = park_id
                return item

            d.addCallback(set_park_id)

        if d:
            d.addCallback(
                lambda item: self._conn.runOperation(query, dict(item))
            )
        else:
            d = self._conn.runOperation(query, dict(item))
        d.addCallback(lambda _: item)
        d.addErrback(log.error)
        return d

    def _park_id(self, park_name):
        d = self._conn.runQuery(
            'SELECT park_id FROM campin.parks WHERE park_name = %(park_name)s',
            {'park_name': park_name}
        )

        def parse_park_id(results):
            if results:
                return results[0][0]
            else:
                return None

        d.addCallback(parse_park_id)
        return d

    def _update_distance(self, exists_item):
        exists, item = exists_item
        if not exists:
            log.debug(
                'Finding distance to Toronto. {}'.format(item['park_name'])
            )
            item['travel_times'] = {
                'Toronto': self._park_distance(item['park_name'])
            }
        return exists, item

    def _park_distance(self, park_name):
        distance = self._gmaps.distance_matrix(
            units='metric',
            origins='Toronto, Ontario',
            destinations='{} Provincial Park, Ontario, Canada'.
            format(park_name)
        )

        try:
            distance = (distance['rows'][0]['elements'][0]['duration']['text'])
        except (IndexError, KeyError):
            log.warning(
                'Could not find distance from Toronto. Park: {}'.
                format(park_name)
            )
            distance = None

        return distance

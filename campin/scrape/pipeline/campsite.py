"""Pipeline for storing campsite information."""
import logging

from psycopg2.extensions import register_adapter
from psycopg2.extras import Json
from txpostgres import txpostgres

from campin.scrape.pipeline.persistence import CampSitePersistor

log = logging.getLogger(__name__)
register_adapter(dict, Json)


class CampSitePipeline(object):

    def open_spider(self, spider):
        # Assigning instance attributes here because this method is called
        # when the spider opens and will always called before process_item.
        self._conn = txpostgres.Connection()
        self._db = self._conn.connect(
            **spider.db_settings
        )

    def process_item(self, item, spider):
        log.info('{} - {}. Campsite pipeline processing.'.format(
            item['park_name'],
            item['site_number']
        ))
        log.debug('{} - {}. Image urls: {}'.format(
            item['park_name'], item['site_number'], item['image_urls']
        ))
        log.debug('{} - {}. Item: {}'.format(
            item['park_name'], item['site_number'], dict(item)
        ))

        persistor = CampSitePersistor(self._conn, item)
        d = persistor.save()

        def onerror(err):
            log.error(err)
            raise err
        d.addErrback(onerror)

        return d




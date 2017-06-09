"""Pipeline for storing reservation information."""
import logging

from psycopg2._json import Json
from psycopg2.extensions import register_adapter
from txpostgres import txpostgres

from campin.scrape.pipeline.persistence.reservation import ReservationPersistor

log = logging.getLogger(__name__)


class ReservationPipeline(object):

    def open_spider(self, spider):
        # Assigning instance attribute here because this method is called
        # when the spider opens and will always called before process_item.
        register_adapter(dict, Json)
        self._conn = txpostgres.Connection()
        self._db = self._conn.connect(**spider.db_settings)

    def process_item(self, item, spider):
        log.debug('Processing reservation: {}'.format(dict(item)))
        log.info(
            '{} - {}. Processing reservation.'.format(
                item['park_name'], item['site_number']
            )
        )

        persistor = ReservationPersistor(self._conn, item)
        d = persistor.save()

        def onerror(err):
            log.error(err)
            return err

        d.addErrback(onerror)

        return d

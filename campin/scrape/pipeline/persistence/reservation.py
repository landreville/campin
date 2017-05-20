import logging


log = logging.getLogger(__name__)


class ReservationPersistor(object):

    def __init__(self, db_connection, item):
        self._conn = db_connection
        self._reservation = item

    def save(self):
        d = self._get_campsite()

        def campsite_callback(campsite_id):
            if not campsite_id:
                log.info('Campsite not found. Park name: {}. Site number: {}.'.format(
                    self._reservation['park_name'],
                    self._reservation['site_number']
                ))
                return
            log.info('Found campsite. Park name: {}. Site number: {}.'.format(
                    self._reservation['park_name'],
                    self._reservation['site_number']
            ))
            d = self._reservation_exists()
            d.addCallback(self._insert_or_update)
            d.addCallback(lambda _: self._reservation)
            return d

        d.addCallback(campsite_callback)
        return d

    def _get_campsite(self):
        d = self._conn.runQuery(
            """
            SELECT campsite_id
            FROM campin.campsites
            WHERE park_name = %(park_name)s
            AND site_number = %(site_number)s
        """, {'park_name': self._reservation['park_name'],
              'site_number': self._reservation['site_number']}
        )

        def add_campsite_id(results):
            campsite_id = results[0][0] if results else None
            self._reservation['campsite_id'] = campsite_id
            return campsite_id

        d.addCallback(add_campsite_id)
        return d

    def _reservation_exists(self):
        d_reservation_id = self._conn.runQuery(
            """
            SELECT reservation_id
            FROM reservations
            WHERE campsite_id = %(campsite_id)s
            AND reserve_date = %(reserve_date)s
        """, {
                'campsite_id': self._reservation['campsite_id'],
                'reserve_date': self._reservation['reserve_date']
            }
        )
        d_reservation_id.addCallback(
            lambda results: results[0][0] if results else None
        )
        return d_reservation_id

    def _insert_or_update(self, reservation_id):
        if reservation_id:
            sql = self._update_reservation_sql()
        else:
            sql = self._insert_reservation_sql()

        if not sql:
            # If site is available there will be no row to insert
            return

        params = dict(self._reservation)
        params['campsite_id'] = self._reservation['campsite_id']
        params['reservation_id'] = reservation_id
        d_update = self._conn.runOperation(sql, params)
        return d_update

    def _update_reservation_sql(self):
        if self._reservation['reason'] == 'Available':
            log.debug((
                          'Removing reservation that is now available. ' +
                          'Park name: {park_name}. ' +
                          'Site number: {site_number}'
                      ).format(**dict(self._reservation)))
            query = """
                    DELETE FROM campin.reservations
                    WHERE reservation_id = %(reservation_id)s
                """
        else:
            log.debug((
                          'Updating existing reservation. ' +
                          'Park name: {park_name}. ' +
                          'Site number: {site_number}. ' +
                          'Status: {reason}'
                      ).format(**dict(self._reservation)))
            query = """
                    UPDATE campin.reservations
                    SET reason = %(reason)s 
                    WHERE reservation_id = %(reservation_id)s
                """
        return query

    def _insert_reservation_sql(self):
        if self._reservation['reason'] == 'Available':
            log.debug((
                          'Not inserting reservation for available date. ' +
                          'Park name: {park_name}. ' +
                          'Site number: {site_number}. ' +
                          'Status: {reason}'
                      ).format(**dict(self._reservation)))
            return

        log.debug((
                      'Inserting new reservation. ' +
                      'Park name: {park_name}. ' +
                      'Site number: {site_number}. ' + 'Status: {reason}'
                  ).format(**dict(self._reservation)))
        query = """
            INSERT INTO campin.reservations(
              campsite_id,
              reserve_date,
              reason
            )VALUES(
              %(campsite_id)s,
              %(reserve_date)s,
              %(reason)s
            )
        """
        return query

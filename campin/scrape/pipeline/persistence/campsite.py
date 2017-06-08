import logging
import os

from twisted.internet.defer import DeferredList

log = logging.getLogger(__name__)


class CampSitePersistor(object):

    def __init__(self, db_connection, item):
        self._conn = db_connection
        self._campsite = item

    def save(self):
        self._campsite['images'] = {
            i['path'] for i in self._campsite['images']
        }
        d = self._set_park_id()
        d.addCallback(lambda _: self._set_campsite_id())
        d.addCallback(lambda _: self._add_or_update())
        d.addCallback(lambda _: self._save_images())
        # Callbacks above populate self._campsite, so return it at the end of the chain
        d.addCallback(lambda _: self._campsite)
        return d

    def _add_or_update(self):
        """
        Add or update the campsite depending on if campsite_id is set on the item.
        """
        if not self._campsite['campsite_id']:
            d = self._add_campsite()
        elif self._campsite['campsite_id']:
            d = self._update_campsite()
        return d

    def _set_park_id(self):
        """
        Set the park id based on the park name in the item. 
        """
        park_name = self._campsite['park_name']
        d = self._conn.runQuery(
            """
            SELECT park_id
            FROM campin.parks
            WHERE park_name = %(park_name)s
        """, {'park_name': park_name}
        )

        def parse_results(results):
            if results:
                self._campsite['park_id'] = results[0][0]
            else:
                dinsert = self._conn.runQuery("""
                    INSERT INTO campin.parks(park_name)
                    VALUES(%(park_name)s)
                    RETURNING park_id
                """)

                def set_campsite(insert_results):
                    self._campsite['park_id'] = insert_results[0][0]
                dinsert.addCallback(set_campsite)
                return dinsert

        d.addCallback(parse_results)

        return d

    def _set_campsite_id(self):
        """
        Set the campsite ID if this is an existing campsite based on the
        park name and site number.
        """
        site_number = self._campsite['site_number']
        park_name = self._campsite['park_name']

        d = self._conn.runQuery(
            """
            SELECT campsite_id
            FROM campin.campsites
            WHERE park_name = %(park_name)s
            AND site_number = %(site_number)s
        """, {'park_name': park_name,
              'site_number': site_number}
        )

        def add_campsite_id(results):
            self._campsite['campsite_id'] = results[0][0] if results else None

        d.addCallback(add_campsite_id)
        return d

    def _update_campsite(self):
        """
        Update the campsite details. 
         
        Don't perform an update if there are no details set on the item.
        """

        if not self._campsite['details']:
            log.debug('Not updating campsite, because no details set.')
            return

        log.debug(
            '{} - {}. Updating campsite.'.format(
                self._campsite['park_name'],
                self._campsite['site_number']
            )
        )

        query = """
            UPDATE campin.campsites
            SET details = %(details)s
            WHERE campsite_id = %(campsite_id)s
        """

        d = self._conn.runOperation(query, dict(self._campsite))
        return d

    def _save_images(self):
        """
        Add campsite images if they don't already exist. 
        """
        campsite_id = self._campsite['campsite_id']
        image_names = {
            os.path.basename(image_path)
            for image_path in self._campsite['images']
        }

        log.debug('{} - {}. Saving images in DB: {}'.format(
            self._campsite['park_name'],
            self._campsite['site_number'],
            image_names
        ))

        query = """
            SELECT COUNT(campsite_image_id)
            FROM campin.campsite_images
            WHERE campsite_id = %(campsite_id)s
            AND image_name = %(image_name)s
        """

        insert = """
            INSERT INTO campin.campsite_images(campsite_id, image_name)
            VALUES(%(campsite_id)s, %(image_name)s)
            RETURNING campsite_image_id
        """

        def insert_on_not_exists(results, image_name):
            if not results[0][0]:
                log.debug(
                    '{} - {}. Inserting campsite image: {}'.format(
                        self._campsite['park_name'],
                        self._campsite['site_number'],
                        image_name
                    )
                )
                d = self._conn.runOperation(
                    insert,
                    {'campsite_id': campsite_id, 'image_name': image_name}
                )

                return d
            else:
                log.debug(
                    '{} - {}. Found existing image record: {}'.format(
                        self._campsite['park_name'],
                        self._campsite['site_number'],
                        image_name
                    )
                )

        dl = []
        for image_name in image_names:
            d = self._conn.runQuery(
                query,
                {'campsite_id': campsite_id, 'image_name': image_name}
            )
            d.addCallback(insert_on_not_exists, image_name)
            dl.append(d)

        dl = DeferredList(dl)
        return dl

    def _add_campsite(self):
        """
         
        """
        log.debug(
            ' {} - {}. Inserting new campsite.'.
            format(self._campsite['park_name'], self._campsite['site_number'])
        )
        query = """
            INSERT into campin.campsites(
                park_id,
                park_name,
                site_number,
                site_type,
                campground_name,
                parent_park_name,
                details,
                images
            )VALUES(
              %(park_id)s,
              %(park_name)s,
              %(site_number)s,
              %(site_type)s,
              %(campground_name)s,
              %(parent_park_name)s,
              %(details)s,
              %(images)s
            ) RETURNING campsite_id
        """
        d = self._conn.runQuery(query, dict(self._campsite))

        def add_campsite_id(results):
            self._campsite['campsite_id'] = results[0][0]

        d.addCallback(add_campsite_id)
        return d

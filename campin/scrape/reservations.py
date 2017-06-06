"""Spider for Ontario Parks reservations."""
import logging
from datetime import datetime, timedelta

import scrapy

from campin.scrape.items import ReservationItem
from campin.scrape.util import text

log = logging.getLogger(__name__)

_status_map = {'Reserve!': 'Available'}


class ReservationSpider(scrapy.Spider):

    name = 'ontarioparks'
    start_urls = ['https://reservations.ontarioparks.com/Algonquin-Achray?List']
    park_post_url = 'https://reservations.OntarioParks.com/Viewer.aspx'

    def __init__(self, db_settings):
        super().__init__()
        self.db_settings = db_settings
        current_year = datetime.now().year
        # Only the summer months
        start_date = max(
            datetime(current_year, 6, 19),
            datetime.now()
        )
        end_date = datetime(current_year, 10, 31)
        date_diff = end_date - start_date
        days = int(date_diff.total_seconds() / 86400)
        log.debug(
            'Starting at: {}. Days: {}'.format(start_date.isoformat(), days)
        )
        # Generate a datetime for every day
        self._dates = (
            start_date + timedelta(days=i) for i in range(0, days + 1)
        )

    def parse(self, response):
        """
        Initiate a request for each park.
        """
        for reserve_date in self._dates:
            nights = '1'
            # Form requires both a date that is the first of the month
            # and the date you are looking for a reservation
            month_str = reserve_date.strftime(
                '%a %b 01 %Y 00:00:00 GMT-0400 (EDT)'
            )
            date_str = reserve_date.strftime(
                '%a %b %d %Y 00:00:00 GMT-0400 (EDT)'
            )
            self.logger.debug('Date: {}'.format(date_str))

            # Each park in the reserve form
            for park_option in response.css(
                    'select[name="ctl00$MainContentPlaceHolder$LocationList"] option'
            ):
                park_name = park_option.xpath('text()').extract()[0]
                park_id = park_option.xpath('@value').extract()[0]

                if park_name == 'Ontario Parks':
                    continue

                form_params = {
                    'ctl00$MainContentPlaceHolder$LocationList': park_id,
                    'selArrMth': month_str,
                    'selArrDay': date_str,
                    'txtArrDateHidden': reserve_date.strftime('%Y-%m-%d'),
                    'selNumNights': nights,
                    'selEquipmentSub': 'Single Tent/Shelter',
                    'selPartySize': '1'
                }

                # Form requires some cookies to be set before submitting
                cookies = {
                    'ArrivalDate': reserve_date.strftime('%Y-%m-%d'),
                    'NumberOfNights': nights
                }

                request = scrapy.FormRequest.from_response(
                    response,
                    formname='MainForm',
                    formdata=form_params,
                    dont_click=True,
                    callback=self._park_callback,
                    cookies=cookies,
                    meta={'reserve_date': reserve_date}
                )
                request.meta['reserve_date'] = reserve_date
                yield request

    def _park_callback(self, response):
        """
        Generate :class:`CampSiteItem` and :class:`ReservationItem` for the park
        that we are scraping
        """
        parent_name, park_name, campground_name = self._park_names_selected(
            response
        )
        reserve_date = response.meta['reserve_date']

        log.debug('On page for park. date: {}. park: {}'.format(reserve_date, park_name))

        if response.css('#viewAvailabilityMsg'):
            # A campground area must be chosen with a new request
            area_table = response.css('.list_new')
            for anchor in area_table.css('a::attr("href")'):
                url = response.urljoin(anchor.extract())

                request = scrapy.Request(url, callback=self._park_callback)
                request.meta['reserve_date'] = reserve_date
                yield request
            # Nothing else to do in this function, because it's not a real park page
            # parks will be parsed with requests in the above loop
            return

        site_table = response.css('.list_new')
        for row in site_table.css('tbody tr'):
            cells = list(row.css('td'))
            if not cells:
                # header row
                continue

            site_number = cells[1].css('a::text').extract()[0].split()[0].strip()

            # Status of campsite reservation for the date
            site_status = cells[3].css('a::text')
            if not site_status:
                site_status = cells[3].xpath('text()')
            site_status = site_status.extract()[0]

            res = ReservationItem()
            res['reason'] = _status_map.get(site_status, site_status)
            res['reserve_date'] = reserve_date
            res['park_name'] = park_name
            res['site_number'] = site_number

            yield res

    def _park_names_selected(self, response):
        """
        Find the park name, campground name, and parent park name from
        the form selection.
        """
        parent_park_name = None
        park_name = text(
            response.css(
                'select[name="ctl00$MainContentPlaceHolder$LocationList"] > option[selected]'
            )
        )

        if ' - ' in park_name:
            parent_park_name, park_name = park_name.split(' - ')

        campground_name = text(
            response.css(
                'select[name="ctl00$MainContentPlaceHolder$MapList"] > option[selected]'
            )
        )

        if campground_name == 'All Campgrounds':
            campground_name = None

        log.debug(
            'Park Name: {}. Campground: {}. Parent park: {}'.
            format(park_name, campground_name, parent_park_name)
        )

        return parent_park_name, park_name, campground_name

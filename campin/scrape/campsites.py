"""Spider for campsite information."""
import logging
from datetime import datetime
from urllib.parse import urlencode
import re

import scrapy

from campin.scrape.items import CampSiteItem
from campin.scrape.util import text

log = logging.getLogger(__name__)

_status_map = {'Reserve!': 'Available'}


class CampSiteSpider(scrapy.Spider):

    name = 'ontarioparks'
    start_urls = ['https://reservations.ontarioparks.com/Algonquin-Achray?List']
    park_post_url = 'https://reservations.OntarioParks.com/Viewer.aspx'

    def __init__(self, db_settings):
        super().__init__()
        # db_settings will be used by Pipeline.
        self.db_settings = db_settings
        current_year = datetime.now().year
        # Date to use when getting campsite information. This is necessary
        # to search for campsites, because it's really a search for reservations.
        self._check_date = datetime(current_year, 6, 1)

    def parse(self, response):
        """
        Initiate a request for each park.
        """
        nights = '1'
        # Form requires both a date that is the first of the month
        # and the date you are looking for a reservation
        month_str = self._check_date.strftime(
            '%a %b 01 %Y 00:00:00 GMT-0400 (EDT)'
        )
        date_str = self._check_date.strftime(
            '%a %b %m %Y 00:00:00 GMT-0400 (EDT)'
        )

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
                'txtArrDateHidden': self._check_date.strftime('%Y-%m-%d'),
                'selNumNights': nights,
                'selEquipmentSub': 'Single Tent/Shelter',
                'selPartySize': '1'
            }

            # Form requires some cookies to be set before submitting
            cookies = {
                'ArrivalDate': self._check_date.strftime('%Y-%m-%d'),
                'NumberOfNights': nights
            }

            request = scrapy.FormRequest.from_response(
                response,
                formname='MainForm',
                formdata=form_params,
                dont_click=True,
                callback=self._park_callback,
                cookies=cookies,
                meta={'reserve_date': self._check_date}
            )
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

        log.debug('On page for park: {}'.format(park_name))

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
            # Table cell containing link to campsite details
            site_cell = cells[1]

            site = CampSiteItem()
            site['parent_park_name'] = parent_name
            site['park_name'] = park_name
            site['campground_name'] = campground_name
            site['site_number'] = (
                cells[1].css('a::text').extract()[0].split()[0].strip()
            )
            site['site_type'] = cells[2].xpath('text()').extract()[0]
            site['details'] = {}
            site['images'] = []
            site['image_urls'] = []

            pop_details = PopulateCampsiteDetails(site)
            yield from pop_details.populate(site_cell)

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


class PopulateCampsiteDetails(object):
    """Populate details in the campsite item."""

    def __init__(self, campsite):
        # self._campsite will be have details set as callbacks are called
        self._campsite = campsite

    def populate(self, site_cell):
        """
        Return a request that will populate the campsite details on callback.
        """
        log.debug('Populating site details. {} - {}'.format(
            self._campsite['park_name'],
            self._campsite['site_number']
        ))
        jscall_re = re.compile(
            r"javascript:SelectRce\('([^']+)','([^']+)','([^']+)'\);"
        )

        for anchor in site_cell.css('a::attr("href")'):
            # The javascript in the href contains the call to navigate to the
            # details page.
            jscall = anchor.extract()
            # log.debug('JS Call: {}'.format(jscall))
            match = jscall_re.match(jscall)
            if not match:
                log.warning('Could not find JS call for campsite details.')
                return []

            # Arguments of the SelectRce Javascript function that displays
            # campsite details.
            loc_id = match.group(1) # named "n" in SelectRce
            rce_id = match.group(3) # named "r" in SelectRce

            def request_photos(response):
                self._set_details(response)
                pictures_url = 'https://reservations.ontarioparks.com/Pictures.aspx'
                pictures_params = {'locId': loc_id, 'rceId': rce_id}
                yield scrapy.Request(
                    pictures_url + '?' + urlencode(pictures_params),
                    callback=self._set_photos
                )

            yield scrapy.FormRequest(
                'https://reservations.ontarioparks.com/Details.ashx',
                callback=request_photos,
                method='POST',
                formdata={'type': 'Resource',
                          'id': rce_id}
            )

    def _set_details(self, response):
        """
        Set the details on the campsite item. 
        """
        details = {}
        for row in response.css('table.rceDetails tbody tr'):
            label = text(row.css('td.label'))
            value = text(row.css('td.value'))
            details[label] = value

        log.info('Found details: {}'.format(details))
        self._campsite['details'] = details

    def _set_photos(self, response):
        """
        Set the photos on the campsite item and return the item. 
        """
        urls = []
        for img in response.css('img.SiteImage::attr("src")'):
            url = img.extract()
            urls.append(url)
        log.info('Found image urls: {}'.format(urls))
        self._campsite['image_urls'] = urls

        yield self._campsite

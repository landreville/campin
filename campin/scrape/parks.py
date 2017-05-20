"""
Scrape park information from ontarioparks.com and insert into database.

Note that the park names from ontarioparks.com sometimes do not match
the park names from reservations.ontarioparks.com. These results in campsite
information not being associated with the park found by this scraper.
"""
import logging

import scrapy
from dateutil.parser import parse

from .items import ParkItem
from .util import text, full_link, extract

log = logging.getLogger(__name__)

_status_map = {'Reserve!': 'Available',}


class OntarioParksSpider(scrapy.Spider):
    name = 'ontarioparks'
    start_urls = ['http://www.ontarioparks.com/en']

    def __init__(self, db_settings, gmaps_apikey):
        super().__init__()
        self.db_settings = db_settings
        self.gmaps_apikey = gmaps_apikey

    def parse(self, response):
        """
        Parse main page
        """
        park_sel = '#parksnavbar > ul > li:first-child ul > li > a'
        for park_link in response.css(park_sel):
            name = park_link.xpath('text()').extract()[0]
            link = ''.join(park_link.xpath('@href').extract())

            self.log('Park: {}. Link: {}'.format(name, link))

            yield scrapy.Request(
                full_link(response, link), callback=self._parse_park
            )

    def _parse_park(self, response):
        """
        Parse information for a park
        """

        park_name = ''.join(
            response.css('.park-heading').xpath('text()').extract()
        )

        self.log('Park name: {}'.format(park_name))

        activities_url = response.url + '/activities'
        facilities_url = response.url + '/facilities'
        maps_url = response.url + '/maps'
        park_url = response.url

        park = ParkItem()
        park['park_name'] = park_name
        park['parent_park_id'] = None
        park['usages'] = []
        park['operating_date_from'] = park['operating_date_to'] = None
        request = scrapy.Request(
            activities_url, callback=self._parse_activities
        )
        request.meta['park'] = park
        request.meta['facilities_url'] = facilities_url
        request.meta['maps_url'] = maps_url
        request.meta['park_url'] = park_url

        yield request

    def _parse_activities(self, response):
        """
        Parse activities for a park.
        """
        park = _parse_description_list(response, 'activities')
        request = scrapy.Request(
            response.meta['facilities_url'], callback=self._parse_facilities
        )
        request.meta.update(response.meta)
        request.meta['park'] = park
        yield request

    def _parse_facilities(self, response):
        """
        Parse facilities for a park.
        """
        park = _parse_description_list(response, 'facilities')

        request = scrapy.Request(
            response.meta['maps_url'], callback=self._parse_park_maps
        )
        request.meta.update(response.meta)
        request.meta['park'] = park
        yield request

    def _parse_park_maps(self, response):
        """
        Parse park map.
        """
        park = response.meta['park']
        el = response.xpath("//a[contains(., 'Park Overview')]")
        if el:
            self.log('Found park map.')
            file_url = el.xpath('@href').extract()

        # TODO: Download map and store somewhere

        request = scrapy.Request(
            response.meta['park_url'],
            callback=self._parse_subparks,
            dont_filter=True
        )
        request.meta.update(response.meta)
        request.meta['park'] = park
        yield request

    def _parse_subparks(self, response):
        park = response.meta['park']
        subparks = []

        for row in response.css(
                'div.panel-operating-dates tr:not(tr:first-child)'
        ):
            cells = row.css('td')
            subpark_name = text(cells[0])
            if ' - ' in subpark_name:
                subpark_name = subpark_name.split(' - ')[-1]

            icons = cells[1]
            usages = []
            if icons.css('span.campin-icon'):
                usages.append('Camping')
            if icons.css('span.interior-icon'):
                usages.append('Backcountry')
            if icons.css('span.day-use-icon'):
                usages.append('Day-use')

            dates = cells[2]
            try:
                from_date, to_date = text(dates).split(' to ')
                from_date = parse(from_date)
                to_date = parse(to_date)
            except ValueError:
                from_date = to_date = None

            if subpark_name == park['park_name']:
                if park.get('usages'):
                    park['usages'].extend(usages)
                else:
                    park['usages'] = usages
                park['operating_date_from'] = from_date
                park['operating_date_to'] = to_date
            else:
                subpark = ParkItem()
                subpark.update(dict(park))
                subpark['park_name'] = subpark_name
                subpark['usages'] = usages
                subpark['operating_date_from'] = from_date
                subpark['operating_date_to'] = to_date
                subpark['parent_park_name'] = park['park_name']
                subparks.append(subpark)

        yield park

        # Done at the end so the parent park is yielded first
        for subpark in subparks:
            yield subpark


def _parse_description_list(response, title):
    selector = '#{} *'.format(title)

    descriptions = {}
    name = None
    desc = None
    for child in response.css(selector):
        if extract(child, 'name()') == 'h2':
            name = text(child)
            continue

        if extract(child, 'name()') == 'p':
            desc = text(child)
            descriptions[name] = desc

    park = response.meta['park']
    park.update({title: descriptions})
    return park

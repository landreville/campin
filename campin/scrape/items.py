import scrapy


class ParkItem(scrapy.Item):
    park_name = scrapy.Field()
    activities = scrapy.Field()
    facilities = scrapy.Field()
    travel_times = scrapy.Field()
    usages = scrapy.Field()
    operating_date_from = scrapy.Field()
    operating_date_to = scrapy.Field()
    parent_park_name = scrapy.Field()
    parent_park_id = scrapy.Field()


class CampSiteItem(scrapy.Item):
    campsite_id = scrapy.Field()
    park_id = scrapy.Field()
    park_name = scrapy.Field()
    parent_park_name = scrapy.Field()
    campground_name = scrapy.Field()
    site_number = scrapy.Field()
    site_type = scrapy.Field()
    site_status = scrapy.Field()
    fee_type = scrapy.Field()
    restrictions = scrapy.Field()
    service_type = scrapy.Field()
    site_shade = scrapy.Field()
    quality = scrapy.Field()
    privacy = scrapy.Field()
    conditions = scrapy.Field()
    ground_cover = scrapy.Field()
    adjacent_to = scrapy.Field()
    allowed_equipment = scrapy.Field()
    on_site_parking = scrapy.Field()
    off_site_parking = scrapy.Field()
    reservable_online = scrapy.Field()
    details = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()


class ReservationItem(scrapy.Item):
    campsite_id = scrapy.Field()
    site_number = scrapy.Field()
    park_name = scrapy.Field()
    reserve_date = scrapy.Field()
    reason = scrapy.Field()


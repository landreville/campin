import argparse
import configparser
import logging
import os

from scrapy.crawler import CrawlerProcess

from campin.scrape.campsites import CampSiteSpider
from campin.scrape.parks import OntarioParksSpider
from campin.scrape.reservations import ReservationSpider

log = logging.getLogger(__name__)


def scrape_parks():
    settings = {
        "USER_AGENT":
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
        'DOWNLOAD_DELAY':
            0.1,
        'CLOSESPIDER_ERRORCOUNT':
            1,
        'ITEM_PIPELINES': {
            'campin.scrape.pipeline.ParkPipeline': 100,
        }
    }
    config = _config_file_settings()
    db_settings = _parse_db_settings(config)
    crawler = CrawlerProcess(settings)
    crawler.crawl(OntarioParksSpider, db_settings, config['gmaps.apikey'])
    crawler.start()


def scrape_reservations():
    settings = {
        "USER_AGENT":
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
        'DOWNLOAD_DELAY':
            0.5,
        'CLOSESPIDER_ERRORCOUNT':
            1,
        'ITEM_PIPELINES': {
            'campin.scrape.pipeline.ReservationPipeline': 100,
        },
    }
    config = _config_file_settings()
    db_settings = _parse_db_settings(config)
    crawler = CrawlerProcess(settings)
    crawler.crawl(ReservationSpider, db_settings)
    crawler.start()


def scrape_sites():
    settings = {
        "USER_AGENT":
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
        'DOWNLOAD_DELAY':
            0.5,
        'CLOSESPIDER_ERRORCOUNT':
            1,
        'ITEM_PIPELINES': {
            'scrapy.pipelines.images.ImagesPipeline': 1,
            'campin.scrape.pipeline.CampSitePipeline': 100,
        },
        'IMAGES_STORE': '/home/jason/workspace/campin/images'
    }

    config = _config_file_settings()
    db_settings = _parse_db_settings(config)

    crawler = CrawlerProcess(settings)
    crawler.crawl(CampSiteSpider, db_settings)
    crawler.start()


def _config_file_settings():
    parser = argparse.ArgumentParser(
        description='Scrape Ontario Parks'
    )
    parser.add_argument('config_file', metavar='CONFIG_FILE')
    args = parser.parse_args()
    config_parser = configparser.ConfigParser()
    with open(os.path.abspath(args.config_file), 'r') as f:
        config_parser.read_file(f)
    return dict(config_parser.items('DEFAULT'))


def _parse_db_settings(settings, prefix='db.'):
    return {
        k[len(prefix):]: v
        for k, v in settings.items()
        if k.startswith('db.')
    }

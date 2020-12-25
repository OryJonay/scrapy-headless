from shutil import which
import pytest
import scrapy
from scrapy.crawler import Crawler


class TestSpider(scrapy.Spider):
    name = 'test_spider'
    allowed_domains = ['python.org']
    start_urls = ['http://python.org']

    def parse(self, response):
        pass


@pytest.fixture(params=[('firefox', 'geckodriver', '-headless'),
                        ('chrome', 'chromedriver', '--headless'),
                        ('firefox', 'geckodriver', '-headless, --block-ads')],
                ids=['Mozilla FireFox', 'Google Chrome', 'Mozilla FireFox + AdBlock'])
def crawler(request):
    settings = {
        'SELENIUM_DRIVER_NAME': request.param[0],
        'SELENIUM_DRIVER_EXECUTABLE_PATH': which(request.param[1]),
        'SELENIUM_DRIVER_ARGUMENTS': [arg for arg in request.param[2].split(', ')]
    }
    return Crawler(spidercls=TestSpider, settings=settings)


@pytest.fixture
def invalid_crawler(request):
    settings = {
        'SELENIUM_DRIVER_NAME': 'edge',
        'SELENIUM_DRIVER_EXECUTABLE_PATH': which('edgedriver'),
        'SELENIUM_DRIVER_ARGUMENTS': [],
    }
    return Crawler(spidercls=TestSpider, settings=settings)

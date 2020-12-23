"""This module contains the test cases for the middlewares of the ``scrapy_headless`` package"""
import pytest
from unittest.mock import patch

from scrapy import Request
# from scrapy.crawler import Crawler

from scrapy_headless.http import SeleniumRequest
from scrapy_headless.middlewares import SeleniumMiddleware


def test_process_request_method_should_initialize_the_driver(crawler):
    """Test that the ``process_request`` method should initialize the selenium driver"""
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    selenium_request = SeleniumRequest(url='http://www.python.org')
    html_response = selenium_middleware.process_request(request=selenium_request, spider=None)

    # The driver must be initialized
    assert html_response.meta.get('driver') is not None

    # We can now use the driver
    html_response.meta.get('driver').get('http://www.python.org')
    assert 'Python' in html_response.meta.get('driver').title

    # Close the driver
    html_response.meta.get('driver').close()


def test_process_spider_output_should_close_the_driver(crawler):
    """Test that the ``process_spider_output`` method should close the driver"""
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    selenium_request = SeleniumRequest(url='http://www.python.org')
    html_response = selenium_middleware.process_request(request=selenium_request, spider=None)
    with patch.object(html_response.meta.get('driver'), 'quit') as mocked_quit:
        selenium_middleware.process_spider_output(html_response, [], None)
    mocked_quit.assert_called_once()
    html_response.meta.get('driver').quit()


def test_process_request_should_return_none_if_not_selenium_request(crawler):
    """Test that the ``process_request`` should return none if not selenium request"""
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    scrapy_request = Request(url='http://not-an-url')
    assert selenium_middleware.process_request(request=scrapy_request, spider=None) is None


def test_process_request_should_return_a_response_if_selenium_request(crawler):  # FIX
    """Test that the ``process_request`` should return a response if selenium request"""
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    selenium_request = SeleniumRequest(url='http://www.python.org')
    html_response = selenium_middleware.process_request(request=selenium_request, spider=None)

    # We have access to the driver on the response via the "meta"
    assert html_response.meta.get('driver') is not None

    # We also have access to the "selector" attribute on the response
    assert html_response.selector.xpath('//title/text()').extract_first() == 'Welcome to Python.org'

    html_response.meta.get('driver').quit()


def test_process_request_should_return_a_screenshot_if_screenshot_option(crawler):
    """Test that the ``process_request`` should return a response with a screenshot"""
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    selenium_request = SeleniumRequest(url='http://www.python.org', screenshot=True)
    html_response = selenium_middleware.process_request(request=selenium_request, spider=None)
    assert html_response.meta['screenshot'] is not None
    html_response.meta.get('driver').quit()


def test_process_request_should_execute_script_if_script_option(crawler):
    """Test that the ``process_request`` should execute the script and return a response"""
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    selenium_request = SeleniumRequest(url='http://www.python.org', script='document.title = "scrapy_selenium";')
    html_response = selenium_middleware.process_request(request=selenium_request, spider=None)
    assert html_response.selector.xpath('//title/text()').extract_first() == 'scrapy_selenium'
    html_response.meta.get('driver').quit()


@pytest.mark.flaky(max_runs=3, min_passes=1)
def test_middleware_should_filter_ads(crawler):
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    selenium_request = SeleniumRequest(url='http://www.yahoo.com')
    html_response = selenium_middleware.process_request(request=selenium_request, spider=None)
    ads = html_response.meta['driver'].find_elements_by_xpath('//*[@data-content="Advertisement"]')
    assert ads, 'No ads found'
    if selenium_middleware._block_ads:
        assert all(not ad.is_displayed() for ad in ads), 'Ads not filtered'
    else:
        assert all(ad.is_displayed() for ad in ads)
    html_response.meta.get('driver').quit()

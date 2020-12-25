"""This module contains the test cases for the middleware of the ``scrapy_headless`` package"""
import pytest
from unittest.mock import patch

from scrapy import Request

from scrapy_headless.http import SeleniumRequest, SeleniumResponse
from scrapy_headless.middlewares import SeleniumMiddleware, NotConfigured


def test_process_request_method_should_initialize_the_driver(crawler):
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    selenium_request = SeleniumRequest(url='http://www.python.org')
    selenium_response = selenium_middleware.process_request(request=selenium_request, spider=None)

    assert selenium_response.interact is not None
    selenium_response.interact.get('http://www.python.org')
    assert 'Python' in selenium_response.interact.title

    selenium_response.interact.close()


def test_process_spider_output_should_close_the_driver(crawler):
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    selenium_request = SeleniumRequest(url='http://www.python.org')
    selenium_response = selenium_middleware.process_request(request=selenium_request, spider=None)

    with patch.object(selenium_response.interact, 'quit') as mocked_quit:
        selenium_middleware.process_spider_output(selenium_response, [], None)

    mocked_quit.assert_called_once()

    selenium_response.interact.quit()


def test_process_request_should_return_none_if_not_selenium_request(crawler):
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    scrapy_request = Request(url='http://not-an-url')
    assert selenium_middleware.process_request(request=scrapy_request, spider=None) is None


def test_process_request_should_return_a_response_if_selenium_request(crawler):  # FIX
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    selenium_request = SeleniumRequest(url='http://www.python.org')
    selenium_response = selenium_middleware.process_request(request=selenium_request, spider=None)

    assert isinstance(selenium_response, SeleniumResponse)
    assert selenium_response.interact is not None
    assert selenium_response.selector.xpath('//title/text()').extract_first() == 'Welcome to Python.org'

    selenium_response.interact.quit()


def test_process_request_should_return_a_screenshot_if_screenshot_option(crawler):
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    selenium_request = SeleniumRequest(url='http://www.python.org', screenshot=True)
    selenium_response = selenium_middleware.process_request(request=selenium_request, spider=None)
    assert selenium_response.meta['screenshot'] is not None
    selenium_response.interact.quit()


def test_process_request_should_execute_script_if_script_option(crawler):
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    selenium_request = SeleniumRequest(url='http://www.python.org', script='document.title = "scrapy_selenium";')
    selenium_response = selenium_middleware.process_request(request=selenium_request, spider=None)
    assert selenium_response.selector.xpath('//title/text()').extract_first() == 'scrapy_selenium'
    selenium_response.interact.quit()


@pytest.mark.flaky(max_runs=3, min_passes=1)
def test_middleware_should_filter_ads(crawler):
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    selenium_request = SeleniumRequest(url='http://www.yahoo.com')
    selenium_response = selenium_middleware.process_request(request=selenium_request, spider=None)
    ads = selenium_response.meta['driver'].find_elements_by_xpath('//*[@data-content="Advertisement"]')

    assert ads, 'No ads found'
    if selenium_middleware._block_ads:
        assert all(not ad.is_displayed() for ad in ads), 'Ads not filtered'
    else:
        assert all(ad.is_displayed() for ad in ads)

    selenium_response.interact.quit()


def test_middleware_raises_not_configured_on_invalid_browsers(invalid_crawler):
    with pytest.raises(NotConfigured):
        SeleniumMiddleware.from_crawler(invalid_crawler)


def test_middleware_should_copy_cookies_if_present(crawler):
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    selenium_request = SeleniumRequest(url='http://www.python.org', cookies={'cookies': 'chocolate chips'})
    selenium_response = selenium_middleware.process_request(request=selenium_request, spider=None)

    assert selenium_response.interact.get_cookie('cookies')['value'] == 'chocolate chips'
    selenium_response.interact.quit()

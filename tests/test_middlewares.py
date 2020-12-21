"""This module contains the test cases for the middlewares of the ``scrapy_selenium`` package"""

from unittest.mock import patch

from scrapy import Request
from scrapy.crawler import Crawler

from scrapy_headless.http import SeleniumRequest
from scrapy_headless.middlewares import SeleniumMiddleware

from .test_cases import BaseScrapySeleniumTestCase


class SeleniumMiddlewareTestCase(BaseScrapySeleniumTestCase):
    """Test case for the ``SeleniumMiddleware`` middleware"""

    @classmethod
    def setUpClass(cls):
        """Initialize the middleware"""
        super().setUpClass()
        crawler = Crawler(spidercls=cls.spider_class, settings=cls.settings)
        cls.selenium_middleware = SeleniumMiddleware.from_crawler(crawler)

    def test_process_request_method_should_initialize_the_driver(self):
        """Test that the ``process_request`` method should initialize the selenium driver"""
        selenium_request = SeleniumRequest(url='http://www.python.org')
        html_response = self.selenium_middleware.process_request(request=selenium_request, spider=None)

        # The driver must be initialized
        self.assertIsNotNone(html_response.meta.get('driver'))

        # We can now use the driver
        html_response.meta.get('driver').get('http://www.python.org')
        self.assertIn('Python', html_response.meta.get('driver').title)

        # Close the driver
        html_response.meta.get('driver').close()

    def test_process_spider_output_should_close_the_driver(self):
        """Test that the ``process_spider_output`` method should close the driver"""
        selenium_request = SeleniumRequest(url='http://www.python.org')
        html_response = self.selenium_middleware.process_request(request=selenium_request, spider=None)
        with patch.object(html_response.meta.get('driver'), 'quit') as mocked_quit:
            self.selenium_middleware.process_spider_output(html_response, [], None)
        mocked_quit.assert_called_once()
        html_response.meta.get('driver').quit()

    def test_process_request_should_return_none_if_not_selenium_request(self):
        """Test that the ``process_request`` should return none if not selenium request"""
        scrapy_request = Request(url='http://not-an-url')
        self.assertIsNone(self.selenium_middleware.process_request(request=scrapy_request, spider=None))

    def test_process_request_should_return_a_response_if_selenium_request(self):  # FIX
        """Test that the ``process_request`` should return a response if selenium request"""
        selenium_request = SeleniumRequest(url='http://www.python.org')
        html_response = self.selenium_middleware.process_request(request=selenium_request, spider=None)

        # We have access to the driver on the response via the "meta"
        self.assertIsNotNone(html_response.meta.get('driver'))

        # We also have access to the "selector" attribute on the response
        self.assertEqual(html_response.selector.xpath('//title/text()').extract_first(), 'Welcome to Python.org')

        html_response.meta.get('driver').quit()

    def test_process_request_should_return_a_screenshot_if_screenshot_option(self):
        """Test that the ``process_request`` should return a response with a screenshot"""
        selenium_request = SeleniumRequest(url='http://www.python.org', screenshot=True)
        html_response = self.selenium_middleware.process_request(request=selenium_request, spider=None)
        self.assertIsNotNone(html_response.meta['screenshot'])
        html_response.meta.get('driver').quit()

    def test_process_request_should_execute_script_if_script_option(self):
        """Test that the ``process_request`` should execute the script and return a response"""
        selenium_request = SeleniumRequest(url='http://www.python.org', script='document.title = "scrapy_selenium";')
        html_response = self.selenium_middleware.process_request(request=selenium_request, spider=None)
        self.assertEqual(html_response.selector.xpath('//title/text()').extract_first(), 'scrapy_selenium')
        html_response.meta.get('driver').quit()

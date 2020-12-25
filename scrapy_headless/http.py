"""This module contains the ``SeleniumRequest`` class"""

from scrapy import Request
from scrapy.http import HtmlResponse
from parsel.csstranslator import HTMLTranslator
from cssselect.parser import SelectorSyntaxError
from selenium.webdriver.support.ui import WebDriverWait


class SeleniumRequest(Request):
    """Scrapy ``Request`` subclass providing additional arguments"""

    def __init__(self, wait_time=None, wait_until=None, screenshot=False, script=None, *args, **kwargs):
        """Initialize a new selenium request

        Parameters
        ----------
        wait_time: int
            The number of seconds to wait.
        wait_until: method
            One of the "selenium.webdriver.support.expected_conditions". The response
            will be returned until the given condition is fulfilled.
        screenshot: bool
            If True, a screenshot of the page will be taken and the data of the screenshot
            will be returned in the response "meta" attribute.
        script: str
            JavaScript code to execute.

        """

        self.wait_time = wait_time
        self.wait_until = wait_until
        self.screenshot = screenshot
        self.script = script

        super().__init__(*args, **kwargs)


class SeleniumResponse(HtmlResponse):

    @property
    def interact(self):
        """Shortcut to the WebDriver"""
        return self.meta['driver']

    def click(self, query):
        """Clicks on an element specified by query, and reloads the pages source into to the body"""
        try:
            xpath_query = HTMLTranslator().css_to_xpath(query)
        except SelectorSyntaxError:
            xpath_query = query
        self.interact.find_element_by_xpath(xpath_query).click()
        if self.request.wait_until:
            WebDriverWait(self.interact, self.request.wait_time).until(self.request.wait_until)
        return self.replace(url=self.interact.current_url,
                            body=str.encode(self.interact.page_source))

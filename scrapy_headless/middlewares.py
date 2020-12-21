"""This module contains the ``SeleniumMiddleware`` scrapy middleware"""

from importlib import import_module
from os.path import abspath, join, dirname

# from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse
from selenium.webdriver.support.ui import WebDriverWait

from .http import SeleniumRequest


class SeleniumMiddleware:
    """Scrapy middleware handling the requests using selenium"""

    _block_ads = False

    def __init__(self, driver_name, driver_executable_path, driver_arguments, browser_executable_path):
        """Initialize the selenium webdriver arguments

        Parameters
        ----------
        driver_name: str
            The selenium ``WebDriver`` to use
        driver_executable_path: str
            The path of the executable binary of the driver
        driver_arguments: list
            A list of arguments to initialize the driver
        browser_executable_path: str
            The path of the executable binary of the browser
        """

        webdriver_base_path = f'selenium.webdriver.{driver_name}'

        driver_class_module = import_module(f'{webdriver_base_path}.webdriver')
        self.driver_class = getattr(driver_class_module, 'WebDriver')

        driver_options_module = import_module(f'{webdriver_base_path}.options')
        driver_options_class = getattr(driver_options_module, 'Options')

        driver_options = driver_options_class()
        if browser_executable_path:
            driver_options.binary_location = browser_executable_path
        if '--block-ads' in driver_arguments:
            self._block_ads = True
            driver_arguments.remove('--block-ads')
        for argument in driver_arguments:
            driver_options.add_argument(argument)

        self.driver_kwargs = {'executable_path': driver_executable_path, 'options': driver_options}

    @classmethod
    def from_crawler(cls, crawler):
        """Initialize the middleware with the crawler settings"""

        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME')
        driver_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        browser_executable_path = crawler.settings.get('SELENIUM_BROWSER_EXECUTABLE_PATH')
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS')

        if not driver_name or not driver_executable_path:
            raise NotConfigured('SELENIUM_DRIVER_NAME and SELENIUM_DRIVER_EXECUTABLE_PATH must be set')

        middleware = cls(driver_name=driver_name, driver_executable_path=driver_executable_path,
                         driver_arguments=driver_arguments, browser_executable_path=browser_executable_path)

        return middleware

    def process_request(self, request, spider):
        """Process a request using the selenium driver if applicable"""

        if not isinstance(request, SeleniumRequest):
            return None

        driver = self.driver_class(**self.driver_kwargs)
        if self._block_ads:
            addon_path = join(dirname(abspath(__file__)), 'uBlock0@raymondhill.net.xpi')
            driver.install_addon(addon_path, temporary=True)
        driver.get(request.url)

        for cookie_name, cookie_value in request.cookies.items():
            driver.add_cookie({'name': cookie_name, 'value': cookie_value})

        if request.wait_until:
            WebDriverWait(driver, request.wait_time).until(request.wait_until)

        if request.screenshot:
            request.meta['screenshot'] = driver.get_screenshot_as_png()

        if request.script:
            driver.execute_script(request.script)

        body = str.encode(driver.page_source)

        # Expose the driver via the "meta" attribute
        request.meta.update({'driver': driver})

        return HtmlResponse(driver.current_url, body=body, encoding='utf-8', request=request)

    def process_spider_output(self, response, result, spider):
        """Shutdown the driver when spider is finished processing the response"""
        response.meta['driver'].quit()
        return result

"""This module contains the test cases for the http module of the ``scrapy_headless`` package"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from scrapy_headless.http import SeleniumRequest
from scrapy_headless.middlewares import SeleniumMiddleware


def test_response_click_should_reload_page_source(crawler):
    market_cap_column_selector = '//*[@id="scr-res-table"]/div[1]/table/thead/tr/th[6]'
    selenium_middleware = SeleniumMiddleware.from_crawler(crawler)
    selenium_request = SeleniumRequest(url='https://finance.yahoo.com/cryptocurrencies', wait_time=10,
                                       wait_until=EC.element_to_be_clickable((By.XPATH, market_cap_column_selector)))
    selenium_response = selenium_middleware.process_request(request=selenium_request, spider=None)

    page_source_before = selenium_response.interact.page_source
    body_before = selenium_response.body

    selenium_response = selenium_response.click(market_cap_column_selector)
    page_source_after = selenium_response.interact.page_source
    body_after = selenium_response.body
    try:
        assert page_source_before != page_source_after
        assert body_before != body_after
    except AssertionError:
        raise
    finally:
        selenium_response.interact.quit()

# Scrapy with Headless Selenium

Scrapy middleware to handle dynamic web pages, using Selenium and running in headless mode by default:

1. Running in headless mode by default
2. Running by default with ad blocking browser plugin, for faster scraping (only for FireFox, see [this issue](https://bugs.chromium.org/p/chromium/issues/detail?id=706008#c5))
3. Dynamic responses, to allow interaction with the web page being scraped

## Installation
```
$ pip install scrapy-headless-selenium
```
You should use **python>=3.6**.
You will also need one of the Selenium compatible browsers and drivers (FireFox & geckodriver or Chrome & chromium-driver).

## Configuration
1. Add the browser to use, the path to the driver executable, and the arguments to pass to the executable to the scrapy settings:
    ```python
    from shutil import which

    SELENIUM_DRIVER_NAME = 'firefox'
    SELENIUM_DRIVER_EXECUTABLE_PATH = which('geckodriver')
    SELENIUM_DRIVER_ARGUMENTS=['-headless']  # '--headless' if using chrome instead of firefox
    ```

Optionally, set the path to the browser executable:
    ```python
    SELENIUM_BROWSER_EXECUTABLE_PATH = which('firefox')
    ```

2. Add the `SeleniumMiddleware` to the downloader middlewares and to the spider middlewares:
    ```python
    DOWNLOADER_MIDDLEWARES = {
        'scrapy_headless.SeleniumMiddleware': 800
    }
    SPIDER_MIDDLEWARES = {
        'scrapy_headless.SeleniumMiddleware': 800
    }
    ```
## Usage
Use the `scrapy_headless.SeleniumRequest` instead of the scrapy built-in `Request` like below:
```python
from scrapy_headless import SeleniumRequest

yield SeleniumRequest(url, self.parse_result)
```
The request will be handled by selenium, and the request will have an additional `meta` key, named `driver` containing the selenium driver with the request processed.
```python
def parse_result(self, response):
    print(response.request.meta['driver'].title)
```
For more information about the available driver methods and attributes, refer to the [selenium python documentation](http://selenium-python.readthedocs.io/api.html#module-selenium.webdriver.remote.webdriver)

The `selector` response attribute work as usual (but contains the html processed by the selenium driver).
```python
def parse_result(self, response):
    print(response.selector.xpath('//title/@text'))
```

The Selenium WebDriver is also exposed through the `response.interact` property, to allow interaction with the browser.
The response also implements a `click` method which excepts a CSS / XPATH selector, to click on an element and return a new response with the new body:
```python
def parse_result(self, response):
    response = response.click('#id')  # equivalent to response.click('//[@id="id"]')
    print(response.selector.xpath('//title/@text'))  # searches the reloaded response body
```

### Additional arguments
The `scrapy_headless.SeleniumRequest` accept 4 additional arguments:

#### `wait_time` / `wait_until`

When used, selenium will perform an [Explicit wait](http://selenium-python.readthedocs.io/waits.html#explicit-waits) before returning the response to the spider.
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

yield SeleniumRequest(
    url=url,
    callback=self.parse_result,
    wait_time=10,
    wait_until=EC.element_to_be_clickable((By.ID, 'someid'))
)
```

#### `screenshot`
When used, selenium will take a screenshot of the page and the binary data of the .png captured will be added to the response `meta`:
```python
yield SeleniumRequest(
    url=url,
    callback=self.parse_result,
    screenshot=True
)

def parse_result(self, response):
    with open('image.png', 'wb') as image_file:
        image_file.write(response.meta['screenshot'])
```

#### `script`
When used, selenium will execute custom JavaScript code.
```python
yield SeleniumRequest(
    url,
    self.parse_result,
    script='window.scrollTo(0, document.body.scrollHeight);',
)
```

## Thanks
Special thanks to @clemfromspace which wrote [scrapy-selenium](https://github.com/clemfromspace/scrapy-selenium), which is the original fork for this project.

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

# useful for handling different item types with a single interface
from scrapy import signals


class LexiconSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class LexiconDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


from urllib.parse import urlparse
import time

from curl_cffi import requests as curl_requests
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


class RateLimitMiddleware:
    """Middleware to implement rate limiting similar to the working version"""

    def __init__(self):
        self.request_count = 0

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        self.request_count += 1

        # Pause every 20 requests (5 seconds)
        if self.request_count % 20 == 0:
            spider.logger.info(
                f"Rate limiting: Pausing 5 seconds after {self.request_count} requests"
            )
            time.sleep(5)

        # Longer pause every 50 requests (20 seconds)
        if self.request_count % 50 == 0:
            spider.logger.info(
                f"Rate limiting: Pausing 20 seconds after {self.request_count} requests"
            )
            time.sleep(20)

        return None


class CurlCFFIDownloaderMiddleware:
    def __init__(self):
        # Reuse one session to retain connection pooling/cookies
        self.session = curl_requests.Session(impersonate="chrome120", verify=False)

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        # Only handle our target domain; let Scrapy handle everything else
        netloc = urlparse(request.url).netloc
        if "portal.stf.jus.br" not in netloc:
            return None

        # Convert Scrapy headers to a plain dict of str -> str
        headers = {
            k.decode() if isinstance(k, bytes) else k: (
                v[0].decode()
                if isinstance(v, (list, tuple))
                else (v.decode() if isinstance(v, bytes) else v)
            )
            for k, v in request.headers.items()
        }

        # Merge a realistic UA if one isn’t already present
        headers.setdefault(
            "User-Agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        # Send the request with curl-cffi
        try:
            if request.method == "POST":
                resp = self.session.post(
                    request.url,
                    data=request.body if request.body else None,
                    headers=headers,
                    cookies=request.cookies or None,
                    timeout=30,
                )
            else:
                resp = self.session.get(
                    request.url,
                    headers=headers,
                    cookies=request.cookies or None,
                    timeout=30,
                )
        except Exception as e:
            spider.logger.warning(f"curl_cffi error for {request.url}: {e}")
            return None  # Let Scrapy retry via its standard pipeline

        # Clean up headers to avoid gzip decompression issues
        clean_headers = {}
        for k, v in resp.headers.items():
            # Skip content-encoding to avoid gzip decompression issues
            if k.lower() not in ["content-encoding", "transfer-encoding"]:
                clean_headers[k] = v

        # Build a Scrapy HtmlResponse
        return HtmlResponse(
            url=request.url,
            status=resp.status_code,
            headers=clean_headers,
            body=resp.content,
            request=request,
            encoding=resp.encoding or "utf-8",
        )


class SeleniumMiddleware:
    """Middleware to handle JavaScript-heavy pages using Selenium WebDriver"""

    def __init__(self):
        self.driver = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        # Only use Selenium if explicitly requested
        if not request.meta.get("use_selenium", False):
            return None

        spider.logger.info(f"Using Selenium for {request.url}")

        max_retries = 5
        retry_count = 0
        success = False

        while not success and retry_count < max_retries:
            try:
                # Initialize driver if not already done
                if not self.driver:
                    self._init_driver(spider)

                # Navigate to the page
                if self.driver:
                    self.driver.get(request.url)

                    # Check for common error pages
                    page_source = self.driver.page_source
                    if "403 Forbidden" in page_source or "CAPTCHA" in page_source:
                        raise Exception("Access denied - 403 or CAPTCHA detected")
                    if "502 Bad Gateway" in page_source:
                        raise Exception("502 Bad Gateway error")

                    # Wait for page to load
                    time.sleep(2)

                    # Wait for specific element if specified
                    if request.meta.get("wait_for_element"):
                        try:
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located(
                                    (By.CSS_SELECTOR, request.meta["wait_for_element"])
                                )
                            )
                            spider.logger.info(f"Found element: {request.meta['wait_for_element']}")
                        except TimeoutException:
                            spider.logger.warning(
                                f"Timeout waiting for element: {request.meta['wait_for_element']}"
                            )

                    # Execute custom JavaScript if specified
                    if request.meta.get("execute_js"):
                        try:
                            self.driver.execute_script(request.meta["execute_js"])
                            time.sleep(1)
                            spider.logger.info("Executed custom JavaScript")
                        except Exception as e:
                            spider.logger.warning(f"Error executing JavaScript: {e}")

                    # Wait for AJAX requests to complete if specified
                    if request.meta.get("wait_for_ajax"):
                        try:
                            # Wait for jQuery to be available and AJAX to complete
                            WebDriverWait(self.driver, 10).until(
                                lambda driver: driver.execute_script("return jQuery.active == 0")
                            )
                            spider.logger.info("AJAX requests completed")
                        except TimeoutException:
                            spider.logger.warning("Timeout waiting for AJAX requests to complete")

                success = True

            except Exception as e:
                retry_count += 1
                spider.logger.warning(f"Attempt {retry_count} failed: {e}")

                if retry_count < max_retries:
                    # Close and recreate driver on error
                    if self.driver:
                        try:
                            self.driver.quit()
                        except:
                            pass
                        self.driver = None

                    # Wait before retry with exponential backoff
                    wait_time = min(5 * (2**retry_count), 60)  # Max 60 seconds
                    spider.logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    spider.logger.error(f"All {max_retries} attempts failed for {request.url}")
                    return None

        if success and self.driver:
            # Create response with the page source
            response = HtmlResponse(
                url=request.url,
                body=self.driver.page_source.encode("utf-8"),
                encoding="utf-8",
                request=request,
            )

            # Let Scrapy's CookiesMiddleware handle cookie management automatically
            # The middleware will extract cookies from Set-Cookie headers in responses
            return response

        return None

    def _init_driver(self, spider):
        """Initialize Chrome WebDriver with advanced anti-detection options"""
        options = Options()

        # Custom user agent that mimics real browser
        my_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"

        # Advanced Chrome options for anti-detection
        options.add_argument("--incognito")
        options.add_argument("--headless")  # Can be disabled for debugging
        options.add_argument("--window-size=920,600")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        # Fix for DevToolsActivePort error in headless environments
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-field-trial-config")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument(f"--user-agent={my_user_agent}")

        # Additional experimental options for stealth
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Disable images and CSS for faster loading (optional)
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.stylesheets": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        options.add_experimental_option("prefs", prefs)

        try:
            self.driver = webdriver.Chrome(options=options)

            # Execute script to remove webdriver property
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            spider.logger.info(
                "Selenium WebDriver initialized successfully with anti-detection features"
            )
        except Exception as e:
            spider.logger.error(f"Failed to initialize Selenium WebDriver: {e}")
            raise

    def spider_closed(self, spider):
        """Clean up WebDriver when spider closes"""
        if self.driver:
            try:
                self.driver.quit()
                spider.logger.info("Selenium WebDriver closed")
            except Exception as e:
                spider.logger.warning(f"Error closing WebDriver: {e}")

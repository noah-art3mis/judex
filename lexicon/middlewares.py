# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


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
        spider.logger.info('Spider opened: %s' % spider.name)


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
        spider.logger.info('Spider opened: %s' % spider.name)

from scrapy.http import HtmlResponse
from urllib.parse import urlparse
from curl_cffi import requests as curl_requests

class CurlCFFIDownloaderMiddleware:
    def __init__(self):
        # Reuse one session to retain connection pooling/cookies
        self.session = curl_requests.Session(impersonate="chrome120")

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        # Only handle our target domain; let Scrapy handle everything else
        netloc = urlparse(request.url).netloc
        if "portal.stf.jus.br" not in netloc:
            return None

        # Convert Scrapy headers to a plain dict of str -> str
        headers = {k.decode() if isinstance(k, bytes) else k:
                   v[0].decode() if isinstance(v, (list, tuple)) else (v.decode() if isinstance(v, bytes) else v)
                   for k, v in request.headers.items()}

        # Merge a realistic UA if one isn’t already present
        headers.setdefault("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

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

        # Build a Scrapy HtmlResponse
        return HtmlResponse(
            url=request.url,
            status=resp.status_code,
            headers={k: v for k, v in resp.headers.items()},
            body=resp.content,
            request=request,
            encoding=resp.encoding or "utf-8",
        )
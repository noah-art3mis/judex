from shutil import which

BOT_NAME = "lexicon"

SPIDER_MODULES = ["lexicon.spiders"]
NEWSPIDER_MODULE = "lexicon.spiders"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

ROBOTSTXT_OBEY = False

# CONCURRENT_REQUESTS = 32
DOWNLOAD_DELAY = 1.0
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# COOKIES_ENABLED = False

# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#     "Accept-Language": "en-US,en;q=0.5",
#     "Accept-Encoding": "gzip, deflate, br, zstd",
#     "DNT": "1",
#     "Connection": "keep-alive",
#     "Upgrade-Insecure-Requests": "1",
#     "Sec-Fetch-Dest": "document",
#     "Sec-Fetch-Mode": "navigate",
#     "Sec-Fetch-Site": "same-origin",
#     "Sec-Fetch-User": "?1",
#     "Sec-GPC": "1",
# }

# SPIDER_MIDDLEWARES = {
# }

DOWNLOADER_MIDDLEWARES = {
    "scrapy_selenium.SeleniumMiddleware": 800,
}

# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# ITEM_PIPELINES = {
#    'lexicon.pipelines.LexiconPipeline': 300,
# }

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = True

HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# JSON output settings for indented output
FEEDS = {
    "out.json": {
        "format": "json",
        "indent": 2,
        "encoding": "utf8",
        "store_empty": False,
        "fields": None,
        "item_export_kwargs": {
            "export_empty_fields": True,
        },
    },
    "out.csv": {
        "format": "csv",
        "encoding": "utf8",
        "store_empty": False,
    },
}

###

# Make retries a bit more forgiving when sites rate-limit
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [403, 408, 429, 500, 502, 503, 504]

# Enable strict item validation
STRICT_ITEMS = True

###

SELENIUM_DRIVER_NAME = "chrome"
SELENIUM_DRIVER_EXECUTABLE_PATH = which("chromedriver")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"

SELENIUM_DRIVER_ARGUMENTS = [
    "--headless",
    "--incognito",
    "--window-size=920,600",
    "--disable-blink-features=AutomationControlled",
    f"--user-agent={USER_AGENT}",
]

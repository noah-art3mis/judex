from shutil import which

BOT_NAME = "judex"

SPIDER_MODULES = ["judex.spiders"]
NEWSPIDER_MODULE = "judex.spiders"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"

ROBOTSTXT_OBEY = False

DOWNLOAD_DELAY = 2.0
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
# CONCURRENT_REQUESTS_PER_IP = 16

# COOKIES_ENABLED = False

# TELNETCONSOLE_ENABLED = False

# SPIDER_MIDDLEWARES = {
# }

DOWNLOADER_MIDDLEWARES = {
    "scrapy_selenium.SeleniumMiddleware": 800,
}

# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

ITEM_PIPELINES = {
    "judex.pydantic_pipeline.PydanticValidationPipeline": 200,
    # "judex.pipelines.DatabasePipeline": 300,  # SQLite database (enabled dynamically)
    # JSON, CSV, and JSONL handled by custom pipelines
}

JSON_OUTPUT_FILE = "data.json"
CSV_OUTPUT_FILE = "data.csv"
DATABASE_PATH = "judex.db"

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 360
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES: list[int] = []
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

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
SELENIUM_DRIVER_ARGUMENTS = [
    "--headless",
    "--incognito",
    "--window-size=920,600",
    "--disable-blink-features=AutomationControlled",
    f"--user-agent={USER_AGENT}",
]

LOG_LEVEL = "DEBUG"

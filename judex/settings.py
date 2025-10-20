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
    "judex.pipelines.GroundTruthOrderPipeline": 150,
    "judex.pydantic_pipeline.PydanticValidationPipeline": 200,
}

# Ensure top-level field order when exporting feeds
FEED_EXPORT_FIELDS = [
    "incidente",
    "classe",
    "processo_id",
    "numero_unico",
    "meio",
    "publicidade",
    "badges",
    "liminar",
    "assuntos",
    "data_protocolo",
    "orgao_origem",
    "origem",
    "numero_origem",
    "volumes",
    "folhas",
    "apensos",
    "relator",
    "primeiro_autor",
    "partes",
    "andamentos",
    "decisoes",
    "sessao_virtual",
    "deslocamentos",
    "peticoes",
    "recursos",
    "pautas",
    "status",
    "extraido",
    "html",
]

FEED_EXPORT_INDENT = 2
FEED_EXPORT_ENCODING = "utf-8"

# Global nested field order templates applied to all items
NESTED_FIELD_ORDERS = {
    "partes": ["index", "tipo", "nome"],
    "andamentos": [
        "index_num",
        "data",
        "nome",
        "complemento",
        "link_descricao",
        "link",
        "julgador",
    ],
    "decisoes": [
        "index_num",
        "data",
        "nome",
        "complemento",
        "julgador",
        "link",
    ],
    "sessao_virtual": ["data", "tipo", "numero", "relator", "status", "participantes"],
    "deslocamentos": [
        "index_num",
        "guia",
        "recebido_por",
        "data_recebido",
        "enviado_por",
        "data_enviado",
    ],
    "peticoes": ["index", "data", "tipo", "autor", "recebido_data", "recebido_por"],
    "recursos": ["index_num", "data", "nome", "julgador", "complemento", "autor"],
    "pautas": ["index_num", "data", "nome", "complemento", "relator"],
}

# Full nested template to force exact ordering across entire item
NESTED_TEMPLATE = {
    "incidente": None,
    "classe": None,
    "processo_id": None,
    "numero_unico": None,
    "meio": None,
    "publicidade": None,
    "badges": [],
    "liminar": None,
    "assuntos": [],
    "data_protocolo": None,
    "orgao_origem": None,
    "origem": None,
    "numero_origem": [],
    "volumes": None,
    "folhas": None,
    "apensos": None,
    "relator": None,
    "primeiro_autor": None,
    "partes": [{"index": None, "tipo": None, "nome": None}],
    "andamentos": [
        {
            "index_num": None,
            "data": None,
            "nome": None,
            "complemento": None,
            "link_descricao": None,
            "link": None,
            "julgador": None,
        }
    ],
    "decisoes": [
        {
            "index_num": None,
            "data": None,
            "nome": None,
            "complemento": None,
            "julgador": None,
            "link": None,
        }
    ],
    "sessao_virtual": [
        {
            "data": None,
            "tipo": None,
            "numero": None,
            "relator": None,
            "status": None,
            "participantes": [],
        }
    ],
    "deslocamentos": [
        {
            "index_num": None,
            "guia": None,
            "recebido_por": None,
            "data_recebido": None,
            "enviado_por": None,
            "data_enviado": None,
        }
    ],
    "peticoes": [
        {
            "index": None,
            "data": None,
            "tipo": None,
            "autor": None,
            "recebido_data": None,
            "recebido_por": None,
        }
    ],
    "recursos": [
        {
            "index_num": None,
            "data": None,
            "nome": None,
            "julgador": None,
            "complemento": None,
            "autor": None,
        }
    ],
    "pautas": [
        {
            "index_num": None,
            "data": None,
            "nome": None,
            "complemento": None,
            "relator": None,
        }
    ],
    "status": None,
    "extraido": None,
    "html": None,
}

JSON_OUTPUT_FILE = "data.json"
CSV_OUTPUT_FILE = "data.csv"
DATABASE_PATH = "judex.db"

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
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

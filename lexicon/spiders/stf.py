import scrapy


class StfSpider(scrapy.Spider):
    name = "stf"
    allowed_domains = ["portal.stf.jus.br"]
    start_urls = ["https://portal.stf.jus.br"]

    def parse(self, response):
        pass

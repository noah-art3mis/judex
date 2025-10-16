import scrapy
import hashlib
from datetime import datetime
from scrapy.exceptions import CloseSpider
import json


class StfSpider(scrapy.Spider):
    """
    Spider para o site do STF.

    Args:
        classe: A classe dos processos, ex: 'ADI'.
        numero_processo: Uma lista JSON de números de processos, ex: '[4916, 4917]'.

    Exemplo:
        scrapy crawl stf -a classe='ADI' -a numero_processo='[4436, 8000]'
    """

    name = "stf"
    allowed_domains = ["portal.stf.jus.br"]

    def __init__(self, classe=None, numero_processo=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not classe:
            raise ValueError("classe is required, e.g., -a classe=ADI")

        self.classe = classe

        if not numero_processo:
            raise ValueError("numero_processo is required, e.g., -a numero_processo='[4916]'")

        try:
            self.numeros = json.loads(numero_processo)
        except Exception:
            raise ValueError("numero_processo must be a JSON list, e.g., '[4916, 4917]'")

    def start_requests(self):
        base = "https://portal.stf.jus.br"
        for numero in self.numeros:
            url = (
                f"{base}/processos/listarProcessos.asp?classe={self.classe}&numeroProcesso={numero}"
            )
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        title = response.xpath("//title/text()\n").get()
        body = response.text or ""
        digest = hashlib.sha256(body.encode("utf-8", errors="ignore")).hexdigest()
        has_conteudo = bool(response.css("#conteudo"))

        yield {
            "url": response.url,
            "status": response.status,
            "title": title,
            "has_conteudo": has_conteudo,
            "sample": body[:180],
            "sha256": digest,
            "server": response.headers.get(b"Server", b"").decode("utf-8", "ignore"),
            "date": datetime.utcnow().isoformat() + "Z",
        }

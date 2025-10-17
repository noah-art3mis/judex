import datetime
import json
from collections.abc import Iterator

import scrapy
from bs4 import BeautifulSoup
from scrapy.http import Response
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from lexicon.items import STFCaseItem
from lexicon.types import validate_case_type


class StfSpider(scrapy.Spider):
    """
    Spider para o site do STF.

    Args:
        classe: A classe dos processos, ex: 'ADI'.
        processos: Uma lista JSON de números de processos, ex: '[4916, 4917]'.

    Exemplo:
        scrapy crawl stf -a classe='ADI' -a processos='[4436, 8000]'
    """

    name = "stf"
    allowed_domains = ["portal.stf.jus.br"]

    def __init__(
        self, classe: str | None = None, processos: str | None = None, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

        if not classe:
            raise ValueError("classe is required, e.g., -a classe=ADI")

        # Validate the case class against the enum
        self.classe = validate_case_type(classe)

        if not processos:
            raise ValueError("processos is required, e.g., -a processos='[4916]'")

        try:
            self.numeros = json.loads(processos)
        except Exception:
            raise ValueError("processos must be a JSON list, e.g., '[4916, 4917]'")

    def start_requests(self) -> Iterator[scrapy.Request]:
        base = "https://portal.stf.jus.br"
        for numero in self.numeros:
            # First, get the main page to extract the incidente number
            url = (
                f"{base}/processos/listarProcessos.asp?classe={self.classe}&numeroProcesso={numero}"
            )

            yield SeleniumRequest(
                url=url,
                callback=self.parse_main_page_selenium,
                meta={"numero": numero},
                wait_time=10,
                wait_until=EC.presence_of_element_located((By.ID, "conteudo")),
            )

    def get_element_by_id(self, driver: WebDriver, id: str) -> str:
        Wait = WebDriverWait(driver, 40)
        Wait.until(EC.presence_of_element_located((By.ID, id)))
        return driver.find_element(By.ID, id).get_attribute("value")

    def get_element_by_xpath(self, driver: WebDriver, xpath: str) -> str:
        Wait = WebDriverWait(driver, 40)
        Wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        return driver.find_element(By.XPATH, xpath).get_attribute("innerHTML")

    def clean_text(self, html_text: str) -> str:
        """Clean HTML text by removing extra whitespace and HTML entities"""
        if not html_text:
            return ""

        # Parse with BeautifulSoup to handle HTML entities and tags
        soup = BeautifulSoup(html_text, "html.parser")
        # Get text content and strip whitespace
        text = soup.get_text(strip=True)
        # Clean up any remaining extra whitespace
        text = " ".join(text.split())
        return text

    def parse_main_page_selenium(self, response: Response) -> Iterator[scrapy.Request]:
        """Parse the main page and extract incidente number, then make AJAX requests"""
        # soup = BeautifulSoup(response.text, "html.parser")
        driver = response.request.meta["driver"]

        if "CAPTCHA" in driver.page_source:
            self.logger.error(f"CAPTCHA detected in {response.url}")
            return
        if "403 Forbidden" in driver.page_source:
            self.logger.error(f"403 Forbidden detected in {response.url}")
            return
        if "502 Bad Gateway" in driver.page_source:
            self.logger.error(f"502 Bad Gateway detected in {response.url}")
            return

        # Extract incidente number from the page
        incidente = self.get_element_by_id(driver, "incidente")
        if not incidente:
            self.logger.error(f"Could not extract incidente number from {response.url}")
            return

        # Create the main item with basic info
        item = STFCaseItem()
        item["processo_id"] = response.meta["numero"]
        item["incidente"] = incidente
        # item["numero_unico"] = extract_numero_unico(soup)
        # item["classe"] = extract_classe(soup)
        # item["liminar"] = extract_liminar(soup)
        # item["tipo_processo"] = extract_tipo_processo(soup)
        item["origem"] = self.clean_text(
            self.get_element_by_xpath(driver, '//*[@id="descricao-procedencia"]')
        )
        # item["origem"] = response.selector.xpath('//*[@id="descricao-procedencia"]/text()').get()
        # item["relator"] = extract_relator(soup)
        item["data_protocolo"] = self.clean_text(
            self.get_element_by_xpath(
                driver, '//*[@id="informacoes-completas"]/div[2]/div[1]/div[2]/div[2]'
            )
        )
        item["origem_orgao"] = self.clean_text(
            self.get_element_by_xpath(
                driver, '//*[@id="informacoes-completas"]/div[2]/div[1]/div[2]/div[4]'
            )
        )
        # item["autor1"] = extract_autor1(soup)
        assuntos_html = self.get_element_by_xpath(
            driver, '//*[@id="informacoes-completas"]/div[1]/div[2]'
        )
        # Parse the HTML to extract clean subject text
        soup = BeautifulSoup(assuntos_html, "html.parser")
        item["assuntos"] = [
            self.clean_text(li.get_text()) for li in soup.find_all("li") if li.get_text().strip()
        ]
        item["status"] = response.status

        item["extraido"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Initialize AJAX fields as empty
        item["partes"] = []
        item["andamentos"] = []
        item["decisoes"] = []
        item["deslocamentos"] = []
        item["peticoes"] = []
        item["recursos"] = []
        item["pautas"] = []
        item["informacoes"] = {}
        item["sessao"] = {}

        yield item

    # def parse(self, response: Response) -> Iterator[STFCaseItem]:
    #     # Parse HTML content
    #     soup = BeautifulSoup(response.text, "html.parser")

    #     # Create STF case item
    #     item = STFCaseItem()

    #     # ids
    #     item["processo_id"] = response.meta["numero"]
    #     item["incidente"] = extract_incidente(soup)
    #     item["numero_unico"] = extract_numero_unico(soup)

    #     # classificacao
    #     item["classe"] = extract_classe(soup)
    #     item["liminar"] = extract_liminar(soup)
    #     item["tipo_processo"] = extract_tipo_processo(soup)

    #     # detalhes
    #     item["origem"] = extract_origem(soup)
    #     item["relator"] = extract_relator(soup)
    #     item["liminar"] = extract_liminar(soup)
    #     item["data_protocolo"] = extract_data_protocolo(soup)
    #     item["origem_orgao"] = extract_origem_orgao(soup)
    #     item["autor1"] = extract_autor1(soup)
    #     item["assuntos"] = extract_assuntos(soup)

    #     # metadados
    #     item["status"] = response.status
    #     # Don't store large HTML content to avoid memory issues
    #     item["extraido"] = datetime.datetime.now().isoformat() + "Z"

    #     yield item

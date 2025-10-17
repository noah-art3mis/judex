import datetime
import json
import time
from collections.abc import Iterator

import scrapy
from bs4 import BeautifulSoup
from scrapy.http import Response
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from lexicon.extract import (
    extract_andamentos,
    extract_assuntos,
    extract_autor1,
    extract_classe,
    extract_data_protocolo,
    extract_decisoes,
    extract_deslocamentos,
    extract_liminar,
    extract_numero_unico,
    extract_origem,
    extract_origem_orgao,
    extract_partes,
    extract_pautas,
    extract_peticoes,
    extract_recursos,
    extract_relator,
    extract_sessao,
    extract_tipo_processo,
)
from lexicon.items import STFCaseItem
from lexicon.types import validate_case_type
from lexicon.database import get_existing_processo_ids, get_failed_processo_ids


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
        self,
        classe: str | None = None,
        processos: str | None = None,
        internal_delay: float = 1.0,
        skip_existing: bool = True,
        retry_failed: bool = True,
        max_age_hours: int = 24,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.internal_delay = internal_delay
        self.skip_existing = skip_existing
        self.retry_failed = retry_failed
        self.max_age_hours = max_age_hours

        if not classe:
            raise ValueError("classe is required, e.g., -a classe=ADI")

        # Validate the case class against the enum
        self.classe = validate_case_type(classe)

        if not processos:
            raise ValueError("processos is required, e.g., -a processos='[4916]'")

        try:
            self.numeros = json.loads(processos)
        except Exception as e:
            raise ValueError("processos must be a JSON list, e.g., '[4916, 4917]'") from e

    def start_requests(self) -> Iterator[scrapy.Request]:
        base = "https://portal.stf.jus.br"
        
        # Get database path from settings
        db_path = self.settings.get("DATABASE_PATH", "lexicon.db")
        
        # Get existing and failed processo IDs from database
        existing_ids = set()
        failed_ids = set()
        
        if self.skip_existing or self.retry_failed:
            try:
                if self.skip_existing:
                    existing_ids = get_existing_processo_ids(db_path, self.classe, self.max_age_hours)
                    self.logger.info(f"Found {len(existing_ids)} existing processo IDs to skip")
                
                if self.retry_failed:
                    failed_ids = get_failed_processo_ids(db_path, self.classe, self.max_age_hours)
                    self.logger.info(f"Found {len(failed_ids)} failed processo IDs to retry")
                    
            except Exception as e:
                self.logger.warning(f"Could not check database for existing data: {e}")
        
        # Filter numeros based on database check
        numeros_to_scrape = []
        skipped_count = 0
        
        for numero in self.numeros:
            if self.skip_existing and numero in existing_ids:
                self.logger.info(f"Skipping {numero} - already exists in database")
                skipped_count += 1
                continue
            
            # Always retry failed cases if retry_failed is True
            if self.retry_failed and numero in failed_ids:
                self.logger.info(f"Retrying {numero} - previously failed")
            
            numeros_to_scrape.append(numero)
        
        self.logger.info(f"Scraping {len(numeros_to_scrape)} out of {len(self.numeros)} processos (skipped {skipped_count})")
        
        # Generate requests only for numeros that need scraping
        for numero in numeros_to_scrape:
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
        time.sleep(self.internal_delay)
        Wait = WebDriverWait(driver, 40)
        Wait.until(EC.presence_of_element_located((By.ID, id)))
        return driver.find_element(By.ID, id).get_attribute("value")

    def get_element_by_xpath(self, driver: WebDriver, xpath: str) -> str:
        time.sleep(self.internal_delay)
        Wait = WebDriverWait(driver, 40)
        Wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        return driver.find_element(By.XPATH, xpath).get_attribute("innerHTML")

    def clean_text(self, html_text: str) -> str | None:
        """Clean HTML text by removing extra whitespace and HTML entities"""
        if not html_text:
            return None

        soup = BeautifulSoup(html_text, "html.parser")
        text = soup.get_text(strip=True)
        text = " ".join(text.split())
        return text

    def parse_main_page_selenium(self, response: Response) -> Iterator[scrapy.Request]:
        driver = response.request.meta["driver"]  # type: ignore
        page_html = driver.page_source
        soup = BeautifulSoup(page_html, "html.parser")

        if "CAPTCHA" in driver.page_source:
            self.logger.error(f"CAPTCHA detected in {response.url}")
            return
        if "403 Forbidden" in driver.page_source:
            self.logger.error(f"403 Forbidden detected in {response.url}")
            return
        if "502 Bad Gateway" in driver.page_source:
            self.logger.error(f"502 Bad Gateway detected in {response.url}")
            return

        # NON NULL
        incidente = int(self.get_element_by_id(driver, "incidente"))
        if not incidente:
            self.logger.error(f"Could not extract incidente number from {response.url}")
            return

        item = STFCaseItem()

        # ids
        item["processo_id"] = response.meta["numero"]
        item["incidente"] = int(incidente)
        # Try optimized extractors first
        try:
            item["numero_unico"] = extract_numero_unico(soup)
        except Exception as e:
            self.logger.warning(f"Could not extract numero_unico with extract function: {e}")
            item["numero_unico"] = None

        try:
            item["classe"] = extract_classe(soup) or self.classe
        except Exception as e:
            self.logger.warning(f"Could not extract classe with extract function: {e}")
            item["classe"] = self.classe

        try:
            item["liminar"] = extract_liminar(self, driver, soup)
        except Exception as e:
            self.logger.warning(f"Could not extract liminar: {e}")
            item["liminar"] = []

        try:
            item["relator"] = extract_relator(soup)
        except Exception as e:
            self.logger.warning(f"Could not extract relator with extract function: {e}")
            item["relator"] = None

        try:
            item["tipo_processo"] = extract_tipo_processo(soup)
        except Exception as e:
            self.logger.warning(f"Could not extract tipo_processo with extract function: {e}")
            # Fallback to page source detection
            if "Processo Físico" in page_html:
                item["tipo_processo"] = "Físico"
            elif "Processo Eletrônico" in page_html:
                item["tipo_processo"] = "Eletrônico"
            else:
                item["tipo_processo"] = None

        try:
            item["origem"] = extract_origem(self, driver, soup)
        except Exception as e:
            self.logger.warning(f"Could not extract origem with extract function: {e}")
            # Fallback to Selenium
            try:
                origem_element = driver.find_element(By.ID, "descricao-procedencia")
                item["origem"] = self.clean_text(origem_element.text)
            except Exception as e2:
                self.logger.warning(f"Could not extract origem with Selenium fallback: {e2}")
                item["origem"] = None

        try:
            item["data_protocolo"] = extract_data_protocolo(self, driver, soup)
        except Exception as e:
            self.logger.warning(f"Could not extract data_protocolo with extract function: {e}")
            item["data_protocolo"] = None

        try:
            item["origem_orgao"] = extract_origem_orgao(self, driver, soup)
        except Exception as e:
            self.logger.warning(f"Could not extract origem_orgao with extract function: {e}")
            item["origem_orgao"] = None

        try:
            item["autor1"] = extract_autor1(self, driver, soup)
        except Exception as e:
            self.logger.warning(f"Could not extract autor1: {e}")
            item["autor1"] = None

        try:
            item["assuntos"] = extract_assuntos(self, driver, soup)
        except Exception as e:
            self.logger.warning(f"Could not extract assuntos with extract function: {e}")
            item["assuntos"] = []

        # Try to extract AJAX content using extract functions
        try:
            item["partes"] = extract_partes(self, driver, soup)
        except Exception as e:
            self.logger.warning(f"Could not extract partes: {e}")
            item["partes"] = []

        try:
            item["andamentos"] = extract_andamentos(self, driver, soup)
        except Exception as e:
            self.logger.warning(f"Could not extract andamentos: {e}")
            item["andamentos"] = []

        try:
            item["decisoes"] = extract_decisoes(self, driver, soup)
        except Exception as e:
            self.logger.warning(f"Could not extract decisoes: {e}")
            item["decisoes"] = []

        try:
            item["deslocamentos"] = extract_deslocamentos(self, driver, soup)
        except Exception as e:
            self.logger.warning(f"Could not extract deslocamentos: {e}")
            item["deslocamentos"] = []

        # Try to extract remaining AJAX content using extract functions
        try:
            item["peticoes"] = extract_peticoes(self, driver, soup)
        except Exception as e:
            self.logger.warning(f"Could not extract peticoes: {e}")
            item["peticoes"] = []

        try:
            item["recursos"] = extract_recursos(self, driver, soup)
        except Exception as e:
            self.logger.warning(f"Could not extract recursos: {e}")
            item["recursos"] = []

        try:
            item["pautas"] = extract_pautas(self, driver, soup)
        except Exception as e:
            self.logger.warning(f"Could not extract pautas: {e}")
            item["pautas"] = []

        try:
            item["sessao"] = extract_sessao(self, driver, soup)
        except Exception as e:
            self.logger.warning(f"Could not extract sessao: {e}")
            item["sessao"] = {}

        # metadados
        item["status"] = response.status
        item["html"] = page_html
        item["extraido"] = datetime.datetime.now().isoformat() + "Z"

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

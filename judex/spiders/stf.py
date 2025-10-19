import datetime
import json
import re
import time
from collections.abc import AsyncGenerator, Iterator

import scrapy
from bs4 import BeautifulSoup
from scrapy.http import Response
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from judex.database import get_existing_processo_ids, get_failed_processo_ids
from judex.extract import (
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
from judex.items import STFCaseItem
from judex.types import validate_case_type


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
        classe: str,
        processos: str,
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

    def _filter_processos_by_database(self, db_path: str) -> tuple[list, int]:
        """
        Filter process numbers based on database checks for existing and failed records.

        Args:
            db_path: Path to the database file

        Returns:
            Tuple of (filtered_processos, skipped_count)
        """
        # Get existing and failed processo IDs from database
        existing_ids = set()
        failed_ids = set()

        if self.skip_existing or self.retry_failed:
            try:
                if self.skip_existing:
                    existing_ids = get_existing_processo_ids(
                        db_path, self.classe, self.max_age_hours
                    )
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

        self.logger.info(
            f"Scraping {len(numeros_to_scrape)} out of {len(self.numeros)} processos (skipped {skipped_count})"
        )

        return numeros_to_scrape, skipped_count

    async def start(self) -> AsyncGenerator[scrapy.Request, None]:
        base = "https://portal.stf.jus.br"

        # Get database path from settings
        db_path = self.settings.get("DATABASE_PATH")

        # Filter process numbers based on database checks
        numeros_to_scrape, skipped_count = self._filter_processos_by_database(db_path)

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
        text = soup.get_text()
        text = " ".join(text.split())
        return text if text else None

    def parse_main_page_selenium(self, response: Response) -> Iterator[STFCaseItem]:
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

        # Track overall extraction timing
        extraction_start_time = time.time()
        self.crawler.stats.inc_value("extraction/started")

        # Create a dictionary for Pydantic validation
        case_data = {}

        # ids
        case_data["processo_id"] = response.meta["numero"]
        case_data["incidente"] = int(incidente)
        # All extractions now handle their own errors and timing via decorators
        case_data["numero_unico"] = extract_numero_unico(soup)
        case_data["classe"] = extract_classe(soup) or self.classe
        case_data["liminar"] = extract_liminar(self, driver, soup)
        case_data["relator"] = extract_relator(soup)
        case_data["tipo_processo"] = extract_tipo_processo(soup)
        case_data["origem"] = extract_origem(self, driver, soup)
        case_data["data_protocolo"] = extract_data_protocolo(self, driver, soup)
        case_data["origem_orgao"] = extract_origem_orgao(self, driver, soup)
        case_data["autor1"] = extract_autor1(self, driver, soup)
        case_data["assuntos"] = extract_assuntos(self, driver, soup)

        # Wait for AJAX content to load dynamically
        try:
            Wait = WebDriverWait(driver, 10)
            Wait.until(
                lambda d: d.find_element(By.ID, "resumo-partes").get_attribute("innerHTML").strip()
                != ""
                or d.find_element(By.ID, "resumo-partes")
                .get_attribute("innerHTML")
                .count("processo-partes")
                > 0
            )
        except Exception:
            # If the wait fails, continue anyway - the extract function will handle empty data
            pass

        # All AJAX extractions now handle their own errors and timing via decorators
        case_data["partes"] = extract_partes(self, driver, soup)
        case_data["andamentos"] = extract_andamentos(self, driver, soup)
        case_data["decisoes"] = extract_decisoes(self, driver, soup)
        case_data["deslocamentos"] = extract_deslocamentos(self, driver, soup)
        case_data["peticoes"] = extract_peticoes(self, driver, soup)
        case_data["recursos"] = extract_recursos(self, driver, soup)
        case_data["pautas"] = extract_pautas(self, driver, soup)
        case_data["sessao"] = extract_sessao(self, driver, soup)

        # Track total extraction time
        total_extraction_time = time.time() - extraction_start_time
        self.crawler.stats.inc_value("extraction/completed")
        self.crawler.stats.set_value("extraction/total_duration", round(total_extraction_time, 2))

        # Log total timing
        self.logger.info(f"Total extraction time: {total_extraction_time:.3f}s")

        # metadados
        case_data["status"] = response.status
        case_data["html"] = re.sub(r"\s+", " ", page_html.strip())
        case_data["extraido"] = datetime.datetime.now().isoformat() + "Z"

        # Create a Scrapy Item from the validated data for compatibility
        item = STFCaseItem()
        for key, value in case_data.items():
            item[key] = value

        yield item

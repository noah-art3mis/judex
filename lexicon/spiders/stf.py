import datetime
import json
import re
import time
from collections.abc import Iterator

import scrapy
from bs4 import BeautifulSoup
from scrapy.http import Response

from lexicon.items import STFCaseItem
from lexicon.types import validate_case_type
from lexicon.extract import (
    extract_incidente,
    extract_numero_unico,
    extract_classe,
    extract_liminar,
    extract_tipo_processo,
    extract_origem,
    extract_relator,
    extract_data_protocolo,
    extract_origem_orgao,
    extract_autor1,
    extract_assuntos,
    extract_partes,
    extract_andamentos,
    extract_decisoes,
    extract_deslocamentos,
    extract_peticoes,
    extract_recursos,
    extract_pautas,
    extract_informacoes,
    extract_sessao,
)


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

            # Advanced headers that mimic real browser requests
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "pt-PT,pt;q=0.9",
                "DNT": "1",
                "Priority": "u=0, i",
                "Sec-CH-UA": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                "Sec-CH-UA-Mobile": "?0",
                "Sec-CH-UA-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_main_page,
                headers=headers,
                meta={
                    "numero": numero,
                    "use_selenium": True,
                    "wait_for_element": ".processo-titulo",
                    "wait_for_ajax": True,
                },
            )

    def parse_main_page(self, response: Response) -> Iterator[scrapy.Request]:
        """Parse the main page and extract incidente number, then make AJAX requests"""
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract incidente number from the page
        incidente = extract_incidente(soup)
        if not incidente:
            self.logger.error(f"Could not extract incidente number from {response.url}")
            return

        # Create the main item with basic info
        item = STFCaseItem()
        item["processo_id"] = response.meta["numero"]
        item["incidente"] = incidente
        item["numero_unico"] = extract_numero_unico(soup)
        item["classe"] = extract_classe(soup)
        item["liminar"] = extract_liminar(soup)
        item["tipo_processo"] = extract_tipo_processo(soup)
        item["origem"] = extract_origem(soup)
        item["relator"] = extract_relator(soup)
        item["data_protocolo"] = extract_data_protocolo(soup)
        item["origem_orgao"] = extract_origem_orgao(soup)
        item["autor1"] = extract_autor1(soup)
        item["assuntos"] = extract_assuntos(soup)
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

        # Store the item in meta for the AJAX callback
        meta = response.meta.copy()
        meta["item"] = item

        # Make AJAX requests to get the dynamic content
        base = "https://portal.stf.jus.br"
        ajax_endpoints = [
            ("partes", f"{base}/abaPartes.asp?incidente={incidente}"),
            ("andamentos", f"{base}/abaAndamentos.asp?incidente={incidente}&imprimir="),
            ("informacoes", f"{base}/abaInformacoes.asp?incidente={incidente}"),
            ("decisoes", f"{base}/abaDecisoes.asp?incidente={incidente}"),
            ("sessao", f"{base}/abaSessao.asp?incidente={incidente}&tema=N"),
            ("deslocamentos", f"{base}/abaDeslocamentos.asp?incidente={incidente}"),
            ("peticoes", f"{base}/abaPeticoes.asp?incidente={incidente}"),
            ("recursos", f"{base}/abaRecursos.asp?incidente={incidente}"),
            ("pautas", f"{base}/abaPautas.asp?incidente={incidente}"),
        ]

        # Scrapy automatically handles cookies through CookiesMiddleware
        # No need to manually extract and pass cookies

        # Set up headers for AJAX requests
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        try:
            if response.request.headers:
                ua_header = response.request.headers.get("User-Agent")
                if ua_header:
                    if isinstance(ua_header, bytes):
                        user_agent = ua_header.decode("utf-8")
                    else:
                        user_agent = ua_header
        except (TypeError, AttributeError):
            pass

        headers = {
            "User-Agent": user_agent,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "Referer": response.url,
            "Origin": "https://portal.stf.jus.br",
            "X-Requested-With": "XMLHttpRequest",
            "DNT": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "TE": "trailers",
        }

        # Make requests to all AJAX endpoints with session information
        # Add small delays to avoid rate limiting
        for i, (field_name, ajax_url) in enumerate(ajax_endpoints):
            # Add delay between requests (except for the first one)
            if i > 0:
                time.sleep(0.5)  # 500ms delay between requests

            # Use Selenium for AJAX requests that might need JavaScript execution
            use_selenium_for_ajax = field_name in ["sessao", "decisoes"]  # These might need JS

            yield scrapy.Request(
                url=ajax_url,
                callback=self.parse_ajax_response,
                headers=headers,
                # Don't pass cookies manually - let Scrapy handle it
                meta={
                    **meta,
                    "ajax_field": field_name,
                    "use_selenium": use_selenium_for_ajax,
                    "wait_for_element": ".processo-andamentos" if use_selenium_for_ajax else None,
                },
                dont_filter=True,  # Allow duplicate requests
            )

    def parse_ajax_response(self, response: Response) -> Iterator[STFCaseItem]:
        """Parse AJAX response and update the item"""
        item = response.meta["item"]
        field_name = response.meta["ajax_field"]

        # Debug: Log response status only
        self.logger.info(f"AJAX {field_name} response status: {response.status}")

        # Store only essential data, not full HTML
        if response.status == 200:
            item[f"ajax_status_{field_name}"] = "success"
        else:
            item[f"ajax_status_{field_name}"] = f"error_{response.status}"

        # Check for 404 error indicators
        is_404_error = False
        if response.status == 404:
            is_404_error = True
            self.logger.warning(f"404 error for {field_name}: {response.url}")
        elif response.status == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            # Check for common 404 error indicators in HTML
            error_indicators = [
                "404",
                "Not Found",
                "Página não encontrada",
                "Erro 404",
                "The requested URL was not found",
                "File not found",
                "Página não existe",
                "Acesso negado",
                "Forbidden",
            ]

            page_text = soup.get_text().lower()
            for indicator in error_indicators:
                if indicator.lower() in page_text:
                    is_404_error = True
                    self.logger.warning(
                        f"404 error indicator '{indicator}' found in {field_name} response"
                    )
                    break

            # Check for empty or minimal content
            if len(response.text.strip()) < 50:
                is_404_error = True
                self.logger.warning(
                    f"Very short response for {field_name}: {len(response.text)} characters"
                )

            # Check for specific error containers
            error_containers = soup.find_all(
                ["div", "section", "main"], class_=re.compile(r"error|404|not-found", re.I)
            )
            if error_containers:
                is_404_error = True
                self.logger.warning(f"Error container found in {field_name} response")

            # Check for valid content structure based on field type
            if not is_404_error:
                if field_name == "partes":
                    # Check for expected partes structure
                    if not soup.find("div", {"id": "todas-partes"}) and not soup.find(
                        "div", {"id": "partes-resumidas"}
                    ):
                        is_404_error = True
                        self.logger.warning(
                            f"No expected partes structure found in {field_name} response"
                        )
                elif field_name == "andamentos":
                    # Check for expected andamentos structure
                    if not soup.find("div", class_="processo-andamentos"):
                        is_404_error = True
                        self.logger.warning(
                            f"No expected andamentos structure found in {field_name} response"
                        )
                elif field_name == "informacoes":
                    # Check for expected informacoes structure
                    if not soup.find("div", {"id": "informacoes-completas"}):
                        is_404_error = True
                        self.logger.warning(
                            f"No expected informacoes structure found in {field_name} response"
                        )

            # Only extract content if not a 404 error
            if not is_404_error:
                # Extract content based on field name
                if field_name == "partes":
                    item["partes"] = self.extract_partes(soup)
                elif field_name == "andamentos":
                    item["andamentos"] = self.extract_andamentos(soup)
                elif field_name == "informacoes":
                    item["informacoes"] = self.extract_informacoes(soup)
                elif field_name == "decisoes":
                    item["decisoes"] = self.extract_decisoes(soup)
                elif field_name == "sessao":
                    item["sessao"] = self.extract_sessao(soup)
                elif field_name == "deslocamentos":
                    item["deslocamentos"] = self.extract_deslocamentos(soup)
                elif field_name == "peticoes":
                    item["peticoes"] = self.extract_peticoes(soup)
                elif field_name == "recursos":
                    item["recursos"] = self.extract_recursos(soup)
                elif field_name == "pautas":
                    item["pautas"] = self.extract_pautas(soup)
            else:
                # Mark as error in the item
                if f"ajax_error_{field_name}" not in item:
                    item[f"ajax_error_{field_name}"] = "404 or error response"
        else:
            self.logger.warning(f"Failed to load {field_name}: {response.status}")
            if f"ajax_error_{field_name}" not in item:
                item[f"ajax_error_{field_name}"] = f"HTTP {response.status}"

        # Track completion of AJAX requests
        if "ajax_completed" not in item:
            item["ajax_completed"] = []

        item["ajax_completed"].append(field_name)

        # Check if all AJAX requests are completed
        expected_ajax_fields = [
            "partes",
            "andamentos",
            "informacoes",
            "decisoes",
            "sessao",
            "deslocamentos",
            "peticoes",
            "recursos",
            "pautas",
        ]
        if len(item["ajax_completed"]) >= len(expected_ajax_fields):
            # All AJAX requests completed, yield the final item
            self.logger.info(f"All AJAX requests completed for process {item['processo_id']}")
            yield item
        else:
            # Still waiting for more AJAX requests
            self.logger.info(
                f"Completed {len(item['ajax_completed'])}/{len(expected_ajax_fields)} AJAX requests for process {item['processo_id']}"
            )
            # Don't yield yet, wait for more requests

    def parse(self, response: Response) -> Iterator[STFCaseItem]:
        # Parse HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        # Create STF case item
        item = STFCaseItem()

        # ids
        item["processo_id"] = response.meta["numero"]
        item["incidente"] = extract_incidente(soup)
        item["numero_unico"] = extract_numero_unico(soup)

        # classificacao
        item["classe"] = extract_classe(soup)
        item["liminar"] = extract_liminar(soup)
        item["tipo_processo"] = extract_tipo_processo(soup)

        # detalhes
        item["origem"] = extract_origem(soup)
        item["relator"] = extract_relator(soup)
        item["liminar"] = extract_liminar(soup)
        item["data_protocolo"] = extract_data_protocolo(soup)
        item["origem_orgao"] = extract_origem_orgao(soup)
        item["autor1"] = extract_autor1(soup)
        item["assuntos"] = extract_assuntos(soup)

        # metadados
        item["status"] = response.status
        # Don't store large HTML content to avoid memory issues
        item["extraido"] = datetime.datetime.now().isoformat() + "Z"

        yield item

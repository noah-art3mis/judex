import datetime
import json
import re
import time
from collections.abc import Iterator

import scrapy
from bs4 import BeautifulSoup
from scrapy.http import Response

from ..items import STFCaseItem
from ..types import is_valid_case_type, validate_case_type


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
            
            # Set proper headers for the initial request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Sec-GPC': '1',
                'Priority': 'u=0, i',
            }
            
            yield scrapy.Request(
                url=url,
                callback=self.parse_main_page,
                headers=headers,
                meta={"numero": numero},
            )

    def parse_main_page(self, response: Response) -> Iterator[scrapy.Request]:
        """Parse the main page and extract incidente number, then make AJAX requests"""
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract incidente number from the page
        incidente = self.extract_incidente(soup)
        if not incidente:
            self.logger.error(f"Could not extract incidente number from {response.url}")
            return
        
        # Create the main item with basic info
        item = STFCaseItem()
        item["processo_id"] = response.meta["numero"]
        item["incidente"] = incidente
        item["numero_unico"] = self.extract_numero_unico(soup)
        item["classe"] = self.extract_classe(soup)
        item["liminar"] = self.extract_liminar(soup)
        item["tipo_processo"] = self.extract_tipo_processo(soup)
        item["origem"] = self.extract_origem(soup)
        item["relator"] = self.extract_relator(soup)
        item["data_protocolo"] = self.extract_data_protocolo(soup)
        item["origem_orgao"] = self.extract_origem_orgao(soup)
        item["autor1"] = self.extract_autor1(soup)
        item["assuntos"] = self.extract_assuntos(soup)
        item["status"] = response.status
        item["html"] = response.text
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
        
        # Extract cookies from the response and merge with request cookies
        response_cookies = {}
        for cookie in response.headers.getlist('Set-Cookie'):
            # Parse Set-Cookie header: "name=value; Path=/; HttpOnly"
            cookie_parts = cookie.decode('utf-8').split(';')[0]
            if '=' in cookie_parts:
                name, value = cookie_parts.split('=', 1)
                response_cookies[name.strip()] = value.strip()
        
        # Merge response cookies with request cookies
        all_cookies = {}
        if response.request.cookies:
            if isinstance(response.request.cookies, dict):
                all_cookies.update(response.request.cookies)
            else:
                # Handle other cookie formats
                try:
                    for cookie in response.request.cookies:
                        if hasattr(cookie, 'name') and hasattr(cookie, 'value'):
                            all_cookies[cookie.name] = cookie.value
                except (TypeError, AttributeError):
                    pass
        
        all_cookies.update(response_cookies)
        
        # Also extract cookies from the response's cookies attribute
        try:
            if hasattr(response, 'cookies') and response.cookies:
                for cookie in response.cookies:
                    if hasattr(cookie, 'name') and hasattr(cookie, 'value'):
                        all_cookies[cookie.name] = cookie.value
        except (TypeError, AttributeError):
            pass
        
        
        # Set up headers for AJAX requests
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
        try:
            if response.request.headers:
                ua_header = response.request.headers.get('User-Agent')
                if ua_header:
                    if isinstance(ua_header, bytes):
                        user_agent = ua_header.decode('utf-8')
                    else:
                        user_agent = ua_header
        except (TypeError, AttributeError):
            pass
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Connection': 'keep-alive',
            'Referer': response.url,
            'Origin': 'https://portal.stf.jus.br',
            'X-Requested-With': 'XMLHttpRequest',
            'DNT': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-GPC': '1',
            'TE': 'trailers',
        }
        
        # Make requests to all AJAX endpoints with session information
        # Add small delays to avoid rate limiting
        for i, (field_name, ajax_url) in enumerate(ajax_endpoints):
            # Add delay between requests (except for the first one)
            if i > 0:
                time.sleep(0.5)  # 500ms delay between requests
            
            yield scrapy.Request(
                url=ajax_url,
                callback=self.parse_ajax_response,
                headers=headers,
                cookies=all_cookies,
                meta={
                    **meta,
                    "ajax_field": field_name,
                },
                dont_filter=True,  # Allow duplicate requests
            )

    def parse_ajax_response(self, response: Response) -> Iterator[STFCaseItem]:
        """Parse AJAX response and update the item"""
        item = response.meta["item"]
        field_name = response.meta["ajax_field"]
        
        # Debug: Log the actual response content
        self.logger.info(f"AJAX {field_name} response length: {len(response.text)}")
        self.logger.info(f"AJAX {field_name} response preview: {response.text[:200]}")
        
        # Store raw HTML for debugging
        if f"ajax_html_{field_name}" not in item:
            item[f"ajax_html_{field_name}"] = response.text
        
        # Check for 404 error indicators
        is_404_error = False
        if response.status == 404:
            is_404_error = True
            self.logger.warning(f"404 error for {field_name}: {response.url}")
        elif response.status == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Check for common 404 error indicators in HTML
            error_indicators = [
                "404", "Not Found", "Página não encontrada", "Erro 404",
                "The requested URL was not found", "File not found",
                "Página não existe", "Acesso negado", "Forbidden"
            ]
            
            page_text = soup.get_text().lower()
            for indicator in error_indicators:
                if indicator.lower() in page_text:
                    is_404_error = True
                    self.logger.warning(f"404 error indicator '{indicator}' found in {field_name} response")
                    break
            
            # Check for empty or minimal content
            if len(response.text.strip()) < 50:
                is_404_error = True
                self.logger.warning(f"Very short response for {field_name}: {len(response.text)} characters")
            
            # Check for specific error containers
            error_containers = soup.find_all(["div", "section", "main"], class_=re.compile(r"error|404|not-found", re.I))
            if error_containers:
                is_404_error = True
                self.logger.warning(f"Error container found in {field_name} response")
            
            # Check for valid content structure based on field type
            if not is_404_error:
                if field_name == "partes":
                    # Check for expected partes structure
                    if not soup.find("div", {"id": "todas-partes"}) and not soup.find("div", {"id": "partes-resumidas"}):
                        is_404_error = True
                        self.logger.warning(f"No expected partes structure found in {field_name} response")
                elif field_name == "andamentos":
                    # Check for expected andamentos structure
                    if not soup.find("div", class_="processo-andamentos"):
                        is_404_error = True
                        self.logger.warning(f"No expected andamentos structure found in {field_name} response")
                elif field_name == "informacoes":
                    # Check for expected informacoes structure
                    if not soup.find("div", {"id": "informacoes-completas"}):
                        is_404_error = True
                        self.logger.warning(f"No expected informacoes structure found in {field_name} response")
            
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
        expected_ajax_fields = ["partes", "andamentos", "informacoes", "decisoes", "sessao", "deslocamentos", "peticoes", "recursos", "pautas"]
        if len(item["ajax_completed"]) >= len(expected_ajax_fields):
            # All AJAX requests completed, yield the final item
            self.logger.info(f"All AJAX requests completed for process {item['processo_id']}")
            yield item
        else:
            # Still waiting for more AJAX requests
            self.logger.info(f"Completed {len(item['ajax_completed'])}/{len(expected_ajax_fields)} AJAX requests for process {item['processo_id']}")
            # Don't yield yet, wait for more requests

    def parse(self, response: Response) -> Iterator[STFCaseItem]:
        # Parse HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        # Create STF case item
        item = STFCaseItem()

        # ids
        item["processo_id"] = response.meta["numero"]
        item["incidente"] = self.extract_incidente(soup)
        item["numero_unico"] = self.extract_numero_unico(soup)

        # classificacao
        item["classe"] = self.extract_classe(soup)
        item["liminar"] = self.extract_liminar(soup)
        item["tipo_processo"] = self.extract_tipo_processo(soup)

        # detalhes
        item["origem"] = self.extract_origem(soup)
        item["relator"] = self.extract_relator(soup)
        item["liminar"] = self.extract_liminar(soup)
        item["data_protocolo"] = self.extract_data_protocolo(soup)
        item["origem_orgao"] = self.extract_origem_orgao(soup)
        item["autor1"] = self.extract_autor1(soup)
        item["assuntos"] = self.extract_assuntos(soup)

        # metadados
        item["status"] = response.status
        item["html"] = response.text or None
        item["extraido"] = datetime.datetime.now().isoformat() + "Z"

        yield item

    def extract_incidente(self, soup) -> int | None:
        """Extract incidente ID from hidden input"""
        try:
            incidente_input = soup.find("input", {"id": "incidente"})
            if incidente_input:
                value = incidente_input.get("value")
                return int(value) if value else None
            return None
        except:
            return None

    def extract_classe(self, soup: BeautifulSoup) -> str | None:
        """Extract case class (ADI, ADPF, etc.) and validate against enum"""
        try:
            # From the process title
            processo_titulo = soup.find("div", class_="processo-titulo")
            if processo_titulo:
                classe_text = processo_titulo.get_text().strip()
                # Extract class from text like "ADI 4436"
                classe = classe_text.split()[0] if classe_text else None

                # Validate the extracted class
                if classe:
                    if is_valid_case_type(classe):
                        return classe
                    else:
                        # If not found in set, return the original value but log a warning
                        self.logger.warning(f"Unknown case type extracted: '{classe}'")
                        return classe
                return classe
            return None
        except Exception as e:
            self.logger.error(f"Error extracting classe: {e}")
            return None


    def extract_tipo_processo(self, soup: BeautifulSoup) -> str | None:
        """Extract process type from badges"""
        try:
            # From badges or process type indicators
            badges = soup.find_all("span", class_="badge")
            if badges:
                # Return the first badge (usually "Processo Eletrônico")
                return badges[0].get_text().strip()
            return None
        except:
            return None

    def extract_numero_unico(self, soup: BeautifulSoup) -> str | None:
        """Extract unique process number"""
        try:
            # From the process number field
            processo_rotulo = soup.find("div", class_="processo-rotulo")
            if processo_rotulo:
                text = processo_rotulo.get_text().strip()
                # Remove "Número Único: " prefix if present
                if "Número Único:" in text:
                    return text.split("Número Único:")[1].strip()
                return text
            return None
        except:
            return None

    def extract_origem(self, soup: BeautifulSoup) -> str | None:
        """Extract origin information"""
        try:
            # Look for origin information in the process data section
            # The HTML structure shows: <div class="processo-dados"><a href="#" data-toggle="tooltip" title="...">Origem:</a>&nbsp;<span id="descricao-procedencia"></span></div>
            processo_dados = soup.find("div", class_="processo-dados")
            if processo_dados:
                # Look for the span with id="descricao-procedencia"
                origem_span = processo_dados.find("span", {"id": "descricao-procedencia"})
                if origem_span:
                    return origem_span.get_text().strip()
                # Fallback: look for text after "Origem:"
                origem_text = processo_dados.get_text()
                if "Origem:" in origem_text:
                    origem = origem_text.split("Origem:")[1].strip()
                    return origem
            return None
        except:
            return None

    def extract_relator(self, soup: BeautifulSoup) -> str | None:
        """Extract relator information"""
        try:
            # Look for relator information in the process data section
            # The HTML structure shows: <div class="processo-dados">Relator(a):  </div>
            processo_dados = soup.find("div", class_="processo-dados")
            if processo_dados:
                # Look for text containing "Relator"
                relator_text = processo_dados.get_text()
                if "Relator" in relator_text:
                    # Extract text after "Relator(a):"
                    if "Relator(a):" in relator_text:
                        relator = relator_text.split("Relator(a):")[1].strip()
                        # Remove "(a): MIN." prefix if present
                        if relator.startswith("(a): MIN."):
                            relator = relator.replace("(a): MIN.", "").strip()
                        return relator if relator else None
                    elif "Relator:" in relator_text:
                        relator = relator_text.split("Relator:")[1].strip()
                        # Remove "(a): MIN." prefix if present
                        if relator.startswith("(a): MIN."):
                            relator = relator.replace("(a): MIN.", "").strip()
                        return relator if relator else None

            # Fallback: search for any div containing "Relator"
            relator_elements = soup.find_all("div")
            for element in relator_elements:
                if element.string and "Relator" in element.string:
                    relator_element = element
                    break
            else:
                relator_element = None
            if relator_element:
                relator_text = relator_element.get_text()
                if "Relator" in relator_text:
                    relator = relator_text.split("Relator")[1].strip()
                    # Remove "(a): MIN." prefix if present
                    if relator.startswith("(a): MIN."):
                        relator = relator.replace("(a): MIN.", "").strip()
                    return relator if relator else None
            return None
        except:
            return None

    def extract_liminar(self, soup: BeautifulSoup) -> str | None:
        """Extract liminar information"""
        try:
            # Look for "Medida Liminar" in badges or text
            badges = soup.find_all("span", class_="badge")
            for badge in badges:
                if "liminar" in badge.get_text().lower():
                    return badge.get_text().strip()

            # Look for liminar in process title
            processo_titulo = soup.find("div", class_="processo-titulo")
            if processo_titulo and "liminar" in processo_titulo.get_text().lower():
                return "Medida Liminar"
            return None
        except:
            return None

    def extract_data_protocolo(self, soup: BeautifulSoup) -> str | None:
        """Extract protocol date"""
        try:
            # Look for date patterns in process information
            date_pattern = r"\d{2}/\d{2}/\d{4}"
            text_elements = soup.find_all(text=re.compile(date_pattern))
            for text in text_elements:
                if (
                    text
                    and isinstance(text, str)
                    and ("protocolo" in text.lower() or "data" in text.lower())
                ):
                    return text.strip()
            return None
        except:
            return None

    def extract_origem_orgao(self, soup: BeautifulSoup) -> str | None:
        """Extract origin organ"""
        try:
            # Look for origin organ information
            orgao_elements = soup.find_all("div")
            for element in orgao_elements:
                if element.string and "Órgão" in element.string:
                    orgao_element = element
                    break
            else:
                orgao_element = None
            if orgao_element:
                return orgao_element.get_text().strip()
            return None
        except:
            return None

    def extract_autor1(self, soup: BeautifulSoup) -> str | None:
        """Extract first author/plaintiff"""
        try:
            # From the parties section
            resumo_partes = soup.find("div", class_="resumo-partes")
            if resumo_partes:
                autor_text = resumo_partes.get_text()
                # Extract first author from the parties list
                if "Autor" in autor_text:
                    autor = autor_text.split("Autor")[1].split()[0]
                    return autor
            return None
        except:
            return None

    def extract_assuntos(self, soup: BeautifulSoup) -> list[str]:
        """Extract subjects/topics"""
        try:
            # From the subjects section
            assuntos_elements = soup.find_all("div", class_="assunto")
            assuntos_list = [assunto.get_text().strip() for assunto in assuntos_elements]
            return assuntos_list
        except:
            return []

    def extract_liminar_info(self, soup: BeautifulSoup) -> list[str]:
        """Extract meaningful information from nome_processo field"""
        try:
            # Extract nome_processo from the soup
            processo_titulo = soup.find("div", class_="processo-titulo")
            if not processo_titulo:
                return []
            
            nome_processo = processo_titulo.get_text().strip()
            if not nome_processo:
                return []
            
            # Clean up the text - remove extra whitespace and normalize
            cleaned = re.sub(r'\r\n\s+', '\n', nome_processo)
            cleaned = re.sub(r'\s+', ' ', cleaned.strip())
            
            # Split by newlines to get individual lines
            lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
            
            result = []
            
            # Look for specific patterns and extract meaningful information
            for line in lines:
                line_upper = line.upper()
                
                # Extract process type (ADI, etc.) - but don't add to result yet
                if re.match(r'^ADI\s*\d+', line_upper):
                    # Extract the ADI number but don't add it to the main result
                    # as it's not one of the requested output items
                    pass
                
                # Check for "Processo Eletrônico" - convert to meaningful status
                if 'PROCESSO ELETRÔNICO' in line_upper or 'PROCESSO ELETRONICO' in line_upper:
                    result.append('CONVERTIDO EM PROCESSO ELETRÔNICO')
                
                # Check for "Medida Liminar"
                if 'MEDIDA LIMINAR' in line_upper:
                    result.append('MEDIDA LIMINAR')
                
                # Check for "Público" - this might indicate public access
                if 'PÚBLICO' in line_upper or 'PUBLICO' in line_upper:
                    result.append('PROCESSO PÚBLICO')
            
            # If no specific patterns found, try to extract meaningful words
            if not result:
                # Look for capitalized words that might be meaningful
                words = re.findall(r'\b[A-Z][A-Z\s]+\b', cleaned)
                for word in words:
                    word_clean = word.strip()
                    if len(word_clean) > 3:  # Only include words longer than 3 characters
                        result.append(word_clean)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing nome_processo: {e}")
            return []

    # AJAX extraction methods
    def extract_partes(self, soup: BeautifulSoup) -> list[dict]:
        """Extract parties from partes section"""
        try:
            partes = []
            partes_section = soup.find("div", {"id": "todas-partes"})
            if partes_section:
                # Extract each party - the structure is:
                # <div class="processo-partes lista-dados m-l-16 p-t-0">
                #   <div class="detalhe-parte">REQTE.(S)</div>
                #   <div class="nome-parte">FEDERACAO NACIONAL DOS ESTABELECIMENTOS DE ENSINO - FENEN</div>
                # </div>
                party_divs = partes_section.find_all("div", class_="processo-partes")
                for party_div in party_divs:
                    party_type = party_div.find("div", class_="detalhe-parte")
                    party_name = party_div.find("div", class_="nome-parte")
                    
                    if party_type and party_name:
                        partes.append({
                            "tipo": party_type.get_text().strip(),
                            "nome": party_name.get_text().strip()
                        })
            return partes
        except Exception as e:
            self.logger.error(f"Error extracting partes: {e}")
            return []

    def extract_andamentos(self, soup: BeautifulSoup) -> list[dict]:
        """Extract proceedings from andamentos section"""
        try:
            andamentos = []
            andamentos_section = soup.find("div", class_="processo-andamentos")
            if andamentos_section:
                # Extract each proceeding - the structure is:
                # <li>
                #   <div class="andamento-item">
                #     <div class="andamento-inner">
                #       <div class="andamento-detalhe">
                #         <div class="andamento-data">23/01/2007</div>
                #         <h5 class="andamento-nome">BAIXA AO ARQUIVO DO STF</h5>
                #         <div class="col-md-9 p-0">GUIA Nº 5509/1997 (BAIXADO EM 10/12/1997).</div>
                #       </div>
                #     </div>
                #   </div>
                # </li>
                andamento_items = andamentos_section.find_all("li")
                for item in andamento_items:
                    andamento_item = item.find("div", class_="andamento-item")
                    if andamento_item:
                        andamento_inner = andamento_item.find("div", class_="andamento-inner")
                        if andamento_inner:
                            andamento_detalhe = andamento_inner.find("div", class_="andamento-detalhe")
                            if andamento_detalhe:
                                data_elem = andamento_detalhe.find("div", class_="andamento-data")
                                nome_elem = andamento_detalhe.find("h5", class_="andamento-nome")
                                
                                # Get the description from the col-md-9 div
                                descricao_elem = andamento_detalhe.find("div", {"class": ["col-md-9", "p-0"]})
                                if not descricao_elem:
                                    # Try alternative selector
                                    # Try to find any div with text content
                                    descricao_elem = andamento_detalhe.find("div")
                                
                                data = data_elem.get_text().strip() if data_elem else ""
                                nome = nome_elem.get_text().strip() if nome_elem else ""
                                descricao = descricao_elem.get_text().strip() if descricao_elem else ""
                                
                                if data or nome:
                                    andamentos.append({
                                        "data": data,
                                        "nome": nome,
                                        "descricao": descricao
                                    })
            return andamentos
        except Exception as e:
            self.logger.error(f"Error extracting andamentos: {e}")
            return []

    def extract_decisoes(self, soup: BeautifulSoup) -> list[dict]:
        """Extract decisions from decisoes section"""
        try:
            decisoes = []
            decisoes_section = soup.find("div", class_="processo-andamentos")
            if decisoes_section:
                # Extract each decision - same structure as andamentos
                andamento_items = decisoes_section.find_all("div", class_="andamento-item")
                for item in andamento_items:
                    andamento_inner = item.find("div", class_="andamento-inner")
                    if andamento_inner:
                        andamento_detalhe = andamento_inner.find("div", class_="andamento-detalhe")
                        if andamento_detalhe:
                            data_elem = andamento_detalhe.find("div", class_="andamento-data")
                            nome_elem = andamento_detalhe.find("h5", class_="andamento-nome")
                            
                            # Get the description from the col-md-9 div
                            descricao_elem = andamento_detalhe.find("div", {"class": ["col-md-9", "p-0"]})
                            if not descricao_elem:
                                # Try alternative selector
                                # Try to find any div with text content
                                descricao_elem = andamento_detalhe.find("div")
                            
                            data = data_elem.get_text().strip() if data_elem else ""
                            nome = nome_elem.get_text().strip() if nome_elem else ""
                            descricao = descricao_elem.get_text().strip() if descricao_elem else ""
                            
                            if data or nome:
                                decisoes.append({
                                    "data": data,
                                    "nome": nome,
                                    "descricao": descricao
                                })
            return decisoes
        except Exception as e:
            self.logger.error(f"Error extracting decisoes: {e}")
            return []

    def extract_deslocamentos(self, soup: BeautifulSoup) -> list[dict]:
        """Extract transfers from deslocamentos section"""
        try:
            deslocamentos = []
            # The structure is:
            # <div class="col-md-12 lista-dados p-r-0 p-l-0">
            #   <div class="lista-dados__col col-md-9">
            #     <div class="processo-detalhes-bold">COORDENADORIA DE GESTÃO DA INFORMAÇÃO, MEMÓRIA INSTITUCIONAL E MUSEU</div>
            #     <div class="lista-dados__col--detalhes">
            #       <span class="processo-detalhes">Enviado por COORDENADORIA DE MEMÓRIA E GESTÃO DOCUMENTAL em 30/01/2021</span>
            #     </div>
            #   </div>
            #   <div class="lista-dados__col col-md-3">
            #     <div class="col-md-12 text-right">
            #       <span class="processo-detalhes">Guia 6/2021</span>
            #     </div>
            #     <div class="col-md-12 text-right">
            #       <span class="processo-detalhes bg-font-success">Recebido em 30/01/2021</span>
            #     </div>
            #   </div>
            # </div>
            deslocamento_items = soup.find_all("div", {"class": ["col-md-12", "lista-dados"]})
            for item in deslocamento_items:
                # Extract the main info
                main_col = item.find("div", {"class": ["lista-dados__col", "col-md-9"]})
                if main_col:
                    nome_elem = main_col.find("span", class_="processo-detalhes-bold")
                    detalhes_elem = main_col.find("div", class_="lista-dados__col--detalhes")
                    
                    # Extract the right side info
                    right_col = item.find("div", {"class": ["lista-dados__col", "col-md-3"]})
                    guia_elem = None
                    recebido_elem = None
                    if right_col:
                        guia_elem = right_col.find("span", class_="processo-detalhes")
                        recebido_elem = right_col.find("span", {"class": ["processo-detalhes", "bg-font-success"]})
                    
                    nome = nome_elem.get_text().strip() if nome_elem else ""
                    detalhes = detalhes_elem.get_text().strip() if detalhes_elem else ""
                    guia = guia_elem.get_text().strip() if guia_elem else ""
                    recebido = recebido_elem.get_text().strip() if recebido_elem else ""
                    
                    if nome:
                        deslocamentos.append({
                            "nome": nome,
                            "detalhes": detalhes,
                            "guia": guia,
                            "recebido": recebido
                        })
            return deslocamentos
        except Exception as e:
            self.logger.error(f"Error extracting deslocamentos: {e}")
            return []

    def extract_peticoes(self, soup: BeautifulSoup) -> list[dict]:
        """Extract petitions from peticoes section"""
        try:
            peticoes = []
            # The structure is:
            # <div class="col-md-12 lista-dados">
            #   <div class="col-6">
            #     <span class="processo-detalhes-bold">27885/1992</span>
            #     <span class="processo-detalhes">Peticionado em 28/09/1992</span>
            #   </div>
            #   <div class="col-6 d-flex justify-content-end">
            #     <span class="processo-detalhes">Recebido em 06/10/1992 00:00:00 por GABINETE DO DIRETOR DO SERVICO DO PROCESSO JUDICIARIO</span>
            #   </div>
            # </div>
            peticao_items = soup.find_all("div", {"class": ["col-md-12", "lista-dados"]})
            for item in peticao_items:
                left_col = item.find("div", class_="col-6")
                right_col = item.find("div", {"class": ["col-6", "d-flex"]})
                
                if left_col:
                    numero_elem = left_col.find("span", class_="processo-detalhes-bold")
                    data_elem = left_col.find("span", class_="processo-detalhes")
                    
                    recebido_elem = None
                    if right_col:
                        recebido_elem = right_col.find("span", class_="processo-detalhes")
                    
                    numero = numero_elem.get_text().strip() if numero_elem else ""
                    data = data_elem.get_text().strip() if data_elem else ""
                    recebido = recebido_elem.get_text().strip() if recebido_elem else ""
                    
                    if numero:
                        peticoes.append({
                            "numero": numero,
                            "data": data,
                            "recebido": recebido
                        })
            return peticoes
        except Exception as e:
            self.logger.error(f"Error extracting peticoes: {e}")
            return []

    def extract_recursos(self, soup: BeautifulSoup) -> list[dict]:
        """Extract appeals from recursos section"""
        try:
            recursos = []
            # The recursos section returns "null" in the example, so we check for that
            text_content = soup.get_text().strip()
            if text_content and text_content.lower() != "null":
                # If there's actual content, try to extract it
                # This would need to be updated based on actual structure when content exists
                pass
            return recursos
        except Exception as e:
            self.logger.error(f"Error extracting recursos: {e}")
            return []

    def extract_pautas(self, soup: BeautifulSoup) -> list[dict]:
        """Extract agendas from pautas section"""
        try:
            pautas = []
            # The pautas section is empty in the example, but has the structure:
            # <div class="processo-andamentos m-t-8"></div>
            pautas_section = soup.find("div", class_="processo-andamentos")
            if pautas_section:
                # If there's actual content, try to extract it
                # This would need to be updated based on actual structure when content exists
                pass
            return pautas
        except Exception as e:
            self.logger.error(f"Error extracting pautas: {e}")
            return []

    def extract_informacoes(self, soup: BeautifulSoup) -> dict:
        """Extract information from informacoes section"""
        try:
            informacoes = {}
            info_section = soup.find("div", {"id": "informacoes-completas"})
            if info_section:
                # Extract subject
                assunto_elem = info_section.find("li")
                if assunto_elem:
                    informacoes["assunto"] = assunto_elem.get_text().strip()
                
                # Extract protocol date - look for "Data de Protocolo:" text
                protocolo_elem = None
                for div in info_section.find_all("div"):
                    if div.string and "Data de Protocolo:" in div.string:
                        protocolo_elem = div
                        break
                if protocolo_elem:
                    parent = protocolo_elem.parent
                    if parent:
                        next_div = parent.find_next_sibling("div")
                        if next_div:
                            informacoes["data_protocolo"] = next_div.get_text().strip()
                
                # Extract origin - look for "Órgão de Origem:" text
                origem_elem = None
                for div in info_section.find_all("div"):
                    if div.string and "Órgão de Origem:" in div.string:
                        origem_elem = div
                        break
                if origem_elem:
                    parent = origem_elem.parent
                    if parent:
                        next_div = parent.find_next_sibling("div")
                        if next_div:
                            informacoes["origem_orgao"] = next_div.get_text().strip()
                
                # Extract origin description - look for "Origem:" text
                origem_desc_elem = None
                for div in info_section.find_all("div"):
                    if div.string and "Origem:" in div.string:
                        origem_desc_elem = div
                        break
                if origem_desc_elem:
                    parent = origem_desc_elem.parent
                    if parent:
                        next_div = parent.find_next_sibling("div")
                        if next_div:
                            informacoes["origem"] = next_div.get_text().strip()
                
                # Extract number of origin - look for "Número de Origem:" text
                numero_origem_elem = None
                for div in info_section.find_all("div"):
                    if div.string and "Número de Origem:" in div.string:
                        numero_origem_elem = div
                        break
                if numero_origem_elem:
                    parent = numero_origem_elem.parent
                    if parent:
                        next_div = parent.find_next_sibling("div")
                        if next_div:
                            informacoes["numero_origem"] = next_div.get_text().strip()
                
                # Extract volumes, pages, and attachments
                volumes_elem = info_section.find("div", class_="numero")
                if volumes_elem:
                    informacoes["volumes"] = volumes_elem.get_text().strip()
                
                # Look for folhas (pages)
                folhas_elem = None
                for div in info_section.find_all("div"):
                    if div.string and "Folhas" in div.string:
                        folhas_elem = div
                        break
                if folhas_elem:
                    parent = folhas_elem.parent
                    if parent:
                        numero_elem = parent.find("div", class_="numero")
                        if numero_elem:
                            informacoes["folhas"] = numero_elem.get_text().strip()
                
                # Look for apensos (attachments)
                apensos_elem = None
                for div in info_section.find_all("div"):
                    if div.string and "Apensos" in div.string:
                        apensos_elem = div
                        break
                if apensos_elem:
                    parent = apensos_elem.parent
                    if parent:
                        numero_elem = parent.find("div", class_="numero")
                        if numero_elem:
                            informacoes["apensos"] = numero_elem.get_text().strip()
            
            return informacoes
        except Exception as e:
            self.logger.error(f"Error extracting informacoes: {e}")
            return {}

    def extract_sessao(self, soup: BeautifulSoup) -> dict:
        """Extract session information from sessao section"""
        try:
            sessao = {}
            # The sessao section contains JavaScript that generates content dynamically
            # We can extract the static parts and note that dynamic content requires JavaScript execution
            
            # Look for any static content that might be present
            votacoes_elem = soup.find("div", {"id": "votacoes"})
            if votacoes_elem:
                sessao["votacoes"] = votacoes_elem.get_text().strip()
            
            votacoes_tema_elem = soup.find("div", {"id": "votacoesTema"})
            if votacoes_tema_elem:
                sessao["votacoes_tema"] = votacoes_tema_elem.get_text().strip()
            
            # Check if there's a "Sem sessão virtual" message
            sem_julgamento_elem = soup.find("div", {"id": "semJulgamento"})
            if sem_julgamento_elem:
                sessao["status"] = "Sem sessão virtual"
            
            return sessao
        except Exception as e:
            self.logger.error(f"Error extracting sessao: {e}")
            return {}

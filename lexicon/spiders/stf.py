import datetime
import json
import re
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
            url = (
                f"{base}/processos/listarProcessos.asp?classe={self.classe}&numeroProcesso={numero}"
            )
            yield scrapy.Request(url=url, callback=self.parse, meta={"numero": numero})

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

    def extract_liminar(self, soup: BeautifulSoup) -> list[str]:
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

import scrapy
import json
import datetime
from bs4 import BeautifulSoup
import re
from typing import Optional
from ..types import validate_case_type, is_valid_case_type
from typing import Optional


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

        # Validate the case class against the enum
        self.classe = validate_case_type(classe)

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
            yield scrapy.Request(url=url, callback=self.parse, meta={'numero': numero})

    def parse(self, response):
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract basic case information
        case_data = {
            "status": response.status,
            "processo_id": response.meta['numero'],
            "incidente": self.extract_incidente(soup),
            "numero_unico": self.extract_numero_unico(soup),
            "classe": self.extract_classe(soup),
            "classe_extenso": self.extract_classe_extenso(soup),
            "nome_processo": self.extract_nome_processo(soup),
            "tipo_processo": self.extract_tipo_processo(soup),
            "origem": self.extract_origem(soup),
            "relator": self.extract_relator(soup),
            "html": response.text or None,
            "extraido": datetime.datetime.now().isoformat() + "Z",
        }
        
        yield case_data

    def extract_incidente(self, soup) -> Optional[int]:
        """Extract incidente ID from hidden input"""
        try:
            incidente_input = soup.find('input', {'id': 'incidente'})
            if incidente_input:
                value = incidente_input.get('value')
                return int(value) if value else None
            return None
        except:
            return None

    def extract_classe(self, soup) -> Optional[str]:
        """Extract case class (ADI, ADPF, etc.) and validate against enum"""
        try:
            # From the process title
            processo_titulo = soup.find('div', class_='processo-titulo')
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

    def extract_classe_extenso(self, soup):
        """Extract full class name"""
        try:
            # From the process class description
            classe_extenso = soup.find('div', class_='processo-classe')
            if classe_extenso:
                return classe_extenso.get_text().strip()
            return None
        except:
            return None

    def extract_nome_processo(self, soup):
        """Extract process name"""
        try:
            # From the process title
            processo_titulo = soup.find('div', class_='processo-titulo')
            if processo_titulo:
                return processo_titulo.get_text().strip()
            return None
        except:
            return None

    def extract_tipo_processo(self, soup):
        """Extract process type from badges"""
        try:
            # From badges or process type indicators
            badges = soup.find_all('span', class_='badge')
            if badges:
                # Return the first badge (usually "Processo Eletrônico")
                return badges[0].get_text().strip()
            return None
        except:
            return None

    def extract_numero_unico(self, soup):
        """Extract unique process number"""
        try:
            # From the process number field
            processo_rotulo = soup.find('div', class_='processo-rotulo')
            if processo_rotulo:
                text = processo_rotulo.get_text().strip()
                # Remove "Número Único: " prefix if present
                if "Número Único:" in text:
                    return text.split("Número Único:")[1].strip()
                return text
            return None
        except:
            return None

    def extract_origem(self, soup):
        """Extract origin information"""
        try:
            # Look for origin information in the process data section
            # The HTML structure shows: <div class="processo-dados"><a href="#" data-toggle="tooltip" title="...">Origem:</a>&nbsp;<span id="descricao-procedencia"></span></div>
            processo_dados = soup.find('div', class_='processo-dados')
            if processo_dados:
                # Look for the span with id="descricao-procedencia"
                origem_span = processo_dados.find('span', {'id': 'descricao-procedencia'})
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

    def extract_relator(self, soup):
        """Extract relator information"""
        try:
            # Look for relator information in the process data section
            # The HTML structure shows: <div class="processo-dados">Relator(a):  </div>
            processo_dados = soup.find('div', class_='processo-dados')
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
            relator_element = soup.find('div', string=re.compile(r'Relator', re.IGNORECASE))
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
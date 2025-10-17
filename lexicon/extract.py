import re
from bs4 import BeautifulSoup
from lexicon.types import is_valid_case_type


def extract_incidente(soup) -> int | None:
    """Extract incidente ID from hidden input"""
    try:
        incidente_input = soup.find("input", {"id": "incidente"})
        if incidente_input:
            value = incidente_input.get("value")
            return int(value) if value else None
        return None
    except:
        return None


def extract_classe(soup: BeautifulSoup) -> str | None:
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
                    print.warning(f"Unknown case type extracted: '{classe}'")
                    return classe
            return classe
        return None
    except Exception as e:
        print.error(f"Error extracting classe: {e}")
        return None


def extract_tipo_processo(soup: BeautifulSoup) -> str | None:
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


def extract_numero_unico(soup: BeautifulSoup) -> str | None:
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


def extract_origem(soup: BeautifulSoup) -> str | None:
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


def extract_relator(soup: BeautifulSoup) -> str | None:
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


def extract_liminar(soup: BeautifulSoup) -> str | None:
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


def extract_data_protocolo(soup: BeautifulSoup) -> str | None:
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


def extract_origem_orgao(soup: BeautifulSoup) -> str | None:
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


def extract_autor1(soup: BeautifulSoup) -> str | None:
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


def extract_assuntos(soup: BeautifulSoup) -> list[str]:
    """Extract subjects/topics"""
    try:
        # From the subjects section
        assuntos_elements = soup.find_all("div", class_="assunto")
        assuntos_list = [assunto.get_text().strip() for assunto in assuntos_elements]
        return assuntos_list
    except:
        return []


def extract_liminar_info(soup: BeautifulSoup) -> list[str]:
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
        cleaned = re.sub(r"\r\n\s+", "\n", nome_processo)
        cleaned = re.sub(r"\s+", " ", cleaned.strip())

        # Split by newlines to get individual lines
        lines = [line.strip() for line in cleaned.split("\n") if line.strip()]

        result = []

        # Look for specific patterns and extract meaningful information
        for line in lines:
            line_upper = line.upper()

            # Extract process type (ADI, etc.) - but don't add to result yet
            if re.match(r"^ADI\s*\d+", line_upper):
                # Extract the ADI number but don't add it to the main result
                # as it's not one of the requested output items
                pass

            # Check for "Processo Eletrônico" - convert to meaningful status
            if "PROCESSO ELETRÔNICO" in line_upper or "PROCESSO ELETRONICO" in line_upper:
                result.append("CONVERTIDO EM PROCESSO ELETRÔNICO")

            # Check for "Medida Liminar"
            if "MEDIDA LIMINAR" in line_upper:
                result.append("MEDIDA LIMINAR")

            # Check for "Público" - this might indicate public access
            if "PÚBLICO" in line_upper or "PUBLICO" in line_upper:
                result.append("PROCESSO PÚBLICO")

        # If no specific patterns found, try to extract meaningful words
        if not result:
            # Look for capitalized words that might be meaningful
            words = re.findall(r"\b[A-Z][A-Z\s]+\b", cleaned)
            for word in words:
                word_clean = word.strip()
                if len(word_clean) > 3:  # Only include words longer than 3 characters
                    result.append(word_clean)

        return result

    except Exception as e:
        print.error(f"Error parsing nome_processo: {e}")
        return []


# AJAX extraction methods
def extract_partes(soup: BeautifulSoup) -> list[dict]:
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
                    partes.append(
                        {
                            "tipo": party_type.get_text().strip(),
                            "nome": party_name.get_text().strip(),
                        }
                    )
        return partes
    except Exception as e:
        print.error(f"Error extracting partes: {e}")
        return []


def extract_andamentos(soup: BeautifulSoup) -> list[dict]:
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
                            descricao_elem = andamento_detalhe.find(
                                "div", {"class": ["col-md-9", "p-0"]}
                            )
                            if not descricao_elem:
                                # Try alternative selector
                                # Try to find any div with text content
                                descricao_elem = andamento_detalhe.find("div")

                            data = data_elem.get_text().strip() if data_elem else ""
                            nome = nome_elem.get_text().strip() if nome_elem else ""
                            descricao = descricao_elem.get_text().strip() if descricao_elem else ""

                            if data or nome:
                                andamentos.append(
                                    {"data": data, "nome": nome, "descricao": descricao}
                                )
        return andamentos
    except Exception as e:
        print.error(f"Error extracting andamentos: {e}")
        return []


def extract_decisoes(soup: BeautifulSoup) -> list[dict]:
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
                        descricao_elem = andamento_detalhe.find(
                            "div", {"class": ["col-md-9", "p-0"]}
                        )
                        if not descricao_elem:
                            # Try alternative selector
                            # Try to find any div with text content
                            descricao_elem = andamento_detalhe.find("div")

                        data = data_elem.get_text().strip() if data_elem else ""
                        nome = nome_elem.get_text().strip() if nome_elem else ""
                        descricao = descricao_elem.get_text().strip() if descricao_elem else ""

                        if data or nome:
                            decisoes.append({"data": data, "nome": nome, "descricao": descricao})
        return decisoes
    except Exception as e:
        print.error(f"Error extracting decisoes: {e}")
        return []


def extract_deslocamentos(soup: BeautifulSoup) -> list[dict]:
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
                    recebido_elem = right_col.find(
                        "span", {"class": ["processo-detalhes", "bg-font-success"]}
                    )

                nome = nome_elem.get_text().strip() if nome_elem else ""
                detalhes = detalhes_elem.get_text().strip() if detalhes_elem else ""
                guia = guia_elem.get_text().strip() if guia_elem else ""
                recebido = recebido_elem.get_text().strip() if recebido_elem else ""

                if nome:
                    deslocamentos.append(
                        {"nome": nome, "detalhes": detalhes, "guia": guia, "recebido": recebido}
                    )
        return deslocamentos
    except Exception as e:
        print.error(f"Error extracting deslocamentos: {e}")
        return []


def extract_peticoes(soup: BeautifulSoup) -> list[dict]:
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
                    peticoes.append({"numero": numero, "data": data, "recebido": recebido})
        return peticoes
    except Exception as e:
        print.error(f"Error extracting peticoes: {e}")
        return []


def extract_recursos(soup: BeautifulSoup) -> list[dict]:
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
        print.error(f"Error extracting recursos: {e}")
        return []


def extract_pautas(soup: BeautifulSoup) -> list[dict]:
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
        print.error(f"Error extracting pautas: {e}")
        return []


def extract_informacoes(soup: BeautifulSoup) -> dict:
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
        print.error(f"Error extracting informacoes: {e}")
        return {}


def extract_sessao(soup: BeautifulSoup) -> dict:
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
        print.error(f"Error extracting sessao: {e}")
        return {}

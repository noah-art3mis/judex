import functools
import time
from typing import Any, Callable

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

# Optimized extractors for STF HTML structure


def track_extraction_timing(func: Callable) -> Callable:
    """Decorator to track extraction function timing using Scrapy stats"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Find spider instance from args
        spider = None
        for arg in args:
            if hasattr(arg, "crawler") and hasattr(arg, "logger"):
                spider = arg
                break

        if not spider:
            # If no spider found, just run the function without timing/stats
            return func(*args, **kwargs)

        # Get function name for stats
        func_name = func.__name__.replace("extract_", "")

        # Track timing
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            # Update stats
            if spider and hasattr(spider, "crawler") and spider.crawler:
                spider.crawler.stats.inc_value(f"extraction/{func_name}/success")
                spider.crawler.stats.set_value(
                    f"extraction/{func_name}/duration", round(duration, 2)
                )

            # Log timing
            if spider and hasattr(spider, "logger") and spider.logger:
                spider.logger.info(f"{func_name} extraction: {duration:.3f}s")

            return result

        except Exception as e:
            duration = time.time() - start_time

            # Update stats
            if spider and hasattr(spider, "crawler") and spider.crawler:
                spider.crawler.stats.inc_value(f"extraction/{func_name}/failed")
                spider.crawler.stats.set_value(
                    f"extraction/{func_name}/duration", round(duration, 2)
                )

            # Log timing and error
            if spider and hasattr(spider, "logger") and spider.logger:
                spider.logger.warning(
                    f"{func_name} extraction failed after {duration:.3f}s: {e}"
                )

            # Re-raise the exception
            raise

    return wrapper


def handle_extraction_errors(
    default_value: Any = None, log_errors: bool = True
) -> Callable:
    """
    Decorator to handle extraction errors with consistent error handling and stats tracking

    Args:
        default_value: Value to return when extraction fails
        log_errors: Whether to log errors (useful for debugging)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Find spider instance from args
            spider = None
            for arg in args:
                if hasattr(arg, "crawler") and hasattr(arg, "logger"):
                    spider = arg
                    break

            if not spider:
                # If no spider found, just run the function without error handling
                return func(*args, **kwargs)

            # Get function name for stats
            func_name = func.__name__.replace("extract_", "")

            try:
                result = func(*args, **kwargs)

                # Track success
                if spider and hasattr(spider, "crawler") and spider.crawler:
                    spider.crawler.stats.inc_value(f"extraction/{func_name}/success")

                return result

            except Exception as e:
                # Track failure
                if spider and hasattr(spider, "crawler") and spider.crawler:
                    spider.crawler.stats.inc_value(f"extraction/{func_name}/failed")
                    spider.crawler.stats.inc_value(
                        f"extraction/{func_name}/error_count"
                    )

                # Log error if enabled
                if (
                    log_errors
                    and spider
                    and hasattr(spider, "logger")
                    and spider.logger
                ):
                    spider.logger.warning(f"Could not extract {func_name}: {e}")

                # Return default value instead of raising
                return default_value

        return wrapper

    return decorator


@track_extraction_timing
@handle_extraction_errors(default_value=None, log_errors=True)
def extract_numero_unico(soup) -> str | None:
    """Extract numero_unico from .processo-rotulo element"""
    el = soup.select_one(".processo-rotulo")
    if not el:
        return None
    text = el.get_text(" ", strip=True)
    # Ex: "Número Único: 0004022-92.1988.0.01.0000"
    if "Número Único:" in text:
        return text.split("Número Único:")[1].strip()
    return None


@track_extraction_timing
@handle_extraction_errors(default_value=None, log_errors=True)
def extract_relator(soup) -> str | None:
    """Extract relator from .processo-dados elements"""
    for div in soup.select(".processo-dados"):
        text = div.get_text(" ", strip=True)
        if text.startswith("Relator(a):"):
            relator = text.split(":", 1)[1].strip()
            # Remove "MIN." prefix if present
            if relator.startswith("MIN. "):
                relator = relator[5:]  # Remove "MIN. " (5 characters)
            return relator
    return None


@track_extraction_timing
@handle_extraction_errors(default_value=None, log_errors=True)
def extract_tipo_processo(soup) -> str | None:
    """Extract meio from badge elements"""
    badges = [b.get_text(strip=True) for b in soup.select(".badge")]
    for badge in badges:
        if "Físico" in badge:
            return "Físico"
        elif "Eletrônico" in badge:
            return "Eletrônico"
    return None


@track_extraction_timing
@handle_extraction_errors(default_value=None, log_errors=True)
def extract_classe(soup) -> str | None:
    """Extract classe from .processo-dados elements"""
    for div in soup.select(".processo-dados"):
        text = div.get_text(" ", strip=True)
        if text.startswith("Classe:"):
            return text.split(":", 1)[1].strip()
    return None


@track_extraction_timing
@handle_extraction_errors(default_value=None, log_errors=True)
def extract_incidente(soup) -> str | None:
    """Extract incidente from .processo-dados elements"""
    for div in soup.select(".processo-dados"):
        text = div.get_text(" ", strip=True)
        if text.startswith("Incidente:"):
            return text.split(":", 1)[1].strip()
    return None


@track_extraction_timing
@handle_extraction_errors(default_value=None, log_errors=True)
def extract_origem(spider, driver: WebDriver, soup) -> str | None:
    """Extract origem from descricao-procedencia span"""
    try:
        element = driver.find_element(By.ID, "descricao-procedencia")
        return spider.clean_text(element.text)
    except Exception as e:
        spider.logger.warning(f"Could not extract origem: {e}")
        return None


@track_extraction_timing
@handle_extraction_errors(default_value=False, log_errors=True)
def extract_liminar(spider, driver: WebDriver, soup: BeautifulSoup) -> bool:
    """Extract liminar from bg-danger elements and return True if any found"""
    try:
        liminar_elements = driver.find_elements(By.CLASS_NAME, "bg-danger")

        # Return True if any liminar elements are found, False otherwise
        return len(liminar_elements) > 0
    except Exception as e:
        spider.logger.warning(f"Could not extract liminar: {e}")
        return False


@track_extraction_timing
@handle_extraction_errors(default_value=None, log_errors=True)
def extract_autor1(spider, driver: WebDriver, soup) -> str | None:
    """Extract autor1 using class selectors from backup"""
    try:
        partes_nome = driver.find_elements(By.CLASS_NAME, "nome-parte")
        if partes_nome:
            primeiro_autor = partes_nome[0].get_attribute("innerHTML")
            return spider.clean_text(primeiro_autor)
        return None
    except Exception as e:
        spider.logger.warning(f"Could not extract autor1: {e}")
        return None


@track_extraction_timing
@handle_extraction_errors(default_value=[], log_errors=True)
def extract_partes(spider, driver: WebDriver, soup) -> list:
    """Extract partes using updated CSS selectors for current STF website"""
    try:
        # Find the partes section
        partes_section = driver.find_element(By.ID, "resumo-partes")

        # Look for all divs with processo-partes class
        processo_partes = partes_section.find_elements(
            By.CSS_SELECTOR, "div[class*='processo-partes']"
        )

        partes_list: list[dict] = []
        for i, div in enumerate(processo_partes):
            # Extract text content
            text_content = div.text.strip()

            # Skip empty or header elements
            if not text_content or text_content in [
                "AUTOR(A/S)(ES)",
                "RÉU/RÉUS",
                "INTERESSADO(A/S)",
            ]:
                continue

            # Try to determine tipo and nome from the text
            # This is a heuristic approach - may need refinement based on actual data
            if "AUTOR" in text_content.upper():
                tipo = "AUTOR"
                nome = text_content.replace("AUTOR(A/S)(ES)", "").strip()
            elif "RÉU" in text_content.upper():
                tipo = "RÉU"
                nome = text_content.replace("RÉU/RÉUS", "").strip()
            elif "INTERESSADO" in text_content.upper():
                tipo = "INTERESSADO"
                nome = text_content.replace("INTERESSADO(A/S)", "").strip()
            else:
                # Default to 'PARTE' if we can't determine the type
                tipo = "PARTE"
                nome = text_content

            if nome:  # Only add if we have a name
                parte_data = {
                    "_index": len(partes_list) + 1,
                    "tipo": tipo,
                    "nome": nome,
                }
                partes_list.append(parte_data)

        return partes_list
    except Exception as e:
        spider.logger.warning(f"Could not extract partes: {e}")
        return []


@track_extraction_timing
@handle_extraction_errors(default_value=None, log_errors=True)
def extract_data_protocolo(spider, driver: WebDriver, soup) -> str | None:
    """Extract data_protocolo using XPath from backup and return Brazilian date format"""
    try:
        data_html = spider.get_element_by_xpath(
            driver, '//*[@id="informacoes-completas"]/div[2]/div[1]/div[2]/div[2]'
        )
        data_text = spider.clean_text(data_html)

        if not data_text:
            return None

        # Return Brazilian date format (DD/MM/YYYY) as expected by ground truth
        if "/" in data_text and len(data_text.split("/")) == 3:
            return data_text
        else:
            # If not in expected format, return as-is
            return data_text
    except (ValueError, IndexError):
        # If parsing fails, return original text
        return data_text
    except Exception:
        return None


@track_extraction_timing
@handle_extraction_errors(default_value=None, log_errors=True)
def extract_origem_orgao(spider, driver: WebDriver, soup) -> str | None:
    """Extract origem_orgao using XPath from backup"""
    try:
        orgao_html = spider.get_element_by_xpath(
            driver, '//*[@id="informacoes-completas"]/div[2]/div[1]/div[2]/div[4]'
        )
        return spider.clean_text(orgao_html)
    except Exception:
        return None


@track_extraction_timing
@handle_extraction_errors(default_value="FISICO", log_errors=True)
def extract_meio(spider, driver: WebDriver, soup) -> str:
    """Extract meio (process type) from page"""
    try:
        # Look for badges that indicate electronic process
        badges = soup.find_all("span", class_="badge")
        for badge in badges:
            if "ELETRÔNICO" in badge.get_text().upper():
                return "ELETRONICO"
        return "FISICO"
    except Exception:
        return "FISICO"


@track_extraction_timing
@handle_extraction_errors(default_value="PUBLICO", log_errors=True)
def extract_publicidade(spider, driver: WebDriver, soup) -> str:
    """Extract publicidade (publicity) from page"""
    try:
        # Look for badges that indicate publicity status
        badges = soup.find_all("span", class_="badge")
        for badge in badges:
            if "PÚBLICO" in badge.get_text().upper():
                return "PUBLICO"
            elif "RESTRITO" in badge.get_text().upper():
                return "RESTRITO"
        return "PUBLICO"
    except Exception:
        return "PUBLICO"


@track_extraction_timing
@handle_extraction_errors(default_value=[], log_errors=True)
def extract_badges(spider, driver: WebDriver, soup) -> list:
    """Extract badges from page"""
    try:
        badges = []
        badge_elements = soup.find_all("span", class_="badge")
        for badge in badge_elements:
            badge_text = badge.get_text().strip()
            if badge_text:
                badges.append(badge_text)
        return badges
    except Exception:
        return []


@track_extraction_timing
@handle_extraction_errors(default_value=[], log_errors=True)
def extract_numero_origem(spider, driver: WebDriver, soup) -> list:
    """Extract numero_origem from page"""
    try:
        # Look for origin number in the process information
        origem_div = soup.find("div", {"id": "descricao-procedencia"})
        if origem_div:
            origem_text = origem_div.get_text().strip()
            # Extract numbers from the text
            import re

            numbers = re.findall(r"\d+", origem_text)
            if numbers:
                return [int(num) for num in numbers]
        return []
    except Exception:
        return []


@track_extraction_timing
@handle_extraction_errors(default_value=1, log_errors=True)
def extract_volumes(spider, driver: WebDriver, soup) -> int:
    """Extract volumes from page"""
    try:
        # Look for volumes information in the process details
        # This is a placeholder - volumes info might not be available on the page
        return 1
    except Exception:
        return 1


@track_extraction_timing
@handle_extraction_errors(default_value=0, log_errors=True)
def extract_folhas(spider, driver: WebDriver, soup) -> int:
    """Extract folhas (pages) from page"""
    try:
        # Look for pages information in the process details
        # This is a placeholder - pages info might not be available on the page
        return 0
    except Exception:
        return 0


@track_extraction_timing
@handle_extraction_errors(default_value=0, log_errors=True)
def extract_apensos(spider, driver: WebDriver, soup) -> int:
    """Extract apensos (attached processes) from page"""
    try:
        # Look for attached processes information
        # This is a placeholder - apensos info might not be available on the page
        return 0
    except Exception:
        return 0


@track_extraction_timing
@handle_extraction_errors(default_value=None, log_errors=True)
def extract_primeiro_autor(spider, driver: WebDriver, soup) -> str | None:
    """Extract primeiro_autor (first author) from page"""
    try:
        # Look for first author in the parts section
        partes_div = soup.find("div", {"id": "resumo-partes"})
        if partes_div:
            # Look for the first author type
            partes = partes_div.find_all("div", class_="processo-partes")
            for i, parte in enumerate(partes):
                if "AUTOR" in parte.get_text().upper() and i + 1 < len(partes):
                    return partes[i + 1].get_text().strip()
        return None
    except Exception:
        return None


@track_extraction_timing
@handle_extraction_errors(default_value=[], log_errors=True)
def extract_assuntos(spider, driver: WebDriver, soup) -> list:
    """Extract assuntos using XPath from backup"""
    try:
        assuntos_html = spider.get_element_by_xpath(
            driver, '//*[@id="informacoes-completas"]/div[1]/div[2]'
        )
        soup_assuntos = BeautifulSoup(assuntos_html, "html.parser")
        assuntos_list = []
        for li in soup_assuntos.find_all("li"):
            assunto_text = li.get_text(strip=True)
            if assunto_text:
                assuntos_list.append(assunto_text)
        return assuntos_list
    except Exception:
        return []


@track_extraction_timing
@handle_extraction_errors(default_value=[], log_errors=True)
def extract_andamentos(spider, driver: WebDriver, soup) -> list:
    """Extract andamentos using class selectors from backup"""
    try:
        andamentos_info = driver.find_element(By.CLASS_NAME, "processo-andamentos")
        andamentos = andamentos_info.find_elements(By.CLASS_NAME, "andamento-item")

        andamentos_list = []
        for i, andamento in enumerate(andamentos):
            try:
                index = len(andamentos) - i

                # Extract data, nome, complemento, julgador
                data = andamento.find_element(By.CLASS_NAME, "andamento-data").text
                nome = andamento.find_element(By.CLASS_NAME, "andamento-nome").text
                complemento = andamento.find_element(By.CLASS_NAME, "col-md-9").text

                # Check for julgador
                try:
                    julgador = andamento.find_element(
                        By.CLASS_NAME, "andamento-julgador"
                    ).text
                except Exception:
                    julgador = None

                # Attempt to extract link and its description (anchor text) from innerHTML
                link = None
                link_descricao = None
                try:
                    html = andamento.get_attribute("innerHTML")
                    if html and "href" in html:
                        import re

                        href_match = re.search(r'href="([^"#]+)"', html)
                        if href_match:
                            # Build absolute URL like ground truth
                            link = (
                                "https://portal.stf.jus.br/processos/"
                                + href_match.group(1).replace("amp;", "")
                            )

                        # Try to get anchor text as link_descricao
                        text_match = re.search(r">\s*([^<][^<]+)\s*</a>", html)
                        if text_match:
                            link_descricao = spider.clean_text(text_match.group(1))
                except Exception:
                    pass

                andamento_data = {
                    "index_num": index,
                    "data": data,
                    "nome": nome,
                    "complemento": complemento,
                    "link_descricao": link_descricao,
                    "link": link,
                    "julgador": julgador,
                }
                andamentos_list.append(andamento_data)
            except Exception as e:
                spider.logger.warning(f"Could not extract andamento {i}: {e}")
                continue

        return andamentos_list
    except Exception as e:
        spider.logger.warning(f"Could not extract andamentos: {e}")
        return []


@track_extraction_timing
@handle_extraction_errors(default_value=[], log_errors=True)
def extract_decisoes(spider, driver: WebDriver, soup) -> list:
    """Extract decisoes from andamento-julgador badge elements"""
    try:
        # Find all andamento elements that contain julgador badges
        andamentos = driver.find_elements(By.CLASS_NAME, "andamento-item")
        decisoes_list = []

        for i, andamento in enumerate(andamentos):
            try:
                html = andamento.get_attribute("innerHTML")

                # Check if this andamento has a julgador badge (indicating a decision)
                if "andamento-julgador badge bg-info" in html:
                    # Extract decision data
                    data_element = andamento.find_element(
                        By.CLASS_NAME, "andamento-data"
                    )
                    nome_element = andamento.find_element(
                        By.CLASS_NAME, "andamento-nome"
                    )
                    julgador_element = andamento.find_element(
                        By.CLASS_NAME, "andamento-julgador"
                    )
                    complemento_element = andamento.find_element(
                        By.CLASS_NAME, "col-md-9"
                    )

                    # Extract link if present
                    link = None
                    if "href" in html:
                        import re

                        link_match = re.search(r'href="([^"]+)"', html)
                        if link_match:
                            link = (
                                "https://portal.stf.jus.br/processos/"
                                + link_match.group(1).replace("amp;", "")
                            )

                    # Clean the extracted data
                    data = spider.clean_text(data_element.text)
                    nome = spider.clean_text(nome_element.text)
                    julgador = spider.clean_text(julgador_element.text)
                    complemento = spider.clean_text(complemento_element.text)

                    # Filter out entries that are mostly null/empty
                    # Keep only if at least 3 meaningful fields have content
                    meaningful_fields = [data, nome, julgador, complemento, link]
                    non_empty_fields = [
                        field for field in meaningful_fields if field and field.strip()
                    ]

                    # Only add if we have at least 3 non-empty fields
                    if len(non_empty_fields) >= 3:
                        decisao_data = {
                            "index_num": i + 1,
                            "data": data,
                            "nome": nome,
                            "julgador": julgador,
                            "complemento": complemento,
                            "link": link,
                        }
                        decisoes_list.append(decisao_data)

            except Exception as e:
                spider.logger.warning(f"Could not extract decisao {i}: {e}")
                continue

        return decisoes_list
    except Exception as e:
        spider.logger.warning(f"Could not extract decisoes: {e}")
        return []


@track_extraction_timing
@handle_extraction_errors(default_value=[], log_errors=True)
def extract_deslocamentos(spider, driver: WebDriver, soup) -> list:
    """Extract deslocamentos using XPath and class selectors from backup"""
    try:
        deslocamentos_info = driver.find_element(By.XPATH, '//*[@id="deslocamentos"]')
        deslocamentos = deslocamentos_info.find_elements(By.CLASS_NAME, "lista-dados")

        deslocamentos_list = []
        for i, deslocamento in enumerate(deslocamentos):
            try:
                index = len(deslocamentos) - i
                html = deslocamento.get_attribute("innerHTML")

                # Extract data from HTML using text parsing (like backup)
                import re

                enviado_match = re.search(r'"processo-detalhes-bold">([^<]+)', html)
                data_recebido_match = re.search(
                    r'processo-detalhes bg-font-success">([^<]+)', html
                )
                recebido_match = re.search(r'"processo-detalhes">([^<]+)', html)
                data_enviado_match = re.search(
                    r'processo-detalhes bg-font-info">([^<]+)', html
                )
                guia_match = re.search(
                    r'text-right">\s*<span class="processo-detalhes">([^<]+)', html
                )

                # Clean the extracted data
                data_recebido = (
                    data_recebido_match.group(1) if data_recebido_match else None
                )
                data_enviado = (
                    data_enviado_match.group(1) if data_enviado_match else None
                )
                guia = guia_match.group(1) if guia_match else None

                # Get raw text for parsing
                enviado_raw = recebido_match.group(1) if recebido_match else None
                recebido_raw = enviado_match.group(1) if enviado_match else None

                # Clean data_recebido - remove extra text, keep only date
                if data_recebido is not None:
                    data_recebido = spider.clean_text(data_recebido)
                    # Remove common prefixes/suffixes
                    data_recebido = (
                        data_recebido.replace("Recebido em ", "")
                        .replace(" em ", "")
                        .strip()
                    )

                # Clean data_enviado - remove extra text, keep only date
                if data_enviado is not None:
                    data_enviado = spider.clean_text(data_enviado)
                    # Remove common prefixes/suffixes
                    data_enviado = (
                        data_enviado.replace("Enviado em ", "")
                        .replace(" em ", "")
                        .strip()
                    )

                # Extract date from enviado_por text and clean it
                enviado_por_clean = enviado_raw
                if enviado_raw is not None:
                    enviado_por_clean = spider.clean_text(enviado_raw)
                    # Extract date from "Enviado por X em DD/MM/YYYY" format
                    date_match = re.search(r"em (\d{2}/\d{2}/\d{4})", enviado_por_clean)
                    if date_match and data_enviado is None:
                        data_enviado = date_match.group(1)
                    # Remove boilerplate text
                    enviado_por_clean = re.sub(r"^Enviado por ", "", enviado_por_clean)
                    enviado_por_clean = re.sub(
                        r" em \d{2}/\d{2}/\d{4}$", "", enviado_por_clean
                    )

                # Extract date from recebido_por text and clean it
                recebido_por_clean = recebido_raw
                if recebido_raw is not None:
                    recebido_por_clean = spider.clean_text(recebido_raw)
                    # Extract date from "Recebido por X em DD/MM/YYYY" format
                    date_match = re.search(
                        r"em (\d{2}/\d{2}/\d{4})", recebido_por_clean
                    )
                    if date_match and data_recebido is None:
                        data_recebido = date_match.group(1)
                    # Remove boilerplate text
                    recebido_por_clean = re.sub(
                        r"^Recebido por ", "", recebido_por_clean
                    )
                    recebido_por_clean = re.sub(
                        r" em \d{2}/\d{2}/\d{4}$", "", recebido_por_clean
                    )

                # Clean guia - remove extra text, keep only number
                if guia is not None:
                    guia = spider.clean_text(guia)
                    # Remove common prefixes/suffixes
                    guia = guia.replace("Guia: ", "").replace("Nº ", "").strip()

                deslocamento_data = {
                    "index": index,
                    "data_enviado": data_enviado,
                    "data_recebido": data_recebido,
                    "enviado_por": enviado_por_clean,
                    "recebido_por": recebido_por_clean,
                    "guia": guia,
                }
                deslocamentos_list.append(deslocamento_data)
            except Exception as e:
                spider.logger.warning(f"Could not extract deslocamento {i}: {e}")
                continue

        return deslocamentos_list
    except Exception as e:
        spider.logger.warning(f"Could not extract deslocamentos: {e}")
        return []


@track_extraction_timing
@handle_extraction_errors(default_value=[], log_errors=True)
def extract_peticoes(spider, driver: WebDriver, soup) -> list:
    """Extract peticoes from AJAX-loaded content"""
    try:
        peticoes_info = driver.find_element(By.XPATH, '//*[@id="peticoes"]')
        peticoes = peticoes_info.find_elements(By.CLASS_NAME, "lista-dados")

        peticoes_list = []
        for i, peticao in enumerate(peticoes):
            try:
                index = len(peticoes) - i
                html = peticao.get_attribute("innerHTML")

                # Extract data from HTML using text parsing
                import re

                # Look for different patterns to extract all fields
                data_match = re.search(r'processo-detalhes bg-font-info">([^<]+)', html)
                tipo_match = re.search(r'processo-detalhes-bold">([^<]+)', html)
                autor_match = re.search(r'processo-detalhes">([^<]+)', html)

                # Also look for "Recebido em" pattern
                recebido_match = re.search(r"Recebido em ([^<]+)", html)

                data = data_match.group(1) if data_match else None
                tipo = tipo_match.group(1) if tipo_match else None
                autor = autor_match.group(1) if autor_match else None
                recebido = recebido_match.group(1) if recebido_match else None

                # Clean the extracted data
                if data is not None:
                    data = spider.clean_text(data)
                if tipo is not None:
                    tipo = spider.clean_text(tipo)
                if autor is not None:
                    autor = spider.clean_text(autor)
                if recebido is not None:
                    recebido = spider.clean_text(recebido)

                # Parse recebido into recebido_data and recebido_por
                recebido_data = None
                recebido_por = None
                if recebido is not None:
                    # Extract date and organization from "04/05/1994 00:00:00 por DIVISAO DE PROCESSOS ORIGINARIOS"
                    recebido_parts = recebido.split(" por ")
                    if len(recebido_parts) == 2:
                        recebido_data = recebido_parts[
                            0
                        ].strip()  # "04/05/1994 00:00:00"
                        recebido_por = recebido_parts[
                            1
                        ].strip()  # "DIVISAO DE PROCESSOS ORIGINARIOS"
                    else:
                        recebido_data = recebido  # Fallback to full string

                # The autor field seems to contain the petition date, not the author
                # Let's use it as the petition date and leave autor as None for now
                peticao_data = {
                    "index": index,
                    "data": autor,  # This seems to be the petition date
                    "tipo": tipo,
                    "autor": None,  # We don't have the actual author
                    "recebido_data": recebido_data,  # "04/05/1994 00:00:00"
                    "recebido_por": recebido_por,  # "DIVISAO DE PROCESSOS ORIGINARIOS"
                }
                peticoes_list.append(peticao_data)
            except Exception as e:
                spider.logger.warning(f"Could not extract peticao {i}: {e}")
                continue

        return peticoes_list
    except Exception as e:
        spider.logger.warning(f"Could not extract peticoes: {e}")
        return []


@track_extraction_timing
@handle_extraction_errors(default_value=[], log_errors=True)
def extract_recursos(spider, driver: WebDriver, soup) -> list:
    """Extract recursos from andamentos that have julgador badges"""
    try:
        # Find all andamento elements
        andamentos = driver.find_elements(By.CLASS_NAME, "andamento-item")
        recursos_list = []

        for i, andamento in enumerate(andamentos):
            try:
                html = andamento.get_attribute("innerHTML")

                # Check if this andamento has a julgador badge (indicating a decision/recurso)
                if "andamento-julgador badge bg-info" in html:
                    # Extract recurso data
                    data_element = andamento.find_element(
                        By.CLASS_NAME, "andamento-data"
                    )
                    nome_element = andamento.find_element(
                        By.CLASS_NAME, "andamento-nome"
                    )
                    julgador_element = andamento.find_element(
                        By.CLASS_NAME, "andamento-julgador"
                    )
                    complemento_element = andamento.find_element(
                        By.CLASS_NAME, "col-md-9"
                    )

                    # Try to extract autor from complemento or other elements
                    autor = None
                    try:
                        # Look for autor in the complemento text
                        complemento_text = complemento_element.text
                        if (
                            "autor" in complemento_text.lower()
                            or "requerente" in complemento_text.lower()
                        ):
                            # Extract autor name from complemento
                            import re

                            autor_match = re.search(
                                r"(?:autor|requerente)[:\s]+([^,\n]+)",
                                complemento_text,
                                re.IGNORECASE,
                            )
                            if autor_match:
                                autor = spider.clean_text(autor_match.group(1))
                    except Exception:
                        pass

                    # Clean the extracted data
                    data = spider.clean_text(data_element.text)
                    nome = spider.clean_text(nome_element.text)
                    julgador = spider.clean_text(julgador_element.text)
                    complemento = spider.clean_text(complemento_element.text)

                    # Filter out entries that are mostly null/empty
                    # Keep only if at least 3 meaningful fields have content
                    meaningful_fields = [data, nome, julgador, complemento, autor]
                    non_empty_fields = [
                        field for field in meaningful_fields if field and field.strip()
                    ]

                    # Only add if we have at least 3 non-empty fields
                    if len(non_empty_fields) >= 3:
                        recurso_data = {
                            "index_num": i + 1,
                            "data": data,
                            "nome": nome,
                            "julgador": julgador,
                            "complemento": complemento,
                            "autor": autor,
                        }
                        recursos_list.append(recurso_data)

            except Exception as e:
                spider.logger.warning(f"Could not extract recurso {i}: {e}")
                continue

        return recursos_list
    except Exception as e:
        spider.logger.warning(f"Could not extract recursos: {e}")
        return []


@track_extraction_timing
@handle_extraction_errors(default_value=[], log_errors=True)
def extract_pautas(spider, driver: WebDriver, soup) -> list:
    """Extract pautas from andamentos that have 'pauta' in their name"""
    try:
        # Find all andamento elements
        andamentos = driver.find_elements(By.CLASS_NAME, "andamento-item")
        pautas_list = []

        for i, andamento in enumerate(andamentos):
            try:
                # Get the andamento name to check if it contains "pauta"
                nome_element = andamento.find_element(By.CLASS_NAME, "andamento-nome")
                nome_text = nome_element.text.lower()

                # Check if this andamento is a pauta (has "pauta" in the name)
                if "pauta" in nome_text:
                    # Extract pauta data
                    data_element = andamento.find_element(
                        By.CLASS_NAME, "andamento-data"
                    )
                    complemento_element = andamento.find_element(
                        By.CLASS_NAME, "col-md-9"
                    )

                    # Try to extract relator from complemento or other elements
                    relator = None
                    try:
                        # Look for relator in the complemento text
                        complemento_text = complemento_element.text
                        if (
                            "relator" in complemento_text.lower()
                            or "ministro" in complemento_text.lower()
                        ):
                            # Extract relator name from complemento
                            import re

                            relator_match = re.search(
                                r"(?:relator|ministro)[:\s]+([^,\n]+)",
                                complemento_text,
                                re.IGNORECASE,
                            )
                            if relator_match:
                                relator = spider.clean_text(relator_match.group(1))
                    except Exception:
                        pass

                    pauta_data = {
                        "index_num": i + 1,
                        "data": spider.clean_text(data_element.text),
                        "nome": spider.clean_text(nome_element.text),
                        "complemento": spider.clean_text(complemento_element.text),
                        "relator": relator,
                    }
                    pautas_list.append(pauta_data)

            except Exception as e:
                spider.logger.warning(f"Could not extract pauta {i}: {e}")
                continue

        return pautas_list
    except Exception as e:
        spider.logger.warning(f"Could not extract pautas: {e}")
        return []


@track_extraction_timing
@handle_extraction_errors(default_value={}, log_errors=True)
def extract_sessao(spider, driver: WebDriver, soup) -> dict:
    """Extract sessao from AJAX-loaded content"""
    try:
        sessao_info = driver.find_element(By.XPATH, '//*[@id="sessao-virtual"]')

        # Extract session information
        sessao_data: dict = {
            "data": None,
            "tipo": None,
            "numero": None,
            "relator": None,
            "status": None,
            "participantes": [],
        }

        # Try to extract basic session info
        try:
            data_element = sessao_info.find_element(By.CLASS_NAME, "processo-detalhes")
            sessao_data["data"] = spider.clean_text(data_element.text)
        except Exception:
            pass

        try:
            tipo_element = sessao_info.find_element(
                By.CLASS_NAME, "processo-detalhes-bold"
            )
            sessao_data["tipo"] = spider.clean_text(tipo_element.text)
        except Exception:
            pass

        return sessao_data
    except Exception as e:
        spider.logger.warning(f"Could not extract sessao: {e}")
        return {}

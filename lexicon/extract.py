import re

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

# Optimized extractors for STF HTML structure


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


def extract_tipo_processo(soup) -> str | None:
    """Extract tipo_processo from badge elements"""
    badges = [b.get_text(strip=True) for b in soup.select(".badge")]
    for badge in badges:
        if "Físico" in badge:
            return "Físico"
        elif "Eletrônico" in badge:
            return "Eletrônico"
    return None


def extract_classe(soup) -> str | None:
    """Extract classe from .processo-dados elements"""
    for div in soup.select(".processo-dados"):
        text = div.get_text(" ", strip=True)
        if text.startswith("Classe:"):
            return text.split(":", 1)[1].strip()
    return None


def extract_incidente(soup) -> str | None:
    """Extract incidente from .processo-dados elements"""
    for div in soup.select(".processo-dados"):
        text = div.get_text(" ", strip=True)
        if text.startswith("Incidente:"):
            return text.split(":", 1)[1].strip()
    return None


def extract_origem(spider, soup, driver: WebDriver) -> str | None:
    return spider.clean_text(
        spider.get_element_by_xpath(driver, '//*[@id="descricao-procedencia"]')
    )


def extract_liminar(spider, driver: WebDriver, soup: BeautifulSoup) -> list:
    """Extract liminar from bg-danger elements like in backup"""
    try:
        liminar_elements = driver.find_elements(By.CLASS_NAME, "bg-danger")
        liminar_list = []

        for element in liminar_elements:
            text = element.text.strip()
            if text:
                liminar_list.append(text)

        return liminar_list
    except Exception as e:
        spider.logger.warning(f"Could not extract liminar: {e}")
        return []


def extract_autor1(spider, driver: WebDriver, soup) -> str | None:
    """Extract autor1 using class selectors from backup"""
    try:
        partes_nome = driver.find_elements(By.CLASS_NAME, "nome-parte")
        if partes_nome:
            primeiro_autor = partes_nome[0].get_attribute("innerHTML")
            return spider.clean_text(primeiro_autor)
    except Exception:
        pass
    return None


def extract_partes(soup):
    partes_elements = soup.find_all("div", class_="parte")
    partes_list = []

    for parte in partes_elements:
        parte_data = {
            "nome": (
                parte.find("div", class_="nome-parte").get_text().strip()
                if parte.find("div", class_="nome-parte")
                else ""
            ),
            "tipo": (
                parte.find("div", class_="tipo-parte").get_text().strip()
                if parte.find("div", class_="tipo-parte")
                else ""
            ),
            "advogados": [
                adv.get_text().strip() for adv in parte.find_all("div", class_="advogado")
            ],
        }
        partes_list.append(parte_data)

    return partes_list


def extract_data_protocolo(spider, driver: WebDriver, soup) -> str | None:
    """Extract data_protocolo using XPath from backup and format as ISO date"""
    try:
        data_html = spider.get_element_by_xpath(
            driver, '//*[@id="informacoes-completas"]/div[2]/div[1]/div[2]/div[2]'
        )
        data_text = spider.clean_text(data_html)

        if not data_text:
            return None

        # Parse Brazilian date format (DD/MM/YYYY) and convert to ISO
        import datetime

        try:
            # Try to parse DD/MM/YYYY format
            if "/" in data_text and len(data_text.split("/")) == 3:
                day, month, year = data_text.split("/")
                date_obj = datetime.datetime(int(year), int(month), int(day))
                return date_obj.isoformat() + "Z"
            else:
                # If not in expected format, return as-is
                return data_text
        except (ValueError, IndexError):
            # If parsing fails, return original text
            return data_text
    except Exception:
        return None


def extract_origem_orgao(spider, driver: WebDriver, soup) -> str | None:
    """Extract origem_orgao using XPath from backup"""
    try:
        orgao_html = spider.get_element_by_xpath(
            driver, '//*[@id="informacoes-completas"]/div[2]/div[1]/div[2]/div[4]'
        )
        return spider.clean_text(orgao_html)
    except Exception:
        return None


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


def extract_andamentos(soup):
    andamentos_elements = soup.find_all("div", class_="andamento")
    andamentos_list = []

    for andamento in andamentos_elements:
        andamento_data = {
            "data": (
                andamento.find("div", class_="data-andamento").get_text().strip()
                if andamento.find("div", class_="data-andamento")
                else ""
            ),
            "descricao": (
                andamento.find("div", class_="descricao-andamento").get_text().strip()
                if andamento.find("div", class_="descricao-andamento")
                else ""
            ),
            "tipo": (
                andamento.find("div", class_="tipo-andamento").get_text().strip()
                if andamento.find("div", class_="tipo-andamento")
                else ""
            ),
        }
        andamentos_list.append(andamento_data)

    return andamentos_list


def extract_decisoes(soup):
    decisoes_elements = soup.find_all("div", class_="decisao")
    decisoes_list = []

    for decisao in decisoes_elements:
        decisao_data = {
            "data": (
                decisao.find("div", class_="data-decisao").get_text().strip()
                if decisao.find("div", class_="data-decisao")
                else ""
            ),
            "tipo": (
                decisao.find("div", class_="tipo-decisao").get_text().strip()
                if decisao.find("div", class_="tipo-decisao")
                else ""
            ),
            "relator": (
                decisao.find("div", class_="relator-decisao").get_text().strip()
                if decisao.find("div", class_="relator-decisao")
                else ""
            ),
            "texto": (
                decisao.find("div", class_="texto-decisao").get_text().strip()
                if decisao.find("div", class_="texto-decisao")
                else ""
            ),
        }
        decisoes_list.append(decisao_data)

    return decisoes_list


def extract_deslocamentos(soup):
    deslocamentos_elements = soup.find_all("div", class_="deslocamento")
    deslocamentos_list = []

    for deslocamento in deslocamentos_elements:
        deslocamento_data = {
            "data": (
                deslocamento.find("div", class_="data-deslocamento").get_text().strip()
                if deslocamento.find("div", class_="data-deslocamento")
                else ""
            ),
            "destino": (
                deslocamento.find("div", class_="destino-deslocamento").get_text().strip()
                if deslocamento.find("div", class_="destino-deslocamento")
                else ""
            ),
            "motivo": (
                deslocamento.find("div", class_="motivo-deslocamento").get_text().strip()
                if deslocamento.find("div", class_="motivo-deslocamento")
                else ""
            ),
        }
        deslocamentos_list.append(deslocamento_data)

    return deslocamentos_list

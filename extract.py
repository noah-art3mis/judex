import re

import requests
from bs4 import BeautifulSoup


def extract_stf_data(html_content, incidente_id, processo_id):
    """
    Extract all STF case data from HTML content
    Returns a dictionary with all the required fields
    """
    soup = BeautifulSoup(html_content, "html.parser")
    data = {}

    data["incidente"] = incidente_id
    data["processo_id"] = processo_id
    data["liminar"] = extract_liminar(soup)
    data["autor1"] = extract_autor1(soup)
    data["data_protocolo"] = extract_data_protocolo(soup)
    data["origem_orgao"] = extract_origem_orgao(soup)
    data["assuntos"] = extract_assuntos(soup)

    data["andamentos"] = extract_andamentos(soup)
    data["andamentos_len"] = len(data["andamentos_lista"])

    data["partes"] = extract_partes(soup)
    data["partes_len"] = len(data["partes"])

    data["decisoes"] = extract_decisoes(soup)
    data["decisoes_len"] = data["decisoes"]

    data["deslocamentos"] = extract_deslocamentos(soup)
    data["deslocamentos_len"] = len(data["deslocamentos"])

    # sessao virtual?
    # peticoes?
    # recursos?
    # pautas?

    return data


def extract_liminar(soup):
    """Extract liminar information"""
    try:
        # Look for liminar information in the process details
        liminar_element = soup.find("div", string=re.compile(r"Liminar", re.IGNORECASE))
        if liminar_element:
            return liminar_element.get_text().strip()
        return None
    except:
        return None


def extract_autor1(soup):
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


def extract_partes(soup):
    """Extract all parties involved"""
    try:
        # From the parties section
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
    except:
        return []


def extract_data_protocolo(soup):
    """Extract protocol date"""
    try:
        # From the process information
        data_element = soup.find("div", string=re.compile(r"Data do Protocolo", re.IGNORECASE))
        if data_element:
            data_text = data_element.get_text()
            if "Data do Protocolo" in data_text:
                data = data_text.split("Data do Protocolo")[1].strip()
                return data
        return None
    except:
        return None


def extract_origem_orgao(soup):
    """Extract origin organ"""
    try:
        # From the origin information
        orgao_element = soup.find("div", string=re.compile(r"Órgão de Origem", re.IGNORECASE))
        if orgao_element:
            orgao_text = orgao_element.get_text()
            if "Órgão de Origem" in orgao_text:
                orgao = orgao_text.split("Órgão de Origem")[1].strip()
                return orgao
        return None
    except:
        return None


def extract_assuntos(soup):
    """Extract subjects/topics"""
    try:
        # From the subjects section
        assuntos_elements = soup.find_all("div", class_="assunto")
        assuntos_list = [assunto.get_text().strip() for assunto in assuntos_elements]
        return assuntos_list
    except:
        return []


def extract_andamentos(soup):
    """Extract case proceedings"""
    try:
        # From the andamentos section
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
    except:
        return []


def extract_decisoes(soup):
    """Extract decisions"""
    try:
        # From the decisions section
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
    except:
        return []


def extract_deslocamentos(soup):
    """Extract displacements"""
    try:
        # From the displacements section
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
    except:
        return []


# Function to get AJAX content
def get_ajax_content(base_url, endpoint, incidente_id):
    """Get AJAX content from specific endpoints"""
    try:
        url = f"{base_url}/{endpoint}?incidente={incidente_id}"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.text
        return None
    except:
        return None


# Main function to extract all data from HTML
def scrape_stf_case(html_content, incidente_id, base_url="https://portal.stf.jus.br"):
    """
    Main function to scrape a complete STF case from HTML
    """
    try:
        # Parse main HTML
        case_data = extract_stf_data(html_content, incidente_id, None)

        # Get AJAX content for additional data
        ajax_endpoints = [
            ("abaPartes.asp", "partes"),
            ("abaAndamentos.asp", "andamentos"),
            ("abaDecisoes.asp", "decisoes"),
            ("abaDeslocamentos.asp", "deslocamentos"),
        ]

        for endpoint, data_type in ajax_endpoints:
            ajax_html = get_ajax_content(base_url, endpoint, incidente_id)
            if ajax_html:
                ajax_soup = BeautifulSoup(ajax_html, "html.parser")

                if data_type == "partes":
                    case_data["partes_total"] = extract_partes(ajax_soup)
                    case_data["len(partes_total)"] = len(case_data["partes_total"])
                elif data_type == "andamentos":
                    case_data["andamentos_lista"] = extract_andamentos(ajax_soup)
                    case_data["len(andamentos_lista)"] = len(case_data["andamentos_lista"])
                elif data_type == "decisoes":
                    case_data["decisões"] = extract_decisoes(ajax_soup)
                    case_data["len(decisões)"] = len(case_data["decisões"])
                elif data_type == "deslocamentos":
                    case_data["deslocamentos_lista"] = extract_deslocamentos(ajax_soup)
                    case_data["len(deslocamentos)"] = len(case_data["deslocamentos_lista"])

        return case_data

    except Exception as e:
        print(f"Error scraping case {incidente_id}: {str(e)}")
        return None

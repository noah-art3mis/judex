# Judex

Ferramenta para extração automatizada de dados do portal do STF.

Utiliza scrapy-selenium. Tem performance de ~4 processos por minuto. Possui suporte a JSON, JSONLines, CSV e SQLite.

## Uso simples via scrapy (Linux)

```bash
# instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# instalar chromedriver (pode demorar um pouco)
sudo apt install chromium-chromedriver

# clonar repositório
git clone https://github.com/noah-art3mis/judex

# baixar dependências
cd judex && uv sync

# scrape
uv run scrapy crawl stf -a classe=ADI -a processos=[4916,4917] -O output.json
```

-   _classe_: classe dos processos de interesse (e.g., ADI, AR, etc.)
-   _processo_: número dos processos. Na CLI, devem ter o formato `[165,568]`, sem espaço.
-   _salvar_como_: permite alterar como os dados são armazenados. Pode ser `json`, `jsonlines`, `csv` e/ou `sql`.

Para outros parâmetros, ver `settings.py` ou a documentação do scrapy. Configurações relevantes do scrapy incluem:

```json
LOG_LEVEL = "DEBUG"
HTTPCACHE_ENABLED = True
AUTOTHROTTLE_ENABLED = True
```

### 2. Como biblioteca

```bash
pip install judex
```

The main entry point is the `JudexScraper` class, which takes a class, a list of cases, and a persistence method ('sql', 'json', 'jsonlines' and/or 'csv').

```python
from judex import judexScraper

scraper = JudexScraper(
    classe="ADI",
    processos="[1,2]",
    salvar_como=['csv']
    )
scraper.scrape()
```

## Resultado

Os dados em json ficam alinhandos, enquanto em sql eles são normalizados nas seguintes tabelas:

-   `processos`: Informações gerais do processo (número único, classe, relator, etc.)
-   `partes`: Partes envolvidas no processo (autores, réus, etc.)
-   `andamentos`: Movimentações processuais
-   `decisoes`: Decisões judiciais com links para os documentos
-   `peticoes`: Petições apresentadas no processo
-   `recursos`: Recursos interpostos
-   `pautas`: Pautas de julgamento

```python

class Processo:
    numero_unico: str
    incidente: int
    processo_id: int

    classe: str
    tipo_processo: str
    liminar: bool
    relator: str
    origem: str
    origem_orgao: str
    data_protocolo: str
    autor1: str
    assuntos: str

    html: str
    error_message: str
    created_at: datetime
    updated_at: datetime

class Partes:
    id: int
    numero_unico: str
    index: int
    tipo: str
    nome: str

class Andamento:
    id: int
    numero_unico: str
    index_num: int
    data: str
    nome: str
    complemento: str
    julgador: str

class Decisao:
    id: int
    numero_unico: str
    index_num: int
    data: str
    nome: str
    julgador: str
    complemento: str
    link: str

class Deslocamento:
    id: int
    numero_unico: str
    index_num: int
    data_enviado: str
    data_recebido: str
    enviado_por: str
    recebido_por: str
    guia: str

class Peticao:
    id: int
    numero_unico: str
    index_num: int
    data: str
    tipo: str
    autor: str
    recebido_data: str
    recebido_por: str

class Recurso:
    id: int
    numero_unico: str
    index_num: int
    data: str
    nome: str
    julgador: str
    complemento: str
    autor: str

class Pauta:
    id: int
    numero_unico: str
    index_num: int
    data: str
    nome: str
    complemento: str
    relator: str
```

## Solução de Problemas

### ChromeDriver não encontrado

```bash
# Verificar se ChromeDriver está instalado
which chromedriver

# Instalar ChromeDriver
sudo apt-get install chromium-chromedriver
```

### Espaço na lista de processos

**scrapy: error: running 'scrapy crawl' with more than one spider is not supported**

```bash
# NO
scrapy crawl stf -a classe=ADPF -a processos=[165, 568]

# YES
scrapy crawl stf -a classe=ADPF -a processos=[165,568]
```

## Considerações Legais e Éticas

Este projeto faz scraping de dados publicamente disponíveis do portal do STF. Por favor, note:

-   **robots.txt não é legalmente vinculante** - É um protocolo voluntário que sites usam para comunicar com crawlers
-   **Nenhum Termo de Serviço encontrado** - O portal do STF não possui termos de serviço publicamente acessíveis
-   **Apenas dados públicos** - O scraper acessa apenas informações de casos publicamente disponíveis
-   **Scraping respeitoso** - Implementa delays e segue práticas éticas para evitar sobrecarga do servidor

## Changelog

### v1.0.0

-   Extração inicial de dados do STF
-   Suporte a múltiplas classes de processo
-   Validação de dados com Pydantic
-   Exportação para JSON e CSV
-   Docker, pre-commit hooks (ruff, black, mypy, pytest)

## Licença

MIT

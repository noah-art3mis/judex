# Judex

Ferramenta para extração automatizada de dados do portal do STF.

Utiliza scrapy-selenium. Tem performance de ~4 processos por minuto. Possui suporte a JSON, JSONLines, CSV e SQLite.

## Uso via CLI (Recomendado)

```bash
# instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# instalar chromedriver (pode demorar um pouco)
sudo apt install chromium-chromedriver

# clonar repositório
git clone https://github.com/noah-art3mis/judex

# baixar dependências
cd judex && uv sync

# instalar em modo editável
uv pip install -e .

# usar o CLI
uv run judex scrape --classe ADI --processo 4916 --processo 4917 --salvar-como json
```

### Parâmetros do CLI

-   `-c, --classe`: classe do processo de interesse (e.g., ADI, AR, etc.)
-   `-p, --processo`: número do processo (pode especificar múltiplos)
-   `-s, --salvar-como`: tipo de persistência (json, csv, jsonl, sql) - pode especificar múltiplos

---

-   `--output-path`: diretório de saída (padrão: judex_output)
-   `--verbose`: habilitar logging verboso
-   `--skip-existing`: pular processos existentes (padrão: true)
-   `--retry-failed`: tentar novamente processos que falharam (padrão: true)
-   `--max-age`: idade máxima dos processos em horas (padrão: 24)

### Exemplos de uso

```bash
# Uso simples
uv run judex scrape -c ADI -p 4916 -s csv

# Múltiplos processos
uv run judex scrape -c ADI -p 4916 -p 4917 -p 4918 -s json

# Múltiplos formatos de saída
uv run judex scrape -c ADPF -p 123 -s json -s sql

# Com opções avançadas
uv run judex scrape -c ADI -p 123 --output-path /tmp/output --verbose --max-age 48
```

### 2. Como biblioteca

```bash
pip install judex
```

O ponto de entrada principal é a classe `JudexScraper`, que recebe uma classe, uma lista de processos e um método de persistência ('sql', 'json', 'jsonl' e/ou 'csv').

```python
from judex import judexScraper

scraper = JudexScraper(
    classe="ADI",
    processos="[1,2]",
    salvar_como=['csv']
    )
scraper.scrape()
```

## Uso avançado via scrapy

```bash
# scrape
uv run scrapy crawl stf -a classe=ADI -a processos=[4916,4917] -O output.json
```

Esta forma permite aplicar outros parâmetros do scrapy, como LOG_LEVEL, HTTPCACHE_ENABLED, AUTOTHROTTLE_ENABLED, etc.

## Resultado

Os dados em json ficam aninhados, enquanto em sql eles são normalizados nas seguintes tabelas:

-   `processo`: Informações gerais do processo (número único, classe, relator, etc.)
-   `partes`: Partes envolvidas no processo (autores, réus, etc.)
-   `andamentos`: Movimentações processuais
-   `decisoes`: Decisões judiciais com links para os documentos
-   `peticoes`: Petições apresentadas no processo
-   `recursos`: Recursos interpostos
-   `pautas`: Pautas de julgamento

Os dados tem o seguinte formato:

```python

class Processo:
    # ids
    numero_unico: str
    incidente: int
    processo_id: int

    # detalhes
    classe: str
    tipo_processo: str
    liminar: bool
    relator: str
    origem: str
    origem_orgao: str
    data_protocolo: str
    autor1: str
    assuntos: str

    # listas
    partes: list
    andamento: list
    decisao: list 
    deslocamento: list 
    peticao: list 
    recursos: list 

    # metadados
    html: str
    error_message: str
    created_at: datetime
    updated_at: datetime
```

## Solução de Problemas

### ChromeDriver não encontrado

```bash
# Verificar se ChromeDriver está instalado
which chromedriver

# Instalar ChromeDriver
sudo apt-get install chromium-chromedriver
```

### Erro no uso via scrapy

**scrapy: error: running 'scrapy crawl' with more than one spider is not supported**

```bash
# NO
scrapy crawl stf -a classe=ADPF -a processo=[165, 568]

# YES
scrapy crawl stf -a classe=ADPF -a processo=[165,568]
```

## Considerações Legais e Éticas

Este projeto faz scraping de dados publicamente disponíveis do portal do STF. Por favor, note:

-   **robots.txt não é legalmente vinculante** - É um protocolo voluntário que sites usam para comunicar com crawlers
-   **Nenhum Termo de Serviço encontrado** - O portal do STF não possui termos de serviço publicamente acessíveis
-   **Apenas dados públicos** - O scraper acessa apenas informações de casos publicamente disponíveis
-   **Scraping respeitoso** - Implementa delays e segue práticas éticas para evitar sobrecarga do servidor

## Changelog

### v1.1.0

-   CLI usando Typer

### v1.0.0

-   Extração inicial de dados do STF
-   Suporte a múltiplas classes de processo
-   Validação de dados com Pydantic
-   Exportação para JSON e CSV
-   Docker, pre-commit hooks (ruff, black, mypy, pytest)

## Licença

MIT

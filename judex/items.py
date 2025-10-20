import scrapy


class STFCaseItem(scrapy.Item):
    # Order must match tests in tests/test_dynamic_field_extraction.py

    # AJAX-loaded and dynamic ordering first
    andamentos = scrapy.Field()
    assuntos = scrapy.Field()
    primeiro_autor = scrapy.Field()

    # classification and dates
    classe = scrapy.Field()
    data_protocolo = scrapy.Field()

    # more dynamic content
    decisoes = scrapy.Field()
    deslocamentos = scrapy.Field()

    # metadata
    extraido = scrapy.Field()
    html = scrapy.Field()

    # ids and meta
    incidente = scrapy.Field()
    # informacoes removed from output
    liminar = scrapy.Field()
    numero_unico = scrapy.Field()
    origem = scrapy.Field()
    orgao_origem = scrapy.Field()
    orgao_origem = scrapy.Field()
    numero_origem = scrapy.Field()
    meio = scrapy.Field()
    publicidade = scrapy.Field()
    badges = scrapy.Field()
    volumes = scrapy.Field()
    folhas = scrapy.Field()
    apensos = scrapy.Field()

    # collections
    partes = scrapy.Field()
    pautas = scrapy.Field()
    peticoes = scrapy.Field()
    processo_id = scrapy.Field()
    recursos = scrapy.Field()

    # other
    relator = scrapy.Field()
    sessao = scrapy.Field()
    sessao_virtual = scrapy.Field()
    status = scrapy.Field()
    # tipo_processo removed from output (use 'meio' instead)

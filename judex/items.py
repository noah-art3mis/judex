import scrapy


class STFCaseItem(scrapy.Item):
    # ids
    processo_id = scrapy.Field()
    incidente = scrapy.Field()
    numero_unico = scrapy.Field()

    # do not need bs4
    classe = scrapy.Field()
    meio = scrapy.Field()
    publicidade = scrapy.Field()
    badges = scrapy.Field()
    liminar = scrapy.Field()
    meio = scrapy.Field()
    relator = scrapy.Field()
    primeiro_autor = scrapy.Field()

    # detalhes do processo
    origem = scrapy.Field()
    data_protocolo = scrapy.Field()
    orgao_origem = scrapy.Field()
    numero_origem = scrapy.Field()
    volumes = scrapy.Field()
    folhas = scrapy.Field()
    apensos = scrapy.Field()
    autor1 = scrapy.Field()
    assuntos = scrapy.Field()

    ### AJAX-loaded content
    partes = scrapy.Field()
    andamentos = scrapy.Field()
    decisoes = scrapy.Field()
    deslocamentos = scrapy.Field()
    peticoes = scrapy.Field()
    recursos = scrapy.Field()
    pautas = scrapy.Field()
    informacoes = scrapy.Field()
    sessao_virtual = scrapy.Field()

    # metadados
    status = scrapy.Field()
    html = scrapy.Field()
    extraido = scrapy.Field()

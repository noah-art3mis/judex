import scrapy


class STFCaseItem(scrapy.Item):
    # ids
    processo_id = scrapy.Field()
    incidente = scrapy.Field()
    numero_unico = scrapy.Field()

    # do not need bs4
    classe = scrapy.Field()
    liminar = scrapy.Field()
    tipo_processo = scrapy.Field()
    relator = scrapy.Field()
    # todo meio fisico ou eletronico
    # todo publicidade publico ou secreto

    # detalhes do processo
    origem = scrapy.Field()
    data_protocolo = scrapy.Field()
    origem_orgao = scrapy.Field()
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
    sessao = scrapy.Field()

    # metadados
    status = scrapy.Field()
    html = scrapy.Field()
    extraido = scrapy.Field()

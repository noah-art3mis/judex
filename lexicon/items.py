import scrapy


class STFCaseItem(scrapy.Item):
    # ids
    processo_id = scrapy.Field()
    incidente = scrapy.Field()
    numero_unico = scrapy.Field()

    # classificação do processo
    classe = scrapy.Field()
    liminar = scrapy.Field()
    tipo_processo = scrapy.Field()

    # detalhes do processo
    origem = scrapy.Field()
    relator = scrapy.Field()
    liminar = scrapy.Field()
    data_protocolo = scrapy.Field()
    origem_orgao = scrapy.Field()
    autor1 = scrapy.Field()
    assuntos = scrapy.Field()

    # metadados
    status = scrapy.Field()
    html = scrapy.Field()
    extraido = scrapy.Field()

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
    data_protocolo = scrapy.Field()
    origem_orgao = scrapy.Field()
    autor1 = scrapy.Field()
    assuntos = scrapy.Field()

    # AJAX-loaded content
    partes = scrapy.Field()
    andamentos = scrapy.Field()
    decisoes = scrapy.Field()
    deslocamentos = scrapy.Field()
    peticoes = scrapy.Field()
    recursos = scrapy.Field()
    pautas = scrapy.Field()
    informacoes = scrapy.Field()
    sessao = scrapy.Field()

    # AJAX status fields
    ajax_status_partes = scrapy.Field()
    ajax_status_andamentos = scrapy.Field()
    ajax_status_informacoes = scrapy.Field()
    ajax_status_decisoes = scrapy.Field()
    ajax_status_sessao = scrapy.Field()
    ajax_status_deslocamentos = scrapy.Field()
    ajax_status_peticoes = scrapy.Field()
    ajax_status_recursos = scrapy.Field()
    ajax_status_pautas = scrapy.Field()
    ajax_completed = scrapy.Field()

    # Error fields for AJAX responses
    ajax_error_partes = scrapy.Field()
    ajax_error_andamentos = scrapy.Field()
    ajax_error_informacoes = scrapy.Field()
    ajax_error_decisoes = scrapy.Field()
    ajax_error_sessao = scrapy.Field()
    ajax_error_deslocamentos = scrapy.Field()
    ajax_error_peticoes = scrapy.Field()
    ajax_error_recursos = scrapy.Field()
    ajax_error_pautas = scrapy.Field()

    # metadados
    status = scrapy.Field()
    html = scrapy.Field()
    extraido = scrapy.Field()

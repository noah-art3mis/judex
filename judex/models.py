"""
Pydantic models for STF case data validation and serialization
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CaseType(str, Enum):
    """STF case types enum"""

    AC = "AC"  # Ação Cível
    ACO = "ACO"  # Ação Cível Originária
    ADC = "ADC"  # Ação Declaratória de Constitucionalidade
    ADI = "ADI"  # Ação Direta de Inconstitucionalidade
    ADO = "ADO"  # Ação Direta de Inconstitucionalidade por Omissão
    ADPF = "ADPF"  # Arguição de Descumprimento de Preceito Fundamental
    AI = "AI"  # Ação Interlocutória
    AImp = "AImp"  # Ação de Improbidade Administrativa
    AO = "AO"  # Ação Originária
    AOE = "AOE"  # Ação Originária Especial
    AP = "AP"  # Ação Penal
    AR = "AR"  # Ação Rescisória
    ARE = "ARE"  # Agravo em Recurso Extraordinário
    AS = "AS"  # Ação de Suspensão
    CC = "CC"  # Conflito de Competência
    Cm = "Cm"  # Comunicado
    EI = "EI"  # Embargos Infringentes
    EL = "EL"  # Embargos de Declaração
    EP = "EP"  # Embargos de Petição
    Ext = "Ext"  # Extradição
    HC = "HC"  # Habeas Corpus
    HD = "HD"  # Habeas Data
    IF = "IF"  # Inquérito Federal
    Inq = "Inq"  # Inquérito
    MI = "MI"  # Mandado de Injunção
    MS = "MS"  # Mandado de Segurança
    PADM = "PADM"  # Processo Administrativo Disciplinar Militar
    Pet = "Pet"  # Petição
    PPE = "PPE"  # Processo de Prestação de Contas Eleitorais
    PSV = "PSV"  # Processo de Suspensão de Vigência
    RC = "RC"  # Recurso Cível
    Rcl = "Rcl"  # Reclamação
    RE = "RE"  # Recurso Extraordinário
    RHC = "RHC"  # Recurso em Habeas Corpus
    RHD = "RHD"  # Recurso em Habeas Data
    RMI = "RMI"  # Recurso em Mandado de Injunção
    RMS = "RMS"  # Recurso em Mandado de Segurança
    RvC = "RvC"  # Recurso em Violação de Cláusula de Tratado
    SE = "SE"  # Suspensão de Eficácia
    SIRDR = "SIRDR"  # Suspensão de Inquérito ou Recurso com Deficiência
    SL = "SL"  # Suspensão de Liminar
    SS = "SS"  # Suspensão de Segurança
    STA = "STA"  # Suspensão de Tutela Antecipada
    STP = "STP"  # Suspensão de Tutela Provisória
    TPA = "TPA"  # Tutela Provisória Antecipada


class ProcessType(str, Enum):
    """Process type enum"""

    FISICO = "Físico"
    ELETRONICO = "Eletrônico"


class Parte(BaseModel):
    """Model for process parties"""

    index: int | None = None  # Changed from _index to index
    tipo: str | None = None
    nome: str | None = None

    model_config = ConfigDict(extra="allow")  # Allow extra fields for flexibility


class Andamento(BaseModel):
    """Model for process movements"""

    index_num: int | None = None  # Database field name
    data: str | None = None
    nome: str | None = None
    complemento: str | None = None
    julgador: str | None = None

    model_config = ConfigDict(extra="allow")  # Allow extra fields for flexibility


class Decisao(BaseModel):
    """Model for decisions"""

    index_num: int | None = None  # Database field name
    data: str | None = None
    nome: str | None = None
    complemento: str | None = None
    julgador: str | None = None
    link: str | None = None  # Additional database field

    model_config = ConfigDict(extra="allow")  # Allow extra fields for flexibility


class Deslocamento(BaseModel):
    """Model for displacements"""

    index_num: int | None = None  # Database field name
    data_enviado: str | None = None  # Database field name
    data_recebido: str | None = None  # Database field name
    enviado_por: str | None = None  # Database field name
    recebido_por: str | None = None  # Database field name
    guia: str | None = None  # Database field name

    model_config = ConfigDict(extra="allow")  # Allow extra fields for flexibility


class Peticao(BaseModel):
    """Model for petitions"""

    index_num: int | None = None  # Database field name
    data: str | None = None
    tipo: str | None = None  # Database field name
    autor: str | None = None  # Database field name
    recebido_data: str | None = None  # Database field name
    recebido_por: str | None = None  # Database field name

    model_config = ConfigDict(extra="allow")  # Allow extra fields for flexibility


class Recurso(BaseModel):
    """Model for appeals"""

    index_num: int | None = None  # Database field name
    data: str | None = None
    nome: str | None = None
    julgador: str | None = None
    complemento: str | None = None
    autor: str | None = None  # Database field name

    model_config = ConfigDict(extra="allow")  # Allow extra fields for flexibility


class Pauta(BaseModel):
    """Model for agendas"""

    index_num: int | None = None  # Database field name
    data: str | None = None
    nome: str | None = None
    complemento: str | None = None
    relator: str | None = None  # Database field name

    model_config = ConfigDict(extra="allow")  # Allow extra fields for flexibility


class Sessao(BaseModel):
    """Model for sessions"""

    data: str | None = None
    tipo: str | None = None
    numero: str | None = None
    relator: str | None = None

    model_config = ConfigDict(extra="allow")  # Allow extra fields for flexibility


class STFCaseModel(BaseModel):
    """Main Pydantic model for STF cases"""

    # IDs
    processo_id: int
    incidente: int
    numero_unico: str | None = None

    # Classification
    classe: str  # Allow strings for backward compatibility
    tipo_processo: ProcessType | None = None
    liminar: int | None = None  # Database stores as INT (0 or 1)
    relator: str | None = None

    # Process details
    origem: str | None = None
    data_protocolo: str | None = None
    origem_orgao: str | None = None
    autor1: str | None = None
    assuntos: str | None = None  # Database stores as JSON TEXT

    # AJAX-loaded content
    partes: list[Parte] = Field(default_factory=list)
    andamentos: list[Andamento] = Field(default_factory=list)
    decisoes: list[Decisao] = Field(default_factory=list)
    deslocamentos: list[Deslocamento] = Field(default_factory=list)
    peticoes: list[Peticao] = Field(default_factory=list)
    recursos: list[Recurso] = Field(default_factory=list)
    pautas: list[Pauta] = Field(default_factory=list)
    sessao: Sessao | None = None

    # Metadata
    status: int | None = None
    html: str | None = None
    extraido: str | None = None

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        extra="allow",  # Allow extra fields for backward compatibility
    )

    @field_validator("classe", mode="before")
    def validate_classe(cls, v):
        if isinstance(v, str):
            try:
                return CaseType(v)
            except ValueError:
                # If it's not a valid enum value, return as string for now
                # This allows for graceful handling of unknown case types
                return v
        return v

    @field_validator("tipo_processo", mode="before")
    def validate_tipo_processo(cls, v):
        if isinstance(v, str):
            try:
                return ProcessType(v)
            except ValueError:
                # If it's not a valid enum value, return as string for now
                return v
        return v

    @field_validator("liminar", mode="before")
    def validate_liminar(cls, v):
        # Convert list to int (0 or 1) for database compatibility
        if isinstance(v, list):
            return 1 if v else 0
        elif isinstance(v, bool):
            return 1 if v else 0
        elif isinstance(v, int):
            return v
        return v

    @field_validator("assuntos", mode="before")
    def validate_assuntos(cls, v):
        # Convert list to JSON string for database compatibility
        if isinstance(v, list):
            import json

            return json.dumps(v, ensure_ascii=False)
        return v

    @field_validator("partes", mode="before")
    def validate_partes(cls, v):
        if isinstance(v, list):
            # Handle field name mapping from '_index' to 'index'
            processed_items = []
            for item in v:
                if isinstance(item, dict) and "_index" in item:
                    item = item.copy()
                    item["index"] = item.pop("_index")
                processed_items.append(
                    Parte(**item) if isinstance(item, dict) else item
                )
            return processed_items
        return v

    @field_validator("andamentos", mode="before")
    def validate_andamentos(cls, v):
        if isinstance(v, list):
            # Handle field name mapping from 'index' to 'index_num'
            processed_items = []
            for item in v:
                if isinstance(item, dict) and "index" in item:
                    item = item.copy()
                    item["index_num"] = item.pop("index")
                processed_items.append(
                    Andamento(**item) if isinstance(item, dict) else item
                )
            return processed_items
        return v

    @field_validator("decisoes", mode="before")
    def validate_decisoes(cls, v):
        if isinstance(v, list):
            # Handle field name mapping from 'index' to 'index_num'
            processed_items = []
            for item in v:
                if isinstance(item, dict) and "index" in item:
                    item = item.copy()
                    item["index_num"] = item.pop("index")
                processed_items.append(
                    Decisao(**item) if isinstance(item, dict) else item
                )
            return processed_items
        return v

    @field_validator("deslocamentos", mode="before")
    def validate_deslocamentos(cls, v):
        if isinstance(v, list):
            # Handle field name mapping from 'index' to 'index_num'
            processed_items = []
            for item in v:
                if isinstance(item, dict) and "index" in item:
                    item = item.copy()
                    item["index_num"] = item.pop("index")
                processed_items.append(
                    Deslocamento(**item) if isinstance(item, dict) else item
                )
            return processed_items
        return v

    @field_validator("peticoes", mode="before")
    def validate_peticoes(cls, v):
        if isinstance(v, list):
            # Handle field name mapping from 'index' to 'index_num'
            processed_items = []
            for item in v:
                if isinstance(item, dict) and "index" in item:
                    item = item.copy()
                    item["index_num"] = item.pop("index")
                processed_items.append(
                    Peticao(**item) if isinstance(item, dict) else item
                )
            return processed_items
        return v

    @field_validator("recursos", mode="before")
    def validate_recursos(cls, v):
        if isinstance(v, list):
            # Handle field name mapping from 'index' to 'index_num'
            processed_items = []
            for item in v:
                if isinstance(item, dict) and "index" in item:
                    item = item.copy()
                    item["index_num"] = item.pop("index")
                processed_items.append(
                    Recurso(**item) if isinstance(item, dict) else item
                )
            return processed_items
        return v

    @field_validator("pautas", mode="before")
    def validate_pautas(cls, v):
        if isinstance(v, list):
            # Handle field name mapping from 'index' to 'index_num'
            processed_items = []
            for item in v:
                if isinstance(item, dict) and "index" in item:
                    item = item.copy()
                    item["index_num"] = item.pop("index")
                processed_items.append(
                    Pauta(**item) if isinstance(item, dict) else item
                )
            return processed_items
        return v

    @field_validator("sessao", mode="before")
    def validate_sessao(cls, v):
        if isinstance(v, dict):
            return Sessao(**v)
        return v

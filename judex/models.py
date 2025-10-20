"""
Pydantic models for STF case data validation and serialization
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .types import CaseType


class Meio(str, Enum):
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
    classe: str  # Case type as string
    meio: str | None = None  # FISICO or ELETRONICO
    publicidade: str | None = None  # PUBLICO or RESTRITO
    badges: list[str] = Field(default_factory=list)  # List of badges
    liminar: int | None = None  # Database stores as INT (0 or 1)
    relator: str | None = None
    primeiro_autor: str | None = None
    meio: Meio | None = None

    # Process details
    origem: str | None = None
    data_protocolo: str | None = None
    orgao_origem: str | None = None  # Changed from origem_orgao
    numero_origem: list[int] = Field(default_factory=list)  # List of numbers
    volumes: int | None = None
    folhas: int | None = None
    apensos: int | None = None
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
    informacoes: list[dict] = Field(default_factory=list)  # Additional field
    sessao_virtual: list[Sessao] = Field(default_factory=list)  # Changed from sessao

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
    @classmethod
    def validate_classe(cls, v):
        if isinstance(v, str):
            try:
                return CaseType(v)
            except ValueError:
                # If it's not a valid enum value, return as string for now
                # This allows for graceful handling of unknown case types
                return v
        return v

    @field_validator("meio", mode="before")
    @classmethod
    def validate_tipo_processo(cls, v):
        if isinstance(v, str):
            try:
                return Meio(v)
            except ValueError:
                # If it's not a valid enum value, return as string for now
                return v
        return v

    @field_validator("liminar", mode="before")
    @classmethod
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
    @classmethod
    def validate_assuntos(cls, v):
        # Convert list to JSON string for database compatibility
        if isinstance(v, list):
            import json

            return json.dumps(v, ensure_ascii=False)
        return v

    @field_validator("partes", mode="before")
    @classmethod
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
    @classmethod
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
    @classmethod
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
    @classmethod
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
    @classmethod
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
    @classmethod
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
    @classmethod
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

    @field_validator("sessao_virtual", mode="before")
    @classmethod
    def validate_sessao_virtual(cls, v):
        if isinstance(v, list):
            processed_items = []
            for item in v:
                if isinstance(item, dict):
                    processed_items.append(Sessao(**item))
                else:
                    processed_items.append(item)
            return processed_items
        elif isinstance(v, dict):
            return [Sessao(**v)]
        return v

    @field_validator("numero_origem", mode="before")
    @classmethod
    def validate_numero_origem(cls, v):
        if isinstance(v, list):
            return v
        elif isinstance(v, str):
            # Try to extract numbers from string
            import re

            numbers = re.findall(r"\d+", v)
            return [int(num) for num in numbers]
        return v

    @field_validator("badges", mode="before")
    @classmethod
    def validate_badges(cls, v):
        if isinstance(v, list):
            return v
        elif isinstance(v, str):
            return [v]
        return v

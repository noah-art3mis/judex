"""
STF (Supremo Tribunal Federal) types and validation
"""

from enum import Enum

from pydantic import BaseModel, field_validator


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


# Set of valid STF case types derived from the enum
STF_CASE_TYPES = frozenset([case_type.value for case_type in CaseType])


class CaseTypeValidator(BaseModel):
    """Pydantic validator for case types"""

    classe: str

    @field_validator("classe")
    @classmethod
    def validate_classe(cls, v):
        try:
            return CaseType(v)
        except ValueError:
            valid_types = [case_type.value for case_type in CaseType]
            raise ValueError(
                f"Invalid case type '{v}'. Valid types are: {', '.join(valid_types)}"
            )


def validate_case_type(classe: str) -> str:
    """Validate that the case type is a valid STF case type"""
    if classe not in STF_CASE_TYPES:
        valid_types = sorted(STF_CASE_TYPES)
        raise ValueError(
            f"Invalid case type '{classe}'. Valid types are: {', '.join(valid_types)}"
        )
    return classe


def is_valid_case_type(classe: str) -> bool:
    """Check if a case type is valid without raising an exception"""
    return classe in STF_CASE_TYPES


def get_all_case_types() -> list[str]:
    """Get all valid STF case types as a list"""
    return sorted(list(STF_CASE_TYPES))

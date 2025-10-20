"""
STF (Supremo Tribunal Federal) types and validation
"""

from pydantic import BaseModel, field_validator

from .models import CaseType

# Set of valid STF case types with full names as comments
STF_CASE_TYPES = frozenset(
    [
        "AC",  # Ação Cível
        "ACO",  # Ação Cível Originária
        "ADC",  # Ação Declaratória de Constitucionalidade
        "ADI",  # Ação Direta de Inconstitucionalidade
        "ADO",  # Ação Direta de Inconstitucionalidade por Omissão
        "ADPF",  # Arguição de Descumprimento de Preceito Fundamental
        "AI",  # Ação Interlocutória
        "AImp",  # Ação de Improbidade Administrativa
        "AO",  # Ação Originária
        "AOE",  # Ação Originária Especial
        "AP",  # Ação Penal
        "AR",  # Ação Rescisória
        "ARE",  # Agravo em Recurso Extraordinário
        "AS",  # Ação de Suspensão
        "CC",  # Conflito de Competência
        "Cm",  # Comunicado
        "EI",  # Embargos Infringentes
        "EL",  # Embargos de Declaração
        "EP",  # Embargos de Petição
        "Ext",  # Extradição
        "HC",  # Habeas Corpus
        "HD",  # Habeas Data
        "IF",  # Inquérito Federal
        "Inq",  # Inquérito
        "MI",  # Mandado de Injunção
        "MS",  # Mandado de Segurança
        "PADM",  # Processo Administrativo Disciplinar Militar
        "Pet",  # Petição
        "PPE",  # Processo de Prestação de Contas Eleitorais
        "PSV",  # Processo de Suspensão de Vigência
        "RC",  # Recurso Cível
        "Rcl",  # Reclamação
        "RE",  # Recurso Extraordinário
        "RHC",  # Recurso em Habeas Corpus
        "RHD",  # Recurso em Habeas Data
        "RMI",  # Recurso em Mandado de Injunção
        "RMS",  # Recurso em Mandado de Segurança
        "RvC",  # Recurso em Violação de Cláusula de Tratado
        "SE",  # Suspensão de Eficácia
        "SIRDR",  # Suspensão de Inquérito ou Recurso com Deficiência
        "SL",  # Suspensão de Liminar
        "SS",  # Suspensão de Segurança
        "STA",  # Suspensão de Tutela Antecipada
        "STP",  # Suspensão de Tutela Provisória
        "TPA",  # Tutela Provisória Antecipada
    ]
)


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
            raise ValueError(f"Invalid case type '{v}'. Valid types are: {', '.join(valid_types)}")


def validate_case_type(classe: str) -> str:
    """Validate that the case type is a valid STF case type"""
    if classe not in STF_CASE_TYPES:
        valid_types = sorted(STF_CASE_TYPES)
        raise ValueError(f"Invalid case type '{classe}'. Valid types are: {', '.join(valid_types)}")
    return classe


def is_valid_case_type(classe: str) -> bool:
    """Check if a case type is valid without raising an exception"""
    return classe in STF_CASE_TYPES


def get_all_case_types() -> list[str]:
    """Get all valid STF case types as a list"""
    return sorted(list(STF_CASE_TYPES))

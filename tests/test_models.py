"""
Unit tests for Pydantic models
"""

import json

import pytest
from pydantic import ValidationError

from judex.models import (
    Andamento,
    CaseType,
    Parte,
    ProcessType,
    STFCaseModel,
)


class TestCaseType:
    """Test CaseType enum"""

    def test_valid_case_types(self):
        """Test that all valid case types are accepted"""
        valid_cases = ["ADI", "ADPF", "HC", "MS", "RE"]
        for case in valid_cases:
            assert CaseType(case) == case

    def test_case_type_validation(self):
        """Test case type validation in STFCaseModel"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
        }
        case = STFCaseModel(**data)
        assert case.classe == "ADI"  # Now returns string, not enum

    def test_invalid_case_type(self):
        """Test that invalid case types are handled gracefully"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "INVALID",
        }
        case = STFCaseModel(**data)
        assert case.classe == "INVALID"  # Should fallback to string


class TestProcessType:
    """Test ProcessType enum"""

    def test_valid_process_types(self):
        """Test that valid process types are accepted"""
        assert ProcessType("Físico") == ProcessType.FISICO
        assert ProcessType("Eletrônico") == ProcessType.ELETRONICO

    def test_process_type_validation(self):
        """Test process type validation in STFCaseModel"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "tipo_processo": "Físico",
        }
        case = STFCaseModel(**data)
        assert case.tipo_processo == ProcessType.FISICO


class TestParte:
    """Test Parte model"""

    def test_partes_creation(self):
        """Test creating Parte instances"""
        parte = Parte(index=1, tipo="Autor", nome="João Silva")
        assert parte.index == 1
        assert parte.tipo == "Autor"
        assert parte.nome == "João Silva"

    def test_partes_optional_fields(self):
        """Test Parte with optional fields"""
        parte = Parte()
        assert parte.index is None
        assert parte.tipo is None
        assert parte.nome is None

    def test_partes_extra_fields(self):
        """Test Parte allows extra fields"""
        parte = Parte(index=1, extra_field="value")
        assert parte.index == 1
        assert hasattr(parte, "extra_field")


class TestAndamento:
    """Test Andamento model"""

    def test_andamento_creation(self):
        """Test creating Andamento instances"""
        andamento = Andamento(
            index_num=1,
            data="2023-01-01",
            nome="Distribuição",
            complemento="Test complement",
            julgador="Ministro Test",
        )
        assert andamento.index_num == 1
        assert andamento.data == "2023-01-01"
        assert andamento.nome == "Distribuição"

    def test_andamento_field_mapping(self):
        """Test field mapping from 'index' to 'index_num'"""
        data = {
            "index": 1,
            "data": "2023-01-01",
            "nome": "Test",
        }
        andamento = Andamento(**data)
        # The field mapping happens in the STFCaseModel validator, not in Andamento directly
        assert (
            andamento.index_num is None
        )  # index_num is None because we passed 'index'
        assert hasattr(andamento, "index")  # The original 'index' field should be there


class TestSTFCaseModel:
    """Test main STFCaseModel"""

    def test_minimal_valid_case(self):
        """Test creating a minimal valid case"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
        }
        case = STFCaseModel(**data)
        assert case.processo_id == 123
        assert case.incidente == 456
        assert case.classe == CaseType.ADI

    def test_liminar_conversion(self):
        """Test liminar field conversion from list to int"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "liminar": ["liminar1", "liminar2"],
        }
        case = STFCaseModel(**data)
        assert case.liminar == 1

        # Test empty list
        data["liminar"] = []
        case = STFCaseModel(**data)
        assert case.liminar == 0

        # Test boolean
        data["liminar"] = True
        case = STFCaseModel(**data)
        assert case.liminar == 1

        # Test integer
        data["liminar"] = 0
        case = STFCaseModel(**data)
        assert case.liminar == 0

    def test_assuntos_conversion(self):
        """Test assuntos field conversion from list to JSON string"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "assuntos": ["Direito Constitucional", "Direito Administrativo"],
        }
        case = STFCaseModel(**data)
        assert isinstance(case.assuntos, str)
        parsed = json.loads(case.assuntos)
        assert parsed == ["Direito Constitucional", "Direito Administrativo"]

    def test_andamentos_field_mapping(self):
        """Test andamentos field mapping from 'index' to 'index_num'"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "andamentos": [
                {"index": 1, "data": "2023-01-01", "nome": "Distribuição"},
                {"index": 2, "data": "2023-01-02", "nome": "Despacho"},
            ],
        }
        case = STFCaseModel(**data)
        assert len(case.andamentos) == 2
        assert case.andamentos[0].index_num == 1
        assert case.andamentos[1].index_num == 2

    def test_decisoes_field_mapping(self):
        """Test decisoes field mapping from 'index' to 'index_num'"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "decisoes": [
                {"index": 1, "data": "2023-01-01", "nome": "Decisão 1"},
            ],
        }
        case = STFCaseModel(**data)
        assert len(case.decisoes) == 1
        assert case.decisoes[0].index_num == 1

    def test_deslocamentos_field_mapping(self):
        """Test deslocamentos field mapping"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "deslocamentos": [
                {
                    "index": 1,
                    "data_enviado": "2023-01-01",
                    "data_recebido": "2023-01-02",
                    "enviado_por": "STF",
                    "recebido_por": "TRF",
                }
            ],
        }
        case = STFCaseModel(**data)
        assert len(case.deslocamentos) == 1
        assert case.deslocamentos[0].index_num == 1
        assert case.deslocamentos[0].data_enviado == "2023-01-01"

    def test_peticoes_field_mapping(self):
        """Test peticoes field mapping"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "peticoes": [
                {
                    "index": 1,
                    "data": "2023-01-01",
                    "tipo": "Petição Inicial",
                    "autor": "João Silva",
                }
            ],
        }
        case = STFCaseModel(**data)
        assert len(case.peticoes) == 1
        assert case.peticoes[0].index_num == 1
        assert case.peticoes[0].tipo == "Petição Inicial"

    def test_recursos_field_mapping(self):
        """Test recursos field mapping"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "recursos": [
                {
                    "index": 1,
                    "data": "2023-01-01",
                    "nome": "Recurso Extraordinário",
                    "autor": "João Silva",
                }
            ],
        }
        case = STFCaseModel(**data)
        assert len(case.recursos) == 1
        assert case.recursos[0].index_num == 1
        assert case.recursos[0].autor == "João Silva"

    def test_pautas_field_mapping(self):
        """Test pautas field mapping"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "pautas": [
                {
                    "index": 1,
                    "data": "2023-01-01",
                    "nome": "Julgamento",
                    "relator": "Ministro Silva",
                }
            ],
        }
        case = STFCaseModel(**data)
        assert len(case.pautas) == 1
        assert case.pautas[0].index_num == 1
        assert case.pautas[0].relator == "Ministro Silva"

    def test_sessao_validation(self):
        """Test sessao field validation"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "sessao": {
                "data": "2023-01-01",
                "tipo": "Plenário",
                "numero": "123",
                "relator": "Ministro Silva",
            },
        }
        case = STFCaseModel(**data)
        assert case.sessao is not None
        assert case.sessao.data == "2023-01-01"
        assert case.sessao.tipo == "Plenário"

    def test_required_fields(self):
        """Test that required fields are enforced"""
        # Missing processo_id
        with pytest.raises(ValidationError):
            STFCaseModel(incidente=456, classe="ADI")

        # Missing incidente
        with pytest.raises(ValidationError):
            STFCaseModel(processo_id=123, classe="ADI")

        # Missing classe
        with pytest.raises(ValidationError):
            STFCaseModel(processo_id=123, incidente=456)

    def test_optional_fields_defaults(self):
        """Test that optional fields have correct defaults"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
        }
        case = STFCaseModel(**data)
        assert case.numero_unico is None
        assert case.tipo_processo is None
        assert case.liminar is None
        assert case.relator is None
        assert case.origem is None
        assert case.data_protocolo is None
        assert case.origem_orgao is None
        assert case.autor1 is None
        assert case.assuntos is None
        assert case.partes == []
        assert case.andamentos == []
        assert case.decisoes == []
        assert case.deslocamentos == []
        assert case.peticoes == []
        assert case.recursos == []
        assert case.pautas == []
        assert case.sessao is None
        assert case.status is None
        assert case.html is None
        assert case.extraido is None

    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed for backward compatibility"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "extra_field": "extra_value",
        }
        case = STFCaseModel(**data)
        assert hasattr(case, "extra_field")
        assert case.extra_field == "extra_value"


class TestComplexValidation:
    """Test complex validation scenarios"""

    def test_full_case_validation(self):
        """Test validation of a complete case with all fields"""
        data = {
            "processo_id": 123,
            "incidente": 456,
            "numero_unico": "ADI 123456",
            "classe": "ADI",
            "tipo_processo": "Eletrônico",
            "liminar": ["Liminar 1", "Liminar 2"],
            "relator": "Ministro Silva",
            "origem": "STF",
            "data_protocolo": "2023-01-01",
            "origem_orgao": "STF",
            "autor1": "João Silva",
            "assuntos": ["Direito Constitucional", "Direito Administrativo"],
            "partes": [
                {"_index": 1, "tipo": "Autor", "nome": "João Silva"},
                {"_index": 2, "tipo": "Réu", "nome": "Estado"},
            ],
            "andamentos": [
                {"index": 1, "data": "2023-01-01", "nome": "Distribuição"},
                {"index": 2, "data": "2023-01-02", "nome": "Despacho"},
            ],
            "decisoes": [
                {
                    "index": 1,
                    "data": "2023-01-01",
                    "nome": "Decisão 1",
                    "link": "http://example.com",
                },
            ],
            "deslocamentos": [
                {
                    "index": 1,
                    "data_enviado": "2023-01-01",
                    "data_recebido": "2023-01-02",
                    "enviado_por": "STF",
                    "recebido_por": "TRF",
                    "guia": "123456",
                }
            ],
            "peticoes": [
                {
                    "index": 1,
                    "data": "2023-01-01",
                    "tipo": "Petição Inicial",
                    "autor": "João Silva",
                    "recebido_data": "2023-01-01",
                    "recebido_por": "Secretaria",
                }
            ],
            "recursos": [
                {
                    "index": 1,
                    "data": "2023-01-01",
                    "nome": "Recurso Extraordinário",
                    "autor": "João Silva",
                }
            ],
            "pautas": [
                {
                    "index": 1,
                    "data": "2023-01-01",
                    "nome": "Julgamento",
                    "relator": "Ministro Silva",
                }
            ],
            "sessao": {
                "data": "2023-01-01",
                "tipo": "Plenário",
                "numero": "123",
                "relator": "Ministro Silva",
            },
            "status": 200,
            "html": "<html>...</html>",
            "extraido": "2023-01-01T10:00:00Z",
        }

        case = STFCaseModel(**data)

        # Test basic fields
        assert case.processo_id == 123
        assert case.incidente == 456
        assert case.numero_unico == "ADI 123456"
        assert case.classe == CaseType.ADI
        assert case.tipo_processo == ProcessType.ELETRONICO

        # Test converted fields
        assert case.liminar == 1
        assert isinstance(case.assuntos, str)
        parsed_assuntos = json.loads(case.assuntos)
        assert parsed_assuntos == ["Direito Constitucional", "Direito Administrativo"]

        # Test field mapping
        assert len(case.andamentos) == 2
        assert case.andamentos[0].index_num == 1
        assert case.andamentos[1].index_num == 2

        assert len(case.decisoes) == 1
        assert case.decisoes[0].index_num == 1
        assert case.decisoes[0].link == "http://example.com"

        # Test metadata
        assert case.status == 200
        assert case.html == "<html>...</html>"
        assert case.extraido == "2023-01-01T10:00:00Z"

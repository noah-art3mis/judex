"""
Standalone unit tests for the normalized database structure.
"""

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import database module directly

spec = importlib.util.spec_from_file_location(
    "database", project_root / "judex" / "database.py"
)
database = importlib.util.module_from_spec(spec)
spec.loader.exec_module(database)

# Get the functions we need
init_database = database.init_database
processo_write = database.processo_write
get_complete_processo = database.get_complete_processo
get_processo_andamentos = database.get_processo_andamentos
get_processo_partes = database.get_processo_partes
get_processo_decisoes = database.get_processo_decisoes
get_processo_deslocamentos = database.get_processo_deslocamentos
get_processo_peticoes = database.get_processo_peticoes
get_processo_recursos = database.get_processo_recursos
get_processo_pautas = database.get_processo_pautas


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_path = tmp_file.name

    init_database(db_path)
    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_processo_data():
    """Sample processo data for testing."""
    return {
        "numero_unico": "0004022-92.1988.0.01.0000",
        "incidente": 4379376,
        "processo_id": 4916,
        "classe": "ADI",
        "tipo_processo": "Eletrônico",
        "liminar": 0,
        "relator": "MIN. CÁRMEN LÚCIA",
        "origem": "GOVERNADOR DO ESTADO DO RIO DE JANEIRO",
        "origem_orgao": "TRIBUNAL DE JUSTIÇA DO ESTADO DO RIO DE JANEIRO",
        "data_protocolo": "2013-03-15T00:00:00Z",
        "autor1": "GOVERNADOR DO ESTADO DO RIO DE JANEIRO",
        "assuntos": [
            "DIREITO ADMINISTRATIVO E OUTRAS MATÉRIAS DE DIREITO PÚBLICO | Controle de Constitucionalidade"
        ],
        "partes_total": [
            {
                "_index": 1,
                "tipo": "REQTE.(S)",
                "nome": "GOVERNADOR DO ESTADO DO RIO DE JANEIRO",
            },
            {"_index": 2, "tipo": "REQDO.(S)", "nome": "PRESIDENTE DA REPÚBLICA"},
            {"_index": 3, "tipo": "REQDO.(S)", "nome": "CONGRESSO NACIONAL"},
        ],
        "andamentos": [
            {
                "index": 202,
                "data": "27/06/2025",
                "nome": "Petição",
                "complemento": "Procuração/Substabelecimento - Petição: 88567 Data: 27/06/2025, às 11:40:43",
                "julgador": None,
            },
            {
                "index": 201,
                "data": "23/06/2025",
                "nome": "Petição",
                "complemento": "Amicus curiae - Petição: 85754 Data: 23/06/2025, às 16:38:18",
                "julgador": None,
            },
            {
                "index": 200,
                "data": "18/03/2024",
                "nome": "Petição",
                "complemento": "Manifestação - Petição: 29642 Data: 18/03/2024, às 22:45:09",
                "julgador": None,
            },
        ],
        "decisoes": [
            {
                "index": 125,
                "data": "28/11/2013",
                "nome": "Adotado rito do Art. 12, da Lei 9.868/99",
                "julgador": "MIN. CÁRMEN LÚCIA",
                "complemento": 'em 21/11/2013: "Rquisitem-se informações às autoridades requeridas..."',
                "link": None,
            }
        ],
        "deslocamentos": [
            {
                "index": 35,
                "data_enviado": "14/06/2023",
                "data_recebido": "14/06/2023",
                "enviado_por": "GERÊNCIA DE PROCESSOS",
                "recebido_por": "PRESIDÊNCIA",
                "guia": "123456",
            },
            {
                "index": 34,
                "data_enviado": "10/06/2023",
                "data_recebido": "12/06/2023",
                "enviado_por": "SECRETARIA JUDICIÁRIA",
                "recebido_por": "GABINETE",
                "guia": "123455",
            },
        ],
        "peticoes": [
            {
                "index": 83,
                "data": "Peticionado em 27/06/2025",
                "tipo": "88567/2025",
                "autor": None,
                "recebido_data": "27/06/2025 11:40:43",
                "recebido_por": "DIVISÃO DE PROCESSOS ORIGINARIOS",
            },
            {
                "index": 82,
                "data": "Peticionado em 23/06/2025",
                "tipo": "85754/2025",
                "autor": None,
                "recebido_data": "23/06/2025 16:38:18",
                "recebido_por": "DIVISÃO DE PROCESSOS ORIGINARIOS",
            },
        ],
        "recursos": [
            {
                "index": 125,
                "data": "28/11/2013",
                "nome": "Adotado rito do Art. 12, da Lei 9.868/99",
                "julgador": "MIN. CÁRMEN LÚCIA",
                "complemento": "em 21/11/2013",
                "autor": None,
            }
        ],
        "pautas": [
            {
                "index": 109,
                "data": "13/05/2014",
                "nome": "Pauta publicada no DJE - Plenário",
                "complemento": "PAUTA Nº 22/2014. DJE nº 90, divulgado em 12/05/2014",
                "relator": "MIN. CÁRMEN LÚCIA",
            },
            {
                "index": 108,
                "data": "09/05/2014",
                "nome": "Inclua-se em pauta - minuta extraída",
                "complemento": "Pleno em 09/05/2014 14:13:39",
                "relator": "MIN. CÁRMEN LÚCIA",
            },
        ],
    }


class TestDatabaseStructure:
    """Test the normalized database structure."""

    def test_database_initialization(self, temp_db):
        """Test that database initializes correctly."""
        assert os.path.exists(temp_db)

    def test_processo_write(self, temp_db, sample_processo_data):
        """Test saving processo data."""
        result = processo_write(temp_db, sample_processo_data)
        assert result is True

    def test_get_complete_processo(self, temp_db, sample_processo_data):
        """Test retrieving complete processo data."""
        # Save data first
        processo_write(temp_db, sample_processo_data)

        # Retrieve complete data
        complete_data = get_complete_processo(
            temp_db, sample_processo_data["numero_unico"]
        )

        # Verify main data
        assert complete_data["numero_unico"] == sample_processo_data["numero_unico"]
        assert complete_data["incidente"] == sample_processo_data["incidente"]
        assert complete_data["classe"] == sample_processo_data["classe"]
        assert complete_data["relator"] == sample_processo_data["relator"]

        # Verify normalized data is included
        assert "andamentos" in complete_data
        assert "partes" in complete_data
        assert "decisoes" in complete_data
        assert "deslocamentos" in complete_data
        assert "peticoes" in complete_data
        assert "recursos" in complete_data
        assert "pautas" in complete_data


class TestNormalizedTables:
    """Test individual normalized tables."""

    def test_partes_table(self, temp_db, sample_processo_data):
        """Test partes table functionality."""
        processo_write(temp_db, sample_processo_data)

        partes = get_processo_partes(temp_db, sample_processo_data["numero_unico"])

        assert len(partes) == 3
        assert partes[0]["nome"] == "GOVERNADOR DO ESTADO DO RIO DE JANEIRO"
        assert partes[0]["tipo"] == "REQTE.(S)"
        assert partes[0]["numero_unico"] == sample_processo_data["numero_unico"]

    def test_andamentos_table(self, temp_db, sample_processo_data):
        """Test andamentos table functionality."""
        processo_write(temp_db, sample_processo_data)

        andamentos = get_processo_andamentos(
            temp_db, sample_processo_data["numero_unico"]
        )

        assert len(andamentos) == 3
        assert andamentos[0]["data"] == "27/06/2025"
        assert andamentos[0]["nome"] == "Petição"
        assert andamentos[0]["numero_unico"] == sample_processo_data["numero_unico"]

    def test_decisoes_table(self, temp_db, sample_processo_data):
        """Test decisoes table functionality."""
        processo_write(temp_db, sample_processo_data)

        decisoes = get_processo_decisoes(temp_db, sample_processo_data["numero_unico"])

        assert len(decisoes) == 1
        assert decisoes[0]["julgador"] == "MIN. CÁRMEN LÚCIA"
        assert decisoes[0]["numero_unico"] == sample_processo_data["numero_unico"]

    def test_deslocamentos_table(self, temp_db, sample_processo_data):
        """Test deslocamentos table functionality."""
        processo_write(temp_db, sample_processo_data)

        deslocamentos = get_processo_deslocamentos(
            temp_db, sample_processo_data["numero_unico"]
        )

        assert len(deslocamentos) == 2
        assert deslocamentos[0]["enviado_por"] == "GERÊNCIA DE PROCESSOS"
        assert deslocamentos[0]["numero_unico"] == sample_processo_data["numero_unico"]

    def test_peticoes_table(self, temp_db, sample_processo_data):
        """Test peticoes table functionality."""
        processo_write(temp_db, sample_processo_data)

        peticoes = get_processo_peticoes(temp_db, sample_processo_data["numero_unico"])

        assert len(peticoes) == 2
        assert peticoes[0]["tipo"] == "88567/2025"
        assert peticoes[0]["numero_unico"] == sample_processo_data["numero_unico"]

    def test_recursos_table(self, temp_db, sample_processo_data):
        """Test recursos table functionality."""
        processo_write(temp_db, sample_processo_data)

        recursos = get_processo_recursos(temp_db, sample_processo_data["numero_unico"])

        assert len(recursos) == 1
        assert recursos[0]["julgador"] == "MIN. CÁRMEN LÚCIA"
        assert recursos[0]["numero_unico"] == sample_processo_data["numero_unico"]

    def test_pautas_table(self, temp_db, sample_processo_data):
        """Test pautas table functionality."""
        processo_write(temp_db, sample_processo_data)

        pautas = get_processo_pautas(temp_db, sample_processo_data["numero_unico"])

        assert len(pautas) == 2
        assert pautas[0]["relator"] == "MIN. CÁRMEN LÚCIA"
        assert pautas[0]["numero_unico"] == sample_processo_data["numero_unico"]


class TestEdgeCases:
    """Test edge cases and complex scenarios."""

    def test_empty_data(self, temp_db):
        """Test handling of empty JSON arrays."""
        empty_data = {
            "numero_unico": "0000000-00.0000.0.00.0000",
            "incidente": 9999999,
            "processo_id": 9999,
            "classe": "ADI",
            "tipo_processo": "Eletrônico",
            "liminar": 0,
            "relator": "TEST MINISTER",
            "origem": "TEST ORIGIN",
            "origem_orgao": "TEST ORG",
            "data_protocolo": "2023-01-01T00:00:00Z",
            "autor1": "TEST AUTHOR",
            "assuntos": [],
            "partes_total": [],
            "andamentos": [],
            "decisoes": [],
            "deslocamentos": [],
            "peticoes": [],
            "recursos": [],
            "pautas": [],
        }

        result = processo_write(temp_db, empty_data)
        assert result is True

        complete_data = get_complete_processo(temp_db, empty_data["numero_unico"])
        assert len(complete_data["partes"]) == 0
        assert len(complete_data["andamentos"]) == 0
        assert len(complete_data["decisoes"]) == 0

    def test_unicode_data(self, temp_db):
        """Test handling of Unicode and special characters."""
        unicode_data = {
            "numero_unico": "0000002-00.0000.0.00.0000",
            "incidente": 7777777,
            "processo_id": 7777,
            "classe": "ADI",
            "tipo_processo": "Eletrônico",
            "liminar": 0,
            "relator": "MIN. CÁRMEN LÚCIA",
            "origem": "GOVERNADOR DO ESTADO DO RIO DE JANEIRO",
            "origem_orgao": "TRIBUNAL DE JUSTIÇA DO ESTADO DO RIO DE JANEIRO",
            "data_protocolo": "2023-01-01T00:00:00Z",
            "autor1": "GOVERNADOR DO ESTADO DO RIO DE JANEIRO",
            "assuntos": [
                "DIREITO ADMINISTRATIVO E OUTRAS MATÉRIAS DE DIREITO PÚBLICO | Controle de Constitucionalidade"
            ],
            "partes_total": [
                {
                    "_index": 1,
                    "tipo": "REQTE.(S)",
                    "nome": "GOVERNADOR DO ESTADO DO RIO DE JANEIRO",
                },
                {"_index": 2, "tipo": "REQDO.(S)", "nome": "PRESIDENTE DA REPÚBLICA"},
            ],
            "andamentos": [
                {
                    "index": 1,
                    "data": "27/06/2025",
                    "nome": "Petição",
                    "complemento": "Procuração/Substabelecimento - Petição: 88567 Data: 27/06/2025, às 11:40:43",
                    "julgador": None,
                },
                {
                    "index": 2,
                    "data": "23/06/2025",
                    "nome": "Petição",
                    "complemento": "Amicus curiae - Petição: 85754 Data: 23/06/2025, às 16:38:18",
                    "julgador": None,
                },
            ],
            "decisoes": [
                {
                    "index": 1,
                    "data": "28/11/2013",
                    "nome": "Adotado rito do Art. 12, da Lei 9.868/99",
                    "julgador": "MIN. CÁRMEN LÚCIA",
                    "complemento": 'em 21/11/2013: "Rquisitem-se informações às autoridades requeridas, que deverão prestá-las no prazo máximo de dez dias. Na seqüência, com base no art. 12 da Lei n. 9868/99, dê-se vista, sucessivamente, ao Advogado-eral da União e ao Procurador-Geral da República no prazo máximo de cnco dias a cada qual. Publique-se."',
                    "link": None,
                }
            ],
            "deslocamentos": [],
            "peticoes": [],
            "recursos": [],
            "pautas": [],
        }

        result = processo_write(temp_db, unicode_data)
        assert result is True

        complete_data = get_complete_processo(temp_db, unicode_data["numero_unico"])
        assert complete_data["relator"] == "MIN. CÁRMEN LÚCIA"
        assert "CÁRMEN LÚCIA" in complete_data["decisoes"][0]["julgador"]
        assert "seqüência" in complete_data["decisoes"][0]["complemento"]

    def test_data_updates(self, temp_db, sample_processo_data):
        """Test data updates and replacements."""
        # Save initial data
        processo_write(temp_db, sample_processo_data)

        # Update data
        updated_data = sample_processo_data.copy()
        updated_data["relator"] = "MIN. ALEXANDRE DE MORAES"
        updated_data["andamentos"].append(
            {
                "index": 203,
                "data": "28/06/2025",
                "nome": "Nova Petição",
                "complemento": "Teste de atualização",
                "julgador": None,
            }
        )

        result = processo_write(temp_db, updated_data)
        assert result is True

        # Verify update
        updated_complete = get_complete_processo(
            temp_db, sample_processo_data["numero_unico"]
        )
        assert updated_complete["relator"] == "MIN. ALEXANDRE DE MORAES"
        assert len(updated_complete["andamentos"]) == 4  # Original 3 + 1 new


class TestForeignKeys:
    """Test foreign key relationships."""

    def test_foreign_key_relationships(self, temp_db, sample_processo_data):
        """Test that all normalized data has correct foreign key relationships."""
        processo_write(temp_db, sample_processo_data)

        complete_data = get_complete_processo(
            temp_db, sample_processo_data["numero_unico"]
        )

        # Verify all normalized data has correct numero_unico
        for parte in complete_data["partes"]:
            assert parte["numero_unico"] == sample_processo_data["numero_unico"]

        for andamento in complete_data["andamentos"]:
            assert andamento["numero_unico"] == sample_processo_data["numero_unico"]

        for decisao in complete_data["decisoes"]:
            assert decisao["numero_unico"] == sample_processo_data["numero_unico"]

        for deslocamento in complete_data["deslocamentos"]:
            assert deslocamento["numero_unico"] == sample_processo_data["numero_unico"]

        for peticao in complete_data["peticoes"]:
            assert peticao["numero_unico"] == sample_processo_data["numero_unico"]

        for recurso in complete_data["recursos"]:
            assert recurso["numero_unico"] == sample_processo_data["numero_unico"]

        for pauta in complete_data["pautas"]:
            assert pauta["numero_unico"] == sample_processo_data["numero_unico"]

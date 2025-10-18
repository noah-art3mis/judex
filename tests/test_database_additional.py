"""
Additional database tests to verify functionality not covered in existing tests.
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
mark_error = database.mark_error
processo_read = database.processo_read
processo_read_all = database.processo_read_all
has_recent_data = database.has_recent_data
get_existing_processo_ids = database.get_existing_processo_ids
get_failed_processo_ids = database.get_failed_processo_ids


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
        "partes_total": [],
        "andamentos": [],
        "decisoes": [],
        "deslocamentos": [],
        "peticoes": [],
        "recursos": [],
        "pautas": [],
    }


class TestDatabaseReadOperations:
    """Test database read operations."""

    def test_processo_read_existing(self, temp_db, sample_processo_data):
        """Test reading an existing processo."""
        # Save data first
        processo_write(temp_db, sample_processo_data)

        # Read the data
        result = processo_read(temp_db, sample_processo_data["numero_unico"])

        assert result is not None
        assert result != {}  # Should not be empty
        # The result is a tuple, so we check the first few elements
        assert (
            result[0] == sample_processo_data["numero_unico"]
        )  # numero_unico is first column
        assert (
            result[1] == sample_processo_data["incidente"]
        )  # incidente is second column
        assert result[3] == sample_processo_data["classe"]  # classe is fourth column

    def test_processo_read_nonexistent(self, temp_db):
        """Test reading a non-existent processo."""
        result = processo_read(temp_db, "nonexistent")
        assert result == {}

    def test_processo_read_all_empty(self, temp_db):
        """Test reading all processos from empty database."""
        result = processo_read_all(temp_db)
        assert result == []

    def test_processo_read_all_with_data(self, temp_db, sample_processo_data):
        """Test reading all processos with data."""
        # Save multiple processos
        processo_write(temp_db, sample_processo_data)

        # Create another processo
        another_processo = sample_processo_data.copy()
        another_processo["numero_unico"] = "0004023-92.1988.0.01.0000"
        another_processo["incidente"] = 4379377
        another_processo["processo_id"] = 4917
        processo_write(temp_db, another_processo)

        # Read all
        result = processo_read_all(temp_db)
        assert len(result) == 2

        # Verify both are present
        numero_unicos = {row[0] for row in result}  # numero_unico is first column
        assert sample_processo_data["numero_unico"] in numero_unicos
        assert another_processo["numero_unico"] in numero_unicos


class TestErrorHandling:
    """Test error handling and marking."""

    def test_mark_error_existing_processo(self, temp_db, sample_processo_data):
        """Test marking an existing processo as having an error."""
        # Save data first
        processo_write(temp_db, sample_processo_data)

        # Mark as error
        error_message = "Test error message"
        result = mark_error(
            temp_db, sample_processo_data["numero_unico"], error_message
        )

        assert result is True

        # Verify error was marked
        processo_data = processo_read(temp_db, sample_processo_data["numero_unico"])
        # error_message is the 14th column (index 13) in the processos table
        assert processo_data[13] == error_message

    def test_mark_error_nonexistent_processo(self, temp_db):
        """Test marking a non-existent processo as having an error."""
        result = mark_error(temp_db, "nonexistent", "Test error")
        assert result is True  # Function should not fail even if processo doesn't exist

    def test_processo_write_invalid_data(self, temp_db):
        """Test writing invalid processo data."""
        # Missing required fields
        invalid_data = {
            "numero_unico": "test",
            # Missing incidente, processo_id
        }

        result = processo_write(temp_db, invalid_data)
        assert result is False

    def test_processo_write_empty_data(self, temp_db):
        """Test writing completely empty data."""
        result = processo_write(temp_db, {})
        assert result is False


class TestRecentDataFunctions:
    """Test functions for checking recent data."""

    def test_has_recent_data_no_data(self, temp_db):
        """Test has_recent_data with no data in database."""
        result = has_recent_data(temp_db, 12345, "ADI", 24)
        assert result is False

    def test_has_recent_data_with_recent_data(self, temp_db, sample_processo_data):
        """Test has_recent_data with recent data."""
        # Save data
        processo_write(temp_db, sample_processo_data)

        # Check for recent data
        result = has_recent_data(
            temp_db,
            sample_processo_data["processo_id"],
            sample_processo_data["classe"],
            24,
        )
        assert result is True

    def test_has_recent_data_with_old_data(self, temp_db, sample_processo_data):
        """Test has_recent_data with old data."""
        # Save data
        processo_write(temp_db, sample_processo_data)

        # Manually update the created_at to be old
        import sqlite3

        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE processos SET created_at = datetime('now', '-48 hours') WHERE numero_unico = ?",
                (sample_processo_data["numero_unico"],),
            )
            conn.commit()

        # Check for recent data (should be False for 24-hour window)
        result = has_recent_data(
            temp_db,
            sample_processo_data["processo_id"],
            sample_processo_data["classe"],
            24,
        )
        assert result is False

    def test_has_recent_data_with_error(self, temp_db, sample_processo_data):
        """Test has_recent_data with errored processo."""
        # Save data
        processo_write(temp_db, sample_processo_data)

        # Mark as error
        mark_error(temp_db, sample_processo_data["numero_unico"], "Test error")

        # Check for recent data (should be False because of error)
        result = has_recent_data(
            temp_db,
            sample_processo_data["processo_id"],
            sample_processo_data["classe"],
            24,
        )
        assert result is False


class TestExistingProcessoIds:
    """Test functions for getting existing processo IDs."""

    def test_get_existing_processo_ids_empty(self, temp_db):
        """Test get_existing_processo_ids with empty database."""
        result = get_existing_processo_ids(temp_db, "ADI", 24)
        assert result == set()

    def test_get_existing_processo_ids_with_data(self, temp_db, sample_processo_data):
        """Test get_existing_processo_ids with data."""
        # Save data
        processo_write(temp_db, sample_processo_data)

        # Get existing IDs
        result = get_existing_processo_ids(temp_db, sample_processo_data["classe"], 24)
        assert sample_processo_data["processo_id"] in result

    def test_get_existing_processo_ids_different_classe(
        self, temp_db, sample_processo_data
    ):
        """Test get_existing_processo_ids with different classe."""
        # Save data
        processo_write(temp_db, sample_processo_data)

        # Get existing IDs for different classe
        result = get_existing_processo_ids(temp_db, "ADPF", 24)
        assert result == set()

    def test_get_existing_processo_ids_with_errors(self, temp_db, sample_processo_data):
        """Test get_existing_processo_ids excludes errored processos."""
        # Save data
        processo_write(temp_db, sample_processo_data)

        # Mark as error
        mark_error(temp_db, sample_processo_data["numero_unico"], "Test error")

        # Get existing IDs (should exclude errored ones)
        result = get_existing_processo_ids(temp_db, sample_processo_data["classe"], 24)
        assert sample_processo_data["processo_id"] not in result


class TestFailedProcessoIds:
    """Test functions for getting failed processo IDs."""

    def test_get_failed_processo_ids_empty(self, temp_db):
        """Test get_failed_processo_ids with empty database."""
        result = get_failed_processo_ids(temp_db, "ADI", 24)
        assert result == set()

    def test_get_failed_processo_ids_with_errors(self, temp_db, sample_processo_data):
        """Test get_failed_processo_ids with errored processos."""
        # Save data
        processo_write(temp_db, sample_processo_data)

        # Mark as error
        mark_error(temp_db, sample_processo_data["numero_unico"], "Test error")

        # Get failed IDs
        result = get_failed_processo_ids(temp_db, sample_processo_data["classe"], 24)
        assert sample_processo_data["processo_id"] in result

    def test_get_failed_processo_ids_without_errors(
        self, temp_db, sample_processo_data
    ):
        """Test get_failed_processo_ids without errors."""
        # Save data without errors
        processo_write(temp_db, sample_processo_data)

        # Get failed IDs (should be empty)
        result = get_failed_processo_ids(temp_db, sample_processo_data["classe"], 24)
        assert result == set()

    def test_get_failed_processo_ids_different_classe(
        self, temp_db, sample_processo_data
    ):
        """Test get_failed_processo_ids with different classe."""
        # Save data and mark as error
        processo_write(temp_db, sample_processo_data)
        mark_error(temp_db, sample_processo_data["numero_unico"], "Test error")

        # Get failed IDs for different classe
        result = get_failed_processo_ids(temp_db, "ADPF", 24)
        assert result == set()


class TestDatabaseConstraints:
    """Test database constraints and validation."""

    def test_unique_constraints(self, temp_db, sample_processo_data):
        """Test unique constraints on incidente and processo_id."""
        # Save first processo
        processo_write(temp_db, sample_processo_data)

        # Try to save another with same incidente
        duplicate_data = sample_processo_data.copy()
        duplicate_data["numero_unico"] = "different-numero"
        duplicate_data["processo_id"] = 9999  # Different processo_id

        # This should succeed because the database uses INSERT OR REPLACE
        # which handles unique constraint violations by replacing
        result = processo_write(temp_db, duplicate_data)
        # The function should succeed because INSERT OR REPLACE handles duplicates
        assert result is True

    def test_check_constraints(self, temp_db):
        """Test CHECK constraints on classe and tipo_processo."""
        # Test invalid classe
        invalid_data = {
            "numero_unico": "test-constraint-1",
            "incidente": 1111111,
            "processo_id": 1111,
            "classe": "INVALID_CLASSE",  # Invalid classe
            "tipo_processo": "Eletrônico",
            "liminar": 0,
            "relator": "TEST",
            "origem": "TEST",
            "origem_orgao": "TEST",
            "data_protocolo": "2023-01-01T00:00:00Z",
            "autor1": "TEST",
            "assuntos": [],
            "partes_total": [],
            "andamentos": [],
            "decisoes": [],
            "deslocamentos": [],
            "peticoes": [],
            "recursos": [],
            "pautas": [],
        }

        result = processo_write(temp_db, invalid_data)
        assert result is False

    def test_liminar_constraint(self, temp_db):
        """Test CHECK constraint on liminar field."""
        # Test invalid liminar value
        invalid_data = {
            "numero_unico": "test-constraint-2",
            "incidente": 2222222,
            "processo_id": 2222,
            "classe": "ADI",
            "tipo_processo": "Eletrônico",
            "liminar": 2,  # Invalid liminar (should be 0 or 1)
            "relator": "TEST",
            "origem": "TEST",
            "origem_orgao": "TEST",
            "data_protocolo": "2023-01-01T00:00:00Z",
            "autor1": "TEST",
            "assuntos": [],
            "partes_total": [],
            "andamentos": [],
            "decisoes": [],
            "deslocamentos": [],
            "peticoes": [],
            "recursos": [],
            "pautas": [],
        }

        result = processo_write(temp_db, invalid_data)
        assert result is False


class TestDatabaseIntegration:
    """Test database integration scenarios."""

    def test_full_workflow(self, temp_db):
        """Test a complete workflow: save, read, update, error, retry."""
        # Initial data
        initial_data = {
            "numero_unico": "workflow-test-001",
            "incidente": 9999999,
            "processo_id": 9999,
            "classe": "ADI",
            "tipo_processo": "Eletrônico",
            "liminar": 0,
            "relator": "MIN. TEST",
            "origem": "TEST ORIGIN",
            "origem_orgao": "TEST ORG",
            "data_protocolo": "2023-01-01T00:00:00Z",
            "autor1": "TEST AUTHOR",
            "assuntos": ["Test subject"],
            "partes_total": [],
            "andamentos": [],
            "decisoes": [],
            "deslocamentos": [],
            "peticoes": [],
            "recursos": [],
            "pautas": [],
        }

        # 1. Save initial data
        result = processo_write(temp_db, initial_data)
        assert result is True

        # 2. Verify data exists
        data = processo_read(temp_db, initial_data["numero_unico"])
        # relator is the 7th column (index 6) in the processos table
        assert data[6] == "MIN. TEST"

        # 3. Check recent data
        has_recent = has_recent_data(
            temp_db, initial_data["processo_id"], initial_data["classe"], 24
        )
        assert has_recent is True

        # 4. Mark as error
        error_result = mark_error(
            temp_db, initial_data["numero_unico"], "Processing error"
        )
        assert error_result is True

        # 5. Verify error was marked
        errored_data = processo_read(temp_db, initial_data["numero_unico"])
        # error_message is the 14th column (index 13) in the processos table
        assert errored_data[13] == "Processing error"

        # 6. Check that it's now in failed list
        failed_ids = get_failed_processo_ids(temp_db, initial_data["classe"], 24)
        assert initial_data["processo_id"] in failed_ids

        # 7. Update with corrected data
        updated_data = initial_data.copy()
        updated_data["relator"] = "MIN. CORRECTED"
        updated_data["error_message"] = None  # Clear error

        update_result = processo_write(temp_db, updated_data)
        assert update_result is True

        # 8. Verify update
        final_data = processo_read(temp_db, initial_data["numero_unico"])
        # relator is the 7th column (index 6), error_message is the 14th column (index 13)
        assert final_data[6] == "MIN. CORRECTED"
        assert final_data[13] is None

    def test_multiple_processos_same_classe(self, temp_db):
        """Test handling multiple processos of the same classe."""
        processos = []
        for i in range(3):
            processo_data = {
                "numero_unico": f"multi-test-{i:03d}",
                "incidente": 1000000 + i,
                "processo_id": 1000 + i,
                "classe": "ADI",
                "tipo_processo": "Eletrônico",
                "liminar": 0,
                "relator": f"MIN. TEST {i}",
                "origem": f"TEST ORIGIN {i}",
                "origem_orgao": f"TEST ORG {i}",
                "data_protocolo": "2023-01-01T00:00:00Z",
                "autor1": f"TEST AUTHOR {i}",
                "assuntos": [f"Test subject {i}"],
                "partes_total": [],
                "andamentos": [],
                "decisoes": [],
                "deslocamentos": [],
                "peticoes": [],
                "recursos": [],
                "pautas": [],
            }
            processos.append(processo_data)

            # Save each processo
            result = processo_write(temp_db, processo_data)
            assert result is True

        # Check all exist
        existing_ids = get_existing_processo_ids(temp_db, "ADI", 24)
        assert len(existing_ids) == 3
        assert {1000, 1001, 1002} == existing_ids

        # Mark one as failed
        mark_error(temp_db, processos[1]["numero_unico"], "Test error")

        # Check failed list
        failed_ids = get_failed_processo_ids(temp_db, "ADI", 24)
        assert 1001 in failed_ids

        # Check existing list (should exclude failed)
        existing_ids_after_error = get_existing_processo_ids(temp_db, "ADI", 24)
        assert 1001 not in existing_ids_after_error
        assert len(existing_ids_after_error) == 2

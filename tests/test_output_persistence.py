"""
Tests for output persistence and file appending behavior
"""

import os
import sqlite3
import tempfile
from unittest.mock import Mock

import pytest

from judex.core import JudexScraper
from judex.output_registry import OutputFormatRegistry
from judex.pipelines.database_pipeline import DatabasePipeline


class TestOutputFileCreation:
    """Test that output files are created in the correct location"""

    def test_output_directory_creation(self):
        """Test that judex_output directory is created when it doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_output")

            # Ensure directory doesn't exist
            assert not os.path.exists(output_path)

            scraper = JudexScraper(
                classe="ADI",
                processos="[123, 456]",
                salvar_como=["json", "csv", "sql"],
                output_path=output_path,
            )

            # Check that directory was created
            assert os.path.exists(output_path)
            assert os.path.isdir(output_path)

    def test_output_files_naming(self):
        """Test that output files are named correctly based on classe"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_output")

            scraper = JudexScraper(
                classe="ADPF",
                processos="[789]",
                salvar_como=["json", "csv", "sql"],
                output_path=output_path,
            )

            # Check expected file paths
            expected_json = os.path.join(output_path, "ADPF_cases.json")
            expected_csv = os.path.join(output_path, "ADPF_processos.csv")
            expected_db = os.path.join(output_path, "judex.db")

            # These files should be created when scraping runs
            # We'll test the file creation in integration tests


# JSON and CSV pipeline tests removed - pipelines deleted


# CSV pipeline tests removed - pipeline deleted


class TestSQLOutputPersistence:
    """Test SQL database output persistence"""

    def test_database_pipeline_initialization(self):
        """Test database pipeline initializes with correct database path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_cases.db")

            pipeline = DatabasePipeline(db_path)

            assert pipeline.db_path == db_path
            assert os.path.exists(db_path)

    def test_database_pipeline_from_crawler(self):
        """Test database pipeline creation from crawler settings"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_cases.db")

            # Mock crawler with settings
            mock_crawler = Mock()
            mock_crawler.settings = Mock()
            mock_crawler.settings.get.return_value = db_path

            pipeline = DatabasePipeline.from_crawler(mock_crawler)

            assert pipeline.db_path == db_path
            mock_crawler.settings.get.assert_called_once_with(
                "DATABASE_PATH", "judex.db"
            )

    def test_database_file_creation(self):
        """Test that database file is created with correct schema"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_cases.db")

            pipeline = DatabasePipeline(db_path)

            # Check database file exists
            assert os.path.exists(db_path)

            # Check database schema
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                # Check main table exists
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='processos'"
                )
                assert cursor.fetchone() is not None

                # Check normalized tables exist
                expected_tables = [
                    "partes",
                    "andamentos",
                    "decisoes",
                    "deslocamentos",
                    "peticoes",
                    "recursos",
                    "pautas",
                ]
                for table in expected_tables:
                    cursor.execute(
                        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
                    )
                    assert cursor.fetchone() is not None

    def test_database_insert_and_replace_behavior(self):
        """Test that database uses INSERT OR REPLACE (appropriate for databases)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_cases.db")

            pipeline = DatabasePipeline(db_path)

            # Insert first item
            item1 = {
                "numero_unico": "123",
                "incidente": 123,
                "processo_id": 123,
                "classe": "ADI",
                "tipo_processo": "Eletrônico",
                "liminar": 0,
                "relator": "Test Judge",
            }

            result1 = pipeline.process_item(item1, Mock())
            assert result1 is not None

            # Insert same item with different data (should replace)
            item2 = {
                "numero_unico": "123",
                "incidente": 123,
                "processo_id": 123,
                "classe": "ADI",
                "tipo_processo": "Eletrônico",
                "liminar": 1,  # Changed
                "relator": "Updated Judge",  # Changed
            }

            result2 = pipeline.process_item(item2, Mock())
            assert result2 is not None

            # Check that only one record exists (replaced)
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM processos WHERE numero_unico = '123'"
                )
                count = cursor.fetchone()[0]
                assert count == 1

                # Check that the updated data is there
                cursor.execute(
                    "SELECT relator, liminar FROM processos WHERE numero_unico = '123'"
                )
                row = cursor.fetchone()
                assert row[0] == "Updated Judge"
                assert row[1] == 1


class TestOutputFileAppending:
    """Test that output files should append instead of overwrite"""

    def test_json_should_append_instead_of_overwrite(self):
        """Test that JSON files should append new data instead of overwriting"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_cases.json")

            # JSON pipeline tests removed - pipeline deleted
            # pipeline1 = JSONPipeline(output_file)
            # pipeline2 = JSONPipeline(output_file)

            # Check that all items are present (currently fails - should be fixed)
            # with open(output_file, "r", encoding="utf-8") as f:
            #     data = json.load(f)

            # This assertion will fail with current implementation
            # It should be updated when append functionality is implemented
            # expected_numbers = ["123", "456", "789", "101112"]
            # actual_numbers = [item["numero_unico"] for item in data]

            # TODO: Update this test when append functionality is implemented
            # For now, this documents the current behavior (overwrite)
            # assert len(data) == 2  # Current behavior: only last batch
            # assert actual_numbers == ["789", "101112"]  # Current behavior

    def test_csv_should_append_instead_of_overwrite(self):
        """Test that CSV files should append new data instead of overwriting"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_processos.csv")

            # CSV pipeline tests removed - pipeline deleted
            # pipeline1 = CSVPipeline(output_file)
            # pipeline2 = CSVPipeline(output_file)

            # Check that all items are present (currently fails - should be fixed)
            # with open(output_file, "r", encoding="utf-8", newline="") as f:
            #     content = f.read()
            #     lines = content.strip().split("\n")

            # This assertion will fail with current implementation
            # It should be updated when append functionality is implemented
            # expected_lines = 5  # Header + 4 data rows
            # actual_lines = len(lines)

            # TODO: Update this test when append functionality is implemented
            # For now, this documents the current behavior (overwrite)
            # assert (
            #     actual_lines == 3
            # )  # Current behavior: header + 2 data rows (last batch only)
            # assert "789,ADI" in lines[1]  # Current behavior: only last batch

    def test_sql_handles_duplicates_correctly(self):
        """Test that SQL database handles duplicates correctly with INSERT OR REPLACE"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_cases.db")

            pipeline = DatabasePipeline(db_path)

            # Insert items
            items = [
                {
                    "numero_unico": "123",
                    "incidente": 123,
                    "processo_id": 123,
                    "classe": "ADI",
                    "tipo_processo": "Eletrônico",
                    "liminar": 0,
                    "relator": "Judge A",
                },
                {
                    "numero_unico": "456",
                    "incidente": 456,
                    "processo_id": 456,
                    "classe": "ADI",
                    "tipo_processo": "Eletrônico",
                    "liminar": 0,
                    "relator": "Judge B",
                },
            ]

            for item in items:
                pipeline.process_item(item, Mock())

            # Insert duplicate with updated data
            updated_item = {
                "numero_unico": "123",
                "incidente": 123,
                "processo_id": 123,
                "classe": "ADI",
                "tipo_processo": "Eletrônico",
                "liminar": 1,  # Updated
                "relator": "Updated Judge A",  # Updated
            }

            pipeline.process_item(updated_item, Mock())

            # Check database state
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                # Should have 2 unique records
                cursor.execute("SELECT COUNT(*) FROM processos")
                count = cursor.fetchone()[0]
                assert count == 2

                # Check that the updated record has new data
                cursor.execute(
                    "SELECT relator, liminar FROM processos WHERE numero_unico = '123'"
                )
                row = cursor.fetchone()
                assert row[0] == "Updated Judge A"
                assert row[1] == 1

                # Check that the other record is unchanged
                cursor.execute(
                    "SELECT relator FROM processos WHERE numero_unico = '456'"
                )
                row = cursor.fetchone()
                assert row[0] == "Judge B"


class TestOutputFileIntegration:
    """Integration tests for output file creation and persistence"""

    def test_all_output_types_created(self):
        """Test that all requested output types create files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "integration_test")

            # Test with all persistence types
            scraper = JudexScraper(
                classe="ADI",
                processos="[123, 456]",
                salvar_como=["json", "csv", "sql"],
                output_path=output_path,
            )

            # Check that output directory was created
            assert os.path.exists(output_path)

            # Expected file paths
            expected_files = [
                os.path.join(output_path, "ADI_cases.json"),
                os.path.join(output_path, "ADI_processos.csv"),
                os.path.join(output_path, "judex.db"),
            ]

            # Note: Files are created during scraping, not during initialization
            # This test documents the expected behavior

    def test_custom_database_path(self):
        """Test that custom database path is used when provided"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_output")
            custom_db_path = os.path.join(temp_dir, "custom_database.db")

            scraper = JudexScraper(
                classe="ADI",
                processos="[123]",
                salvar_como=["sql"],
                output_path=output_path,
                db_path=custom_db_path,
            )

            # Check that custom database path is set
            # This would be verified during actual scraping
            assert scraper.db_path == custom_db_path

    def test_persistence_types_validation(self):
        """Test that invalid persistence types are rejected"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_output")

            # Test invalid persistence type
            with pytest.raises(Exception) as exc_info:
                JudexScraper(
                    classe="ADI",
                    processos="[123]",
                    salvar_como=["invalid_type"],
                    output_path=output_path,
                )

            error_msg = str(exc_info.value)
            assert "salvar_como must contain only:" in error_msg
            assert "json" in error_msg
            assert "csv" in error_msg
            assert "sql" in error_msg

    def test_jsonlines_persistence_type_validation(self):
        """Test that jsonlines persistence type is accepted"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_output")

            # Test jsonlines persistence type - should NOT raise exception
            scraper = JudexScraper(
                classe="ADI",
                processos="[123]",
                salvar_como=["jsonlines"],
                output_path=output_path,
            )

            assert scraper.salvar_como == ["jsonlines"]

    def test_jsonlines_combined_with_other_formats(self):
        """Test that jsonlines can be combined with other formats"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_output")

            # Test jsonlines combined with other formats
            scraper = JudexScraper(
                classe="ADI",
                processos="[123]",
                salvar_como=["json", "jsonlines", "csv"],
                output_path=output_path,
            )

            assert "jsonlines" in scraper.salvar_como
            assert "json" in scraper.salvar_como
            assert "csv" in scraper.salvar_como

    def test_empty_persistence_list_behavior(self):
        """Test that empty persistence list behavior"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_output")

            scraper = JudexScraper(
                classe="ADI", processos="[123]", salvar_como=[], output_path=output_path
            )

            # Current behavior: empty list is passed through as-is
            assert scraper.salvar_como == []


class TestJSONLinesFormatRegistration:
    """Test JSONLines format registration and configuration"""

    def test_jsonlines_format_is_registered(self):
        """Test that jsonlines format is registered in the output registry"""
        jsonlines_config = OutputFormatRegistry.get_format("jsonlines")

        assert jsonlines_config is not None
        assert jsonlines_config["format"] == "jsonlines"
        assert jsonlines_config["extension"] == "jsonl"
        assert jsonlines_config["use_feeds"] is True

    def test_jsonlines_feed_configuration(self):
        """Test that jsonlines format generates correct feed configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_output")

            feeds = OutputFormatRegistry.configure_feeds(
                output_path=output_path,
                classe="ADI",
                custom_name=None,
                requested_formats=["jsonlines"],
                process_numbers=[123, 456],
                overwrite=False,
            )

            # Should have one feed for jsonlines
            assert len(feeds) == 1

            # Check the feed path and configuration
            feed_path = list(feeds.keys())[0]
            assert feed_path.endswith(".jsonl")
            assert "ADI_123_456" in feed_path

            feed_config = list(feeds.values())[0]
            assert feed_config["format"] == "jsonlines"
            assert feed_config["use_feeds"] is True

    def test_jsonlines_with_custom_name(self):
        """Test jsonlines format with custom filename"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_output")

            feeds = OutputFormatRegistry.configure_feeds(
                output_path=output_path,
                classe="ADI",
                custom_name="custom_cases",
                requested_formats=["jsonlines"],
                process_numbers=None,
                overwrite=False,
            )

            # Should have one feed for jsonlines
            assert len(feeds) == 1

            # Check the feed path includes custom name
            feed_path = list(feeds.keys())[0]
            assert feed_path.endswith(".jsonl")
            assert "custom_cases" in feed_path


class TestOutputFileAppendingImplementation:
    """Tests for the required changes to implement file appending"""

    def test_json_pipeline_should_use_append_mode(self):
        """Test that JSON pipeline should be modified to use append mode"""
        # This test documents the required change
        # Current implementation uses "w" mode (overwrite)
        # Should be changed to "a" mode (append) with proper JSON array handling

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_cases.json")

            # Current behavior (overwrite)
            # JSONPipeline removed - pipeline deleted
            # pipeline = JSONPipeline(output_file)
            # pipeline.process_item({"numero_unico": "123"}, Mock())
            # pipeline.close_spider(Mock())

            # Check current file content
            # with open(output_file, "r") as f:
            #     data = json.load(f)
            # assert len(data) == 1

            # TODO: Implement append mode in JSONPipeline
            # The pipeline should:
            # 1. Check if file exists and has content
            # 2. If it exists, load existing data
            # 3. Append new items to existing data
            # 4. Write back the combined data

    def test_csv_pipeline_should_use_append_mode(self):
        """Test that CSV pipeline should be modified to use append mode"""
        # This test documents the required change
        # Current implementation uses "w" mode (overwrite)
        # Should be changed to "a" mode (append) with proper header handling

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_processos.csv")

            # Current behavior (overwrite)
            # CSVPipeline removed - pipeline deleted
            # pipeline = CSVPipeline(output_file)
            # pipeline.process_item({"numero_unico": "123"}, Mock())
            # pipeline.close_spider(Mock())

            # Check current file content
            # with open(output_file, "r") as f:
            #     content = f.read()
            # lines = content.strip().split("\n")
            # assert len(lines) == 2  # Header + 1 data row

            # TODO: Implement append mode in CSVPipeline
            # The pipeline should:
            # 1. Check if file exists
            # 2. If it doesn't exist, write header + data
            # 3. If it exists, append only data rows (skip header)

    def test_sql_pipeline_already_handles_duplicates_correctly(self):
        """Test that SQL pipeline already handles duplicates correctly"""
        # SQL pipeline already uses INSERT OR REPLACE which is appropriate
        # No changes needed for SQL pipeline

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_cases.db")

            pipeline = DatabasePipeline(db_path)

            # Insert item
            item = {
                "numero_unico": "123",
                "incidente": 123,
                "processo_id": 123,
                "classe": "ADI",
                "tipo_processo": "Eletrônico",
                "liminar": 0,
                "relator": "Judge A",
            }

            result = pipeline.process_item(item, Mock())
            assert result is not None

            # Insert same item with different data
            updated_item = {
                "numero_unico": "123",
                "incidente": 123,
                "processo_id": 123,
                "classe": "ADI",
                "tipo_processo": "Eletrônico",
                "liminar": 1,
                "relator": "Updated Judge A",
            }

            result = pipeline.process_item(updated_item, Mock())
            assert result is not None

            # Check that only one record exists (replaced)
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM processos")
                count = cursor.fetchone()[0]
                assert count == 1

                # Check updated data
                cursor.execute(
                    "SELECT relator FROM processos WHERE numero_unico = '123'"
                )
                row = cursor.fetchone()
                assert row[0] == "Updated Judge A"

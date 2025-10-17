"""
Test cases for judex.persistence module that will expose critical issues
"""

import json
import os
import sqlite3
import tempfile
from unittest.mock import MagicMock, mock_open, patch

import pytest
import scrapy

from judex.persistence import (
    PersistencePipeline,
    export_to_csv,
    export_to_json,
    export_to_sqlite,
    persist_data,
)


class TestPersistenceModule:
    """Test cases that will expose issues in the persistence module"""

    def setup_method(self):
        """Set up test fixtures"""
        self.sample_data = [
            {"id": 1, "name": "Test Case 1", "status": "active"},
            {"id": 2, "name": "Test Case 2", "status": "inactive"},
            {"id": 3, "name": "Test Case 3", "status": "pending"},
        ]

    def test_persist_data_invalid_type(self):
        """Test persist_data with invalid persistence type - should fail"""
        with pytest.raises(ValueError, match="Invalid persistence type"):
            persist_data(self.sample_data, "invalid_type", "/tmp")

    def test_persist_data_none_type(self):
        """Test persist_data with None type - should fail"""
        with pytest.raises(ValueError, match="Invalid persistence type"):
            persist_data(self.sample_data, None, "/tmp")

    def test_export_to_csv_empty_data(self):
        """Test CSV export with empty data - will crash"""
        with pytest.raises(IndexError):  # data[0].keys() will fail
            export_to_csv([], "test.csv")

    def test_export_to_csv_single_item(self):
        """Test CSV export with single item - should work"""
        single_item = [{"id": 1, "name": "test"}]
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_file = f.name

        try:
            result = export_to_csv(single_item, temp_file)
            assert result is True

            # Verify file was created and has correct content
            with open(temp_file, "r", encoding="utf-8") as f:
                content = f.read()
                assert "id,name" in content
                assert "1,test" in content
        finally:
            os.unlink(temp_file)

    def test_export_to_csv_inconsistent_keys(self):
        """Test CSV export with inconsistent dictionary keys - will produce malformed CSV"""
        inconsistent_data = [
            {"id": 1, "name": "test1"},
            {"id": 2, "status": "active"},  # Different keys!
            {"id": 3, "name": "test3", "extra": "field"},
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_file = f.name

        try:
            result = export_to_csv(inconsistent_data, temp_file)
            assert result is True  # Function returns True but CSV is malformed

            # Verify the CSV is malformed
            with open(temp_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Header will be from first item only
                assert "id,name" in lines[0]
                # But subsequent rows have different structures
                assert len(lines) == 4  # Header + 3 data rows
        finally:
            os.unlink(temp_file)

    def test_export_to_csv_file_permission_error(self):
        """Test CSV export with permission error - should handle gracefully"""
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            result = export_to_csv(self.sample_data, "/root/test.csv")
            assert result is False

    def test_export_to_json_empty_data(self):
        """Test JSON export with empty data - should work"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_file = f.name

        try:
            result = export_to_json([], temp_file)
            assert result is True

            # Verify file contains empty array
            with open(temp_file, "r", encoding="utf-8") as f:
                content = json.load(f)
                assert content == []
        finally:
            os.unlink(temp_file)

    def test_export_to_json_complex_data(self):
        """Test JSON export with complex nested data"""
        complex_data = [
            {
                "id": 1,
                "nested": {"key": "value", "list": [1, 2, 3]},
                "unicode": "café",
                "special_chars": "test\nwith\ttabs",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_file = f.name

        try:
            result = export_to_json(complex_data, temp_file)
            assert result is True

            # Verify file content
            with open(temp_file, "r", encoding="utf-8") as f:
                content = json.load(f)
                assert content == complex_data
        finally:
            os.unlink(temp_file)

    def test_export_to_sqlite_missing_table(self):
        """Test SQLite export without creating table first - will fail"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            temp_file = f.name

        try:
            result = export_to_sqlite(self.sample_data, temp_file)
            assert result is False  # Should fail because table doesn't exist
        finally:
            os.unlink(temp_file)

    def test_export_to_sqlite_with_table_creation(self):
        """Test SQLite export with proper table creation"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            temp_file = f.name

        try:
            # First create the table
            with sqlite3.connect(temp_file) as conn:
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE data (id INTEGER, name TEXT, status TEXT)")
                conn.commit()

            # Now test the export
            result = export_to_sqlite(self.sample_data, temp_file)
            assert result is True

            # Verify data was inserted
            with sqlite3.connect(temp_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM data")
                count = cursor.fetchone()[0]
                assert count == 3
        finally:
            os.unlink(temp_file)

    def test_export_to_sqlite_inconsistent_schema(self):
        """Test SQLite export with data that doesn't match table schema"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            temp_file = f.name

        try:
            # Create table with different schema
            with sqlite3.connect(temp_file) as conn:
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE data (id INTEGER, name TEXT)")
                conn.commit()

            # Try to export data with extra fields
            extra_field_data = [{"id": 1, "name": "test", "status": "active", "extra": "field"}]

            result = export_to_sqlite(extra_field_data, temp_file)
            # This might fail or succeed depending on SQLite behavior
            # The current implementation doesn't handle schema mismatches
        finally:
            os.unlink(temp_file)

    def test_persist_data_directory_creation(self):
        """Test persist_data when output directory doesn't exist"""
        non_existent_dir = "/tmp/non_existent_dir_12345"

        # This should fail because the directory doesn't exist
        with pytest.raises(FileNotFoundError):
            persist_data(self.sample_data, "json", non_existent_dir)

    def test_export_functions_return_values(self):
        """Test that export functions properly return success/failure status"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test successful export
            csv_file = os.path.join(temp_dir, "test.csv")
            result = export_to_csv(self.sample_data, csv_file)
            assert result is True

            # Test with invalid path (should fail)
            result = export_to_csv(self.sample_data, "/invalid/path/test.csv")
            assert result is False

    def test_unicode_handling_in_csv(self):
        """Test CSV export with unicode characters"""
        unicode_data = [
            {"id": 1, "name": "José", "city": "São Paulo"},
            {"id": 2, "name": "François", "city": "Montréal"},
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_file = f.name

        try:
            result = export_to_csv(unicode_data, temp_file)
            assert result is True

            # Verify unicode is preserved
            with open(temp_file, "r", encoding="utf-8") as f:
                content = f.read()
                assert "José" in content
                assert "São Paulo" in content
                assert "François" in content
        finally:
            os.unlink(temp_file)

    def test_large_dataset_handling(self):
        """Test export with large dataset"""
        large_data = [{"id": i, "name": f"item_{i}"} for i in range(10000)]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_file = f.name

        try:
            result = export_to_json(large_data, temp_file)
            assert result is True

            # Verify file size is reasonable
            file_size = os.path.getsize(temp_file)
            assert file_size > 0
        finally:
            os.unlink(temp_file)

    def test_concurrent_access_simulation(self):
        """Test behavior when file is locked by another process"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_file = f.name

        try:
            # Open file in exclusive mode to simulate lock
            with open(temp_file, "r+") as locked_file:
                result = export_to_json(self.sample_data, temp_file)
                # This might fail or succeed depending on OS behavior
                # The current implementation doesn't handle file locks gracefully
        finally:
            os.unlink(temp_file)

    def test_memory_efficiency_with_generator(self):
        """Test that functions don't load entire dataset into memory unnecessarily"""

        def data_generator():
            for i in range(1000):
                yield {"id": i, "name": f"item_{i}"}

        # This will fail because the functions expect a list, not a generator
        with pytest.raises(AttributeError):
            export_to_json(data_generator(), "test.json")

    def test_csv_with_special_characters(self):
        """Test CSV export with special characters that need escaping"""
        special_data = [
            {"id": 1, "name": "Test, with comma", "description": 'Has "quotes" and newlines\nhere'},
            {"id": 2, "name": "Another, test", "description": "Normal text"},
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_file = f.name

        try:
            result = export_to_csv(special_data, temp_file)
            assert result is True

            # Verify file was created (content validation would be complex)
            assert os.path.exists(temp_file)
            assert os.path.getsize(temp_file) > 0
        finally:
            os.unlink(temp_file)

    def test_json_with_non_serializable_data(self):
        """Test JSON export with non-serializable data types"""
        non_serializable_data = [
            {"id": 1, "name": "test", "function": lambda x: x},  # Function not serializable
            {"id": 2, "name": "test2", "set": {1, 2, 3}},  # Set not JSON serializable
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_file = f.name

        try:
            # This should fail due to non-serializable data
            result = export_to_json(non_serializable_data, temp_file)
            assert result is False
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_sqlite_with_mixed_data_types(self):
        """Test SQLite export with mixed data types"""
        mixed_data = [
            {"id": 1, "name": "test", "value": 123.45, "active": True},
            {"id": 2, "name": "test2", "value": None, "active": False},
        ]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            temp_file = f.name

        try:
            # Create table with appropriate schema
            with sqlite3.connect(temp_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "CREATE TABLE data (id INTEGER, name TEXT, value REAL, active INTEGER)"
                )
                conn.commit()

            result = export_to_sqlite(mixed_data, temp_file)
            # This might fail due to the current implementation's limitations
        finally:
            os.unlink(temp_file)

    def test_persist_data_with_relative_paths(self):
        """Test persist_data with relative paths"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            # Create a subdirectory
            os.makedirs("output", exist_ok=True)

            # Test with relative path
            result = persist_data(self.sample_data, "json", "output")
            # This should work but might have issues with path handling
            assert os.path.exists("output/judex_output.json")

    def test_export_with_none_values(self):
        """Test export functions with None values in data"""
        none_data = [
            {"id": 1, "name": "test", "value": None},
            {"id": 2, "name": None, "value": 123},
            {"id": None, "name": "test3", "value": 456},
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_file = f.name

        try:
            result = export_to_json(none_data, temp_file)
            assert result is True

            # Verify None values are preserved
            with open(temp_file, "r", encoding="utf-8") as f:
                content = json.load(f)
            assert content[0]["value"] is None
            assert content[1]["name"] is None
            assert content[2]["id"] is None
        finally:
            os.unlink(temp_file)


class TestPersistencePipeline:
    """Test cases for the new Scrapy-compatible PersistencePipeline"""

    def setup_method(self):
        """Set up test fixtures"""
        self.sample_data = [
            {"id": 1, "name": "Test Case 1", "status": "active"},
            {"id": 2, "name": "Test Case 2", "status": "inactive"},
            {"id": 3, "name": "Test Case 3", "status": "pending"},
        ]

    def test_pipeline_initialization(self):
        """Test pipeline initialization"""
        pipeline = PersistencePipeline(output_dir="test_output", formats=["json"])
        assert pipeline.output_dir == "test_output"
        assert pipeline.formats == ["json"]
        assert pipeline.items_buffer == []

    def test_pipeline_from_crawler(self):
        """Test pipeline creation from crawler settings"""
        # Mock crawler with settings
        crawler = MagicMock()
        crawler.settings = {
            "PERSISTENCE_OUTPUT_DIR": "custom_output",
            "PERSISTENCE_FORMATS": ["json", "csv"],
        }
        crawler.settings.get = lambda key, default=None: crawler.settings.get(key, default)
        crawler.settings.getlist = lambda key, default=None: crawler.settings.get(key, default)

        pipeline = PersistencePipeline.from_crawler(crawler)
        assert pipeline.output_dir == "custom_output"
        assert pipeline.formats == ["json", "csv"]

    def test_pipeline_process_item(self):
        """Test pipeline processing of items"""
        pipeline = PersistencePipeline(output_dir="test_output", formats=["json"])

        # Mock spider
        spider = MagicMock()
        spider.name = "test_spider"
        spider.crawler.stats.get_value.return_value = "2024-01-01"

        # Mock item
        item = {"id": 1, "name": "test"}

        # Process item
        result = pipeline.process_item(item, spider)

        # Check that item was buffered
        assert len(pipeline.items_buffer) == 1
        assert pipeline.items_buffer[0]["id"] == 1
        assert pipeline.items_buffer[0]["name"] == "test"
        assert pipeline.items_buffer[0]["_spider_name"] == "test_spider"
        assert result == item  # Pass-through

    def test_pipeline_export_json(self):
        """Test JSON export functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = PersistencePipeline(output_dir=temp_dir, formats=["json"])
            pipeline.items_buffer = self.sample_data

            # Mock spider
            spider = MagicMock()
            spider.name = "test_spider"

            # Test export
            pipeline.close_spider(spider)

            # Check file was created
            output_file = os.path.join(temp_dir, "test_spider_output.json")
            assert os.path.exists(output_file)

            # Check content
            with open(output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert len(data) == 3
                assert data[0]["id"] == 1

    def test_pipeline_export_csv(self):
        """Test CSV export functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = PersistencePipeline(output_dir=temp_dir, formats=["csv"])
            pipeline.items_buffer = self.sample_data

            # Mock spider
            spider = MagicMock()
            spider.name = "test_spider"

            # Test export
            pipeline.close_spider(spider)

            # Check file was created
            output_file = os.path.join(temp_dir, "test_spider_output.csv")
            assert os.path.exists(output_file)

            # Check content
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()
                assert "id,name,status" in content
                assert "1,Test Case 1,active" in content

    def test_pipeline_export_sqlite(self):
        """Test SQLite export functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = PersistencePipeline(output_dir=temp_dir, formats=["sqlite"])
            pipeline.items_buffer = self.sample_data

            # Mock spider
            spider = MagicMock()
            spider.name = "test_spider"

            # Test export
            pipeline.close_spider(spider)

            # Check file was created
            output_file = os.path.join(temp_dir, "test_spider_output.db")
            assert os.path.exists(output_file)

            # Check database content
            with sqlite3.connect(output_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM test_spider_data")
                count = cursor.fetchone()[0]
                assert count == 3

    def test_pipeline_empty_data(self):
        """Test pipeline with empty data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = PersistencePipeline(output_dir=temp_dir, formats=["json"])
            pipeline.items_buffer = []  # Empty data

            # Mock spider
            spider = MagicMock()
            spider.name = "test_spider"

            # Test export (should not crash)
            pipeline.close_spider(spider)

            # Check no files were created
            files = os.listdir(temp_dir)
            assert len(files) == 0

    def test_pipeline_multiple_formats(self):
        """Test pipeline with multiple export formats"""
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = PersistencePipeline(output_dir=temp_dir, formats=["json", "csv", "sqlite"])
            pipeline.items_buffer = self.sample_data

            # Mock spider
            spider = MagicMock()
            spider.name = "test_spider"

            # Test export
            pipeline.close_spider(spider)

            # Check all files were created
            files = os.listdir(temp_dir)
            assert "test_spider_output.json" in files
            assert "test_spider_output.csv" in files
            assert "test_spider_output.db" in files

    def test_pipeline_directory_creation(self):
        """Test that pipeline creates output directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, "new_output_dir")

            # Directory shouldn't exist yet
            assert not os.path.exists(output_dir)

            pipeline = PersistencePipeline(output_dir=output_dir, formats=["json"])

            # Directory should be created
            assert os.path.exists(output_dir)

    def test_pipeline_error_handling(self):
        """Test pipeline error handling"""
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = PersistencePipeline(output_dir=temp_dir, formats=["invalid_format"])
            pipeline.items_buffer = self.sample_data

            # Mock spider
            spider = MagicMock()
            spider.name = "test_spider"

            # Test export (should handle invalid format gracefully)
            pipeline.close_spider(spider)

            # Should not crash, just log warning

    def test_pipeline_unicode_handling(self):
        """Test pipeline with unicode data"""
        unicode_data = [
            {"id": 1, "name": "José", "city": "São Paulo"},
            {"id": 2, "name": "François", "city": "Montréal"},
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = PersistencePipeline(output_dir=temp_dir, formats=["json"])
            pipeline.items_buffer = unicode_data

            # Mock spider
            spider = MagicMock()
            spider.name = "test_spider"

            # Test export
            pipeline.close_spider(spider)

            # Check file was created and unicode is preserved
            output_file = os.path.join(temp_dir, "test_spider_output.json")
            with open(output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert data[0]["name"] == "José"
                assert data[0]["city"] == "São Paulo"

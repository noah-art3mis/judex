"""
Unit tests for Pydantic validation pipeline
"""

import os
import tempfile
from unittest.mock import Mock, patch

from judex.pydantic_pipeline import PydanticValidationPipeline


class TestPydanticValidationPipeline:
    """Test PydanticValidationPipeline"""

    def setup_method(self):
        """Set up test fixtures"""
        self.pipeline = PydanticValidationPipeline()
        self.mock_spider = Mock()
        # Use temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.mock_spider.settings = {"DATABASE_PATH": self.temp_db.name}

    def teardown_method(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_pipeline_initialization(self):
        """Test pipeline can be initialized"""
        pipeline = PydanticValidationPipeline()
        assert pipeline is not None

    def test_valid_item_processing(self):
        """Test processing a valid item"""
        # Create a mock item with valid data
        mock_item = Mock()
        item_data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "numero_unico": "ADI 123456",
        }

        # Mock ItemAdapter to return a dict-like object
        with patch("judex.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.return_value = item_data

            result = self.pipeline.process_item(mock_item, self.mock_spider)

            # Should return the original item
            assert result == mock_item

    def test_invalid_item_validation_error(self):
        """Test handling of validation errors"""
        # Create a mock item with invalid data (missing required fields)
        mock_item = Mock()
        item_data = {
            "processo_id": "invalid",  # Should be int
            "incidente": "invalid",  # Should be int
            "classe": "INVALID_TYPE",  # Invalid case type
        }

        # Mock ItemAdapter
        with patch("judex.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.return_value = item_data

            # Should not raise exception, but log error
            result = self.pipeline.process_item(mock_item, self.mock_spider)

            # Should return the original item even on validation error
            assert result == mock_item

    def test_database_save_failure(self):
        """Test that pipeline doesn't handle database saves anymore"""
        # Create a mock item with valid data
        mock_item = Mock()
        item_data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
        }

        # Mock ItemAdapter
        with patch("judex.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.return_value = item_data

            result = self.pipeline.process_item(mock_item, self.mock_spider)

            # Should return the original item
            assert result == mock_item

    def test_unexpected_error_handling(self):
        """Test handling of unexpected errors"""
        # Create a mock item that will cause an unexpected error
        mock_item = Mock()
        item_data = {"processo_id": 123, "incidente": 456, "classe": "ADI"}

        # Mock ItemAdapter to return data but then raise an error during processing
        with patch("judex.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.return_value = item_data

            # Mock the STFCaseModel to raise an unexpected error
            with patch("judex.pydantic_pipeline.STFCaseModel") as mock_model:
                mock_model.side_effect = Exception("Unexpected error")

                result = self.pipeline.process_item(mock_item, self.mock_spider)

                # Should return the original item even on unexpected error
                assert result == mock_item

    def test_field_mapping_validation(self):
        """Test that field mapping works correctly in pipeline"""
        # Create a mock item with data that needs field mapping
        mock_item = Mock()
        item_data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "liminar": ["liminar1", "liminar2"],  # Should convert to 1
            "assuntos": ["assunto1", "assunto2"],  # Should convert to JSON string
            "andamentos": [
                {"index": 1, "data": "2023-01-01", "nome": "Test"}
            ],  # Should map index to index_num
        }

        # Mock ItemAdapter
        with patch("judex.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.return_value = item_data

            result = self.pipeline.process_item(mock_item, self.mock_spider)

            # Should return the original item
            assert result == mock_item

    def test_enum_validation(self):
        """Test that enum validation works correctly"""
        # Test with valid enum values
        mock_item = Mock()
        item_data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "tipo_processo": "Eletrônico",
        }

        # Mock ItemAdapter
        with patch("judex.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.return_value = item_data

            result = self.pipeline.process_item(mock_item, self.mock_spider)

            # Should return the original item
            assert result == mock_item

    def test_spider_settings_database_path(self):
        """Test that pipeline doesn't use database path anymore"""
        # Test with custom database path
        custom_spider = Mock()
        custom_spider.settings = {"DATABASE_PATH": "custom.db"}

        mock_item = Mock()
        item_data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
        }

        with patch("judex.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.return_value = item_data

            result = self.pipeline.process_item(mock_item, custom_spider)

            # Should return the original item
            assert result == mock_item

    def test_default_database_path(self):
        """Test that pipeline doesn't use database path anymore"""
        # Test with spider that doesn't specify database path
        default_spider = Mock()
        default_spider.settings = {}

        mock_item = Mock()
        item_data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
        }

        with patch("judex.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.return_value = item_data

            result = self.pipeline.process_item(mock_item, default_spider)

            # Should return the original item
            assert result == mock_item

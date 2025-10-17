"""
Unit tests for Pydantic validation pipeline
"""

from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from lexicon.models import STFCaseModel
from lexicon.pydantic_pipeline import PydanticValidationPipeline


class TestPydanticValidationPipeline:
    """Test PydanticValidationPipeline"""

    def setup_method(self):
        """Set up test fixtures"""
        self.pipeline = PydanticValidationPipeline()
        self.mock_spider = Mock()
        self.mock_spider.settings = {"DATABASE_PATH": "test.db"}

    def test_pipeline_initialization(self):
        """Test pipeline can be initialized"""
        pipeline = PydanticValidationPipeline()
        assert pipeline is not None

    @patch("lexicon.pydantic_pipeline.save_processo_data")
    def test_valid_item_processing(self, mock_save):
        """Test processing a valid item"""
        mock_save.return_value = True

        # Create a mock item with valid data
        mock_item = Mock()
        item_data = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "numero_unico": "ADI 123456",
        }

        # Mock ItemAdapter to return a dict-like object
        with patch("lexicon.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.return_value = item_data

            result = self.pipeline.process_item(mock_item, self.mock_spider)

            # Should return the original item
            assert result == mock_item

            # Should call save_processo_data
            mock_save.assert_called_once()

    @patch("lexicon.pydantic_pipeline.save_processo_data")
    def test_invalid_item_validation_error(self, mock_save):
        """Test handling of validation errors"""
        # Create a mock item with invalid data (missing required fields)
        mock_item = Mock()
        mock_item.__dict__ = {
            "processo_id": "invalid",  # Should be int
            "incidente": "invalid",  # Should be int
            "classe": "INVALID_TYPE",  # Invalid case type
        }

        # Mock ItemAdapter
        with patch("lexicon.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.return_value.__dict__ = mock_item.__dict__

            # Should not raise exception, but log error
            result = self.pipeline.process_item(mock_item, self.mock_spider)

            # Should return the original item even on validation error
            assert result == mock_item

            # Should not call save_processo_data on validation error
            mock_save.assert_not_called()

    @patch("lexicon.pydantic_pipeline.save_processo_data")
    def test_database_save_failure(self, mock_save):
        """Test handling of database save failures"""
        mock_save.return_value = False  # Simulate save failure

        # Create a mock item with valid data
        mock_item = Mock()
        mock_item.__dict__ = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
        }

        # Mock ItemAdapter
        with patch("lexicon.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.return_value.__dict__ = mock_item.__dict__

            result = self.pipeline.process_item(mock_item, self.mock_spider)

            # Should return the original item
            assert result == mock_item

            # Should call save_processo_data
            mock_save.assert_called_once()

    def test_unexpected_error_handling(self):
        """Test handling of unexpected errors"""
        # Create a mock item that will cause an unexpected error
        mock_item = Mock()
        mock_item.__dict__ = {}

        # Mock ItemAdapter to raise an unexpected error
        with patch("lexicon.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.side_effect = Exception("Unexpected error")

            result = self.pipeline.process_item(mock_item, self.mock_spider)

            # Should return the original item even on unexpected error
            assert result == mock_item

    @patch("lexicon.pydantic_pipeline.save_processo_data")
    def test_field_mapping_validation(self, mock_save):
        """Test that field mapping works correctly in pipeline"""
        mock_save.return_value = True

        # Create a mock item with data that needs field mapping
        mock_item = Mock()
        mock_item.__dict__ = {
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
        with patch("lexicon.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.return_value.__dict__ = mock_item.__dict__

            result = self.pipeline.process_item(mock_item, self.mock_spider)

            # Should return the original item
            assert result == mock_item

            # Should call save_processo_data with validated data
            mock_save.assert_called_once()

            # Check that the validated data has correct types
            call_args = mock_save.call_args[0]
            validated_data = call_args[1]  # Second argument is the data dict

            assert validated_data["liminar"] == 1
            assert isinstance(validated_data["assuntos"], str)
            assert validated_data["andamentos"][0]["index_num"] == 1

    @patch("lexicon.pydantic_pipeline.save_processo_data")
    def test_enum_validation(self, mock_save):
        """Test that enum validation works correctly"""
        mock_save.return_value = True

        # Test with valid enum values
        mock_item = Mock()
        mock_item.__dict__ = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
            "tipo_processo": "Eletrônico",
        }

        # Mock ItemAdapter
        with patch("lexicon.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.return_value.__dict__ = mock_item.__dict__

            result = self.pipeline.process_item(mock_item, self.mock_spider)

            # Should return the original item
            assert result == mock_item

            # Should call save_processo_data
            mock_save.assert_called_once()

    def test_spider_settings_database_path(self):
        """Test that pipeline uses correct database path from spider settings"""
        # Test with custom database path
        custom_spider = Mock()
        custom_spider.settings = {"DATABASE_PATH": "custom.db"}

        mock_item = Mock()
        mock_item.__dict__ = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
        }

        with patch("lexicon.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.return_value.__dict__ = mock_item.__dict__

            with patch("lexicon.pydantic_pipeline.save_processo_data") as mock_save:
                mock_save.return_value = True

                self.pipeline.process_item(mock_item, custom_spider)

                # Should use custom database path
                mock_save.assert_called_once_with("custom.db", mock_adapter.return_value.__dict__)

    def test_default_database_path(self):
        """Test that pipeline uses default database path when not specified"""
        # Test with spider that doesn't specify database path
        default_spider = Mock()
        default_spider.settings = {}

        mock_item = Mock()
        mock_item.__dict__ = {
            "processo_id": 123,
            "incidente": 456,
            "classe": "ADI",
        }

        with patch("lexicon.pydantic_pipeline.ItemAdapter") as mock_adapter:
            mock_adapter.return_value.__dict__ = mock_item.__dict__

            with patch("lexicon.pydantic_pipeline.save_processo_data") as mock_save:
                mock_save.return_value = True

                self.pipeline.process_item(mock_item, default_spider)

                # Should use default database path
                mock_save.assert_called_once_with("lexicon.db", mock_adapter.return_value.__dict__)

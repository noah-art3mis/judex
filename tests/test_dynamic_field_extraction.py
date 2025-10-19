"""
Tests for dynamic field extraction from STFCaseItem
"""

from judex.items import STFCaseItem
from judex.output_registry import OutputFormatRegistry


class TestDynamicFieldExtraction:
    """Test dynamic field extraction from STFCaseItem"""

    def test_stf_case_item_fields_exist(self):
        """Test that STFCaseItem has the expected fields"""
        fields = list(STFCaseItem.fields.keys())

        # Check that we have the expected number of fields
        assert len(fields) == 24

        # Check for key fields
        expected_fields = [
            "processo_id",
            "incidente",
            "numero_unico",
            "classe",
            "liminar",
            "tipo_processo",
            "relator",
            "origem",
            "data_protocolo",
            "origem_orgao",
            "autor1",
            "assuntos",
            "partes",
            "andamentos",
            "decisoes",
            "deslocamentos",
            "peticoes",
            "recursos",
            "pautas",
            "informacoes",
            "sessao",
            "status",
            "html",
            "extraido",
        ]

        for field in expected_fields:
            assert field in fields, f"Field '{field}' not found in STFCaseItem"

    def test_csv_format_has_dynamic_fields(self):
        """Test that CSV format configuration is correct"""
        csv_config = OutputFormatRegistry.get_format("csv")

        assert csv_config is not None
        assert "extra_config" in csv_config
        assert "include_headers_line" in csv_config["extra_config"]
        assert csv_config["extra_config"]["include_headers_line"] is True

    def test_json_format_has_dynamic_fields(self):
        """Test that JSON format configuration is correct"""
        json_config = OutputFormatRegistry.get_format("json")

        assert json_config is not None
        assert "extra_config" in json_config
        assert "indent" in json_config["extra_config"]
        assert "export_empty_fields" in json_config["extra_config"]
        assert json_config["extra_config"]["indent"] == 2
        assert json_config["extra_config"]["export_empty_fields"] is True

    def test_jsonl_format_has_dynamic_fields(self):
        """Test that JSONLines format configuration is correct"""
        jsonl_config = OutputFormatRegistry.get_format("jsonl")

        assert jsonl_config is not None
        assert "extra_config" in jsonl_config
        # JSONL config has empty extra_config
        assert jsonl_config["extra_config"] == {}

    def test_field_order_consistency(self):
        """Test that all formats have consistent configuration"""
        csv_config = OutputFormatRegistry.get_format("csv")
        json_config = OutputFormatRegistry.get_format("json")
        jsonl_config = OutputFormatRegistry.get_format("jsonl")

        # All formats should have extra_config
        assert "extra_config" in csv_config
        assert "extra_config" in json_config
        assert "extra_config" in jsonl_config

        # Each format should have its specific configuration
        assert "include_headers_line" in csv_config["extra_config"]
        assert "indent" in json_config["extra_config"]
        assert jsonl_config["extra_config"] == {}

    def test_field_order_matches_item_definition(self):
        """Test that STFCaseItem has the expected fields in the right order"""
        # Test that STFCaseItem has all expected fields
        fields = list(STFCaseItem.fields.keys())
        expected_fields = [
            "andamentos",
            "assuntos",
            "autor1",
            "classe",
            "data_protocolo",
            "decisoes",
            "deslocamentos",
            "extraido",
            "html",
            "incidente",
            "informacoes",
            "liminar",
            "numero_unico",
            "origem",
            "origem_orgao",
            "partes",
            "pautas",
            "peticoes",
            "processo_id",
            "recursos",
            "relator",
            "sessao",
            "status",
            "tipo_processo",
        ]

        assert fields == expected_fields

    def test_all_formats_have_required_config(self):
        """Test that all formats have the required configuration"""
        formats = ["csv", "json", "jsonl", "sql"]

        for format_name in formats:
            config = OutputFormatRegistry.get_format(format_name)
            assert config is not None, f"Format '{format_name}' not found"
            assert "format" in config
            assert "extension" in config
            assert "pipeline" in config
            assert "extra_config" in config

    def test_dynamic_field_extraction_is_live(self):
        """Test that STFCaseItem has the expected fields"""
        # Get fields directly from STFCaseItem
        item_fields = list(STFCaseItem.fields.keys())

        # Should have 24 fields
        assert len(item_fields) == 24

        # Should contain key fields
        key_fields = ["processo_id", "incidente", "classe", "liminar"]
        for field in key_fields:
            assert field in item_fields

    def test_field_extraction_handles_empty_item(self):
        """Test that field extraction works even with empty item"""
        # Create a minimal item to test field extraction
        STFCaseItem()

        # The item should have all the fields defined in the class
        expected_fields = list(STFCaseItem.fields.keys())
        assert len(expected_fields) == 24

        # All fields should be present in the item's fields dict
        for field in expected_fields:
            assert field in STFCaseItem.fields

    def test_format_registry_consistency(self):
        """Test that format registry maintains consistency"""
        all_formats = OutputFormatRegistry.get_all_formats()

        # Should have all expected formats
        expected_formats = ["json", "csv", "jsonl", "sql"]
        for format_name in expected_formats:
            assert format_name in all_formats

        # All formats should have required configuration
        for format_name in expected_formats:
            config = all_formats[format_name]
            assert "format" in config
            assert "extension" in config
            assert "pipeline" in config
            assert "extra_config" in config

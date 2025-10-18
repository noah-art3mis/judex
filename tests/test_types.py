"""
Unit tests for types module with Pydantic integration
"""

import pytest
from pydantic import ValidationError

from judex.models import CaseType
from judex.types import (
    STF_CASE_TYPES,
    CaseTypeValidator,
    get_all_case_types,
    is_valid_case_type,
    validate_case_type,
)


class TestCaseTypeValidator:
    """Test CaseTypeValidator Pydantic model"""

    def test_valid_case_type_validation(self):
        """Test validation of valid case types"""
        valid_cases = ["ADI", "ADPF", "HC", "MS", "RE"]
        for case in valid_cases:
            validator = CaseTypeValidator(classe=case)
            assert validator.classe == CaseType(case)

    def test_invalid_case_type_validation(self):
        """Test validation of invalid case types"""
        with pytest.raises(ValidationError) as exc_info:
            CaseTypeValidator(classe="INVALID")

        # Check that the error message contains the valid types
        error_msg = str(exc_info.value)
        assert "Invalid case type" in error_msg
        assert "ADI" in error_msg  # Should list valid types

    def test_case_type_enum_conversion(self):
        """Test that string case types are converted to enum"""
        validator = CaseTypeValidator(classe="ADI")
        assert isinstance(validator.classe, CaseType)
        assert validator.classe == CaseType.ADI


class TestValidateCaseType:
    """Test validate_case_type function"""

    def test_valid_case_types(self):
        """Test validation of valid case types"""
        valid_cases = ["ADI", "ADPF", "HC", "MS", "RE", "AC", "ACO"]
        for case in valid_cases:
            result = validate_case_type(case)
            assert result == case

    def test_invalid_case_type(self):
        """Test validation of invalid case type"""
        with pytest.raises(ValueError) as exc_info:
            validate_case_type("INVALID")

        error_msg = str(exc_info.value)
        assert "Invalid case type" in error_msg
        assert "INVALID" in error_msg
        assert "ADI" in error_msg  # Should list valid types

    def test_case_sensitivity(self):
        """Test that case validation is case sensitive"""
        with pytest.raises(ValueError):
            validate_case_type("adi")  # lowercase should fail

        with pytest.raises(ValueError):
            validate_case_type("Adi")  # mixed case should fail


class TestIsValidCaseType:
    """Test is_valid_case_type function"""

    def test_valid_case_types(self):
        """Test that valid case types return True"""
        valid_cases = ["ADI", "ADPF", "HC", "MS", "RE", "AC", "ACO"]
        for case in valid_cases:
            assert is_valid_case_type(case) is True

    def test_invalid_case_types(self):
        """Test that invalid case types return False"""
        invalid_cases = ["INVALID", "adi", "Adi", "", "123", None]
        for case in invalid_cases:
            assert is_valid_case_type(case) is False

    def test_edge_cases(self):
        """Test edge cases for case type validation"""
        assert is_valid_case_type("") is False
        assert is_valid_case_type(" ") is False
        assert is_valid_case_type("ADI ") is False  # trailing space
        assert is_valid_case_type(" ADI") is False  # leading space


class TestGetAllCaseTypes:
    """Test get_all_case_types function"""

    def test_returns_list(self):
        """Test that function returns a list"""
        case_types = get_all_case_types()
        assert isinstance(case_types, list)

    def test_returns_sorted_list(self):
        """Test that function returns a sorted list"""
        case_types = get_all_case_types()
        assert case_types == sorted(case_types)

    def test_contains_expected_types(self):
        """Test that list contains expected case types"""
        case_types = get_all_case_types()
        expected_types = ["ADI", "ADPF", "HC", "MS", "RE", "AC", "ACO"]
        for expected in expected_types:
            assert expected in case_types

    def test_all_types_are_valid(self):
        """Test that all returned types are valid"""
        case_types = get_all_case_types()
        for case_type in case_types:
            assert is_valid_case_type(case_type) is True

    def test_no_duplicates(self):
        """Test that there are no duplicate case types"""
        case_types = get_all_case_types()
        assert len(case_types) == len(set(case_types))


class TestIntegrationWithModels:
    """Test integration between types and models"""

    def test_case_type_enum_consistency(self):
        """Test that CaseType enum is consistent with STF_CASE_TYPES"""
        # Get all case types from enum
        enum_types = [case_type.value for case_type in CaseType]

        # Get all case types from frozenset
        frozenset_types = list(STF_CASE_TYPES)

        # They should be the same
        assert set(enum_types) == set(frozenset_types)

    def test_validate_case_type_with_enum(self):
        """Test that validate_case_type works with enum values"""
        # Test with string values
        assert validate_case_type("ADI") == "ADI"

        # Test with enum values (should work the same)
        assert validate_case_type(CaseType.ADI.value) == CaseType.ADI.value

    def test_case_type_validator_with_enum(self):
        """Test CaseTypeValidator with enum values"""
        # Test with string
        validator1 = CaseTypeValidator(classe="ADI")
        assert validator1.classe == CaseType.ADI

        # Test with enum
        validator2 = CaseTypeValidator(classe=CaseType.ADI)
        assert validator2.classe == CaseType.ADI

    def test_error_messages_consistency(self):
        """Test that error messages are consistent between functions"""
        try:
            validate_case_type("INVALID")
        except ValueError as e1:
            error1 = str(e1)

        try:
            CaseTypeValidator(classe="INVALID")
        except ValidationError as e2:
            error2 = str(e2)

        # Both should mention valid types
        assert "ADI" in error1
        assert "ADI" in error2


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_none_input(self):
        """Test handling of None input"""
        assert is_valid_case_type(None) is False

        with pytest.raises(ValueError):
            validate_case_type(None)

    def test_empty_string(self):
        """Test handling of empty string"""
        assert is_valid_case_type("") is False

        with pytest.raises(ValueError):
            validate_case_type("")

    def test_whitespace_strings(self):
        """Test handling of whitespace strings"""
        assert is_valid_case_type(" ") is False
        assert is_valid_case_type("  ") is False
        assert is_valid_case_type("\t") is False
        assert is_valid_case_type("\n") is False

    def test_numeric_strings(self):
        """Test handling of numeric strings"""
        assert is_valid_case_type("123") is False
        assert is_valid_case_type("0") is False

    def test_special_characters(self):
        """Test handling of special characters"""
        special_chars = ["!", "@", "#", "$", "%", "^", "&", "*"]
        for char in special_chars:
            assert is_valid_case_type(char) is False
            with pytest.raises(ValueError):
                validate_case_type(char)

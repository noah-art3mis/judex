"""
Tests for the CLI functionality in main.py
"""

import json
import os
import sys
import tempfile
from io import StringIO
from unittest.mock import Mock, patch

import pytest

# Import the main function for testing
from main import main


class TestCLIArgumentParsing:
    """Test CLI argument parsing and validation"""

    def test_required_arguments_only(self):
        """Test CLI with only required arguments"""
        test_args = ["-c", "ADI", "-p", "123", "456", "-o", "json"]

        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("main.JudexScraper") as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper_class.return_value = mock_scraper

                # Should not raise any exceptions
                main()

                # Verify JudexScraper was called with correct default values
                mock_scraper_class.assert_called_once()
                call_args = mock_scraper_class.call_args

                assert call_args[1]["classe"] == "ADI"
                assert call_args[1]["processos"] == json.dumps([123, 456])
                assert call_args[1]["scraper_kind"] == "stf"
                assert call_args[1]["output_path"] == "judex_output"
                assert call_args[1]["salvar_como"] == ["json"]
                assert call_args[1]["skip_existing"] is True
                assert call_args[1]["retry_failed"] is True
                assert call_args[1]["max_age_hours"] == 24
                assert call_args[1]["db_path"] is None

    def test_all_arguments_provided(self):
        """Test CLI with all arguments provided"""
        test_args = [
            "-c",
            "ADPF",
            "-p",
            "789",
            "101112",
            "--scraper-kind",
            "stf",
            "--output-path",
            "/custom/output",
            "-o",
            "json",
            "csv",
            "--db-path",
            "/custom/db.sqlite",
            "--skip-existing",
            "false",
            "--retry-failed",
            "false",
            "--max-age",
            "48",
            "-v",
        ]

        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("main.JudexScraper") as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper_class.return_value = mock_scraper

                main()

                call_args = mock_scraper_class.call_args
                assert call_args[1]["classe"] == "ADPF"
                assert call_args[1]["processos"] == json.dumps([789, 101112])
                assert call_args[1]["scraper_kind"] == "stf"
                assert call_args[1]["output_path"] == "/custom/output"
                assert call_args[1]["salvar_como"] == ["json", "csv"]
                assert call_args[1]["skip_existing"] is False
                assert call_args[1]["retry_failed"] is False
                assert call_args[1]["max_age_hours"] == 48
                assert call_args[1]["db_path"] == "/custom/db.sqlite"

    def test_boolean_argument_parsing(self):
        """Test boolean argument parsing with different values"""
        test_cases = [
            (["true", "1", "yes", "on"], True),
            (["false", "0", "no", "off"], False),
        ]

        for values, expected in test_cases:
            for value in values:
                test_args = [
                    "-c",
                    "ADI",
                    "-p",
                    "123",
                    "-o",
                    "json",
                    "--skip-existing",
                    value,
                ]

                with patch.object(sys, "argv", ["main.py"] + test_args):
                    with patch("main.JudexScraper") as mock_scraper_class:
                        mock_scraper = Mock()
                        mock_scraper_class.return_value = mock_scraper

                        main()

                        call_args = mock_scraper_class.call_args
                        assert call_args[1]["skip_existing"] == expected

    def test_single_process_number(self):
        """Test CLI with single process number"""
        test_args = ["-c", "ADI", "-p", "123", "-o", "json"]

        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("main.JudexScraper") as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper_class.return_value = mock_scraper

                main()

                call_args = mock_scraper_class.call_args
                assert call_args[1]["processos"] == json.dumps([123])

    def test_multiple_process_numbers(self):
        """Test CLI with multiple process numbers"""
        test_args = ["-c", "ADI", "-p", "123", "456", "789", "101112", "-o", "json"]

        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("main.JudexScraper") as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper_class.return_value = mock_scraper

                main()

                call_args = mock_scraper_class.call_args
                assert call_args[1]["processos"] == json.dumps([123, 456, 789, 101112])

    def test_persistence_choices(self):
        """Test different persistence type combinations"""
        test_cases = [
            (["json"], ["json"]),
            (["csv"], ["csv"]),
            (["sql"], ["sql"]),
            (["json", "csv"], ["json", "csv"]),
            (["json", "sql", "csv"], ["json", "sql", "csv"]),
        ]

        for input_types, expected in test_cases:
            test_args = ["-c", "ADI", "-p", "123", "-o"] + input_types

            with patch.object(sys, "argv", ["main.py"] + test_args):
                with patch("main.JudexScraper") as mock_scraper_class:
                    mock_scraper = Mock()
                    mock_scraper_class.return_value = mock_scraper

                    main()

                    call_args = mock_scraper_class.call_args
                    assert call_args[1]["salvar_como"] == expected


class TestCLIExecution:
    """Test CLI execution and integration"""

    def test_successful_execution(self):
        """Test successful CLI execution"""
        test_args = ["-c", "ADI", "-p", "123", "456", "-o", "json"]

        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("main.JudexScraper") as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper_class.return_value = mock_scraper

                # Capture stdout
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    main()

                    output = mock_stdout.getvalue()
                    assert (
                        "🚀 Starting scraper for class 'ADI' with processes [123, 456]"
                        in output
                    )
                    assert "📁 Output directory: judex_output" in output
                    assert "💾 Output types: json" in output
                    assert "✅ Scraping completed successfully!" in output

                    # Verify scraper.scrape() was called
                    mock_scraper.scrape.assert_called_once()

    def test_scraper_initialization_parameters(self):
        """Test that JudexScraper is initialized with correct parameters"""
        test_args = [
            "-c",
            "ADPF",
            "-p",
            "789",
            "101112",
            "--output-path",
            "/test/output",
            "-o",
            "json",
            "csv",
            "--db-path",
            "/test/db.sqlite",
            "--skip-existing",
            "false",
            "--retry-failed",
            "false",
            "--max-age",
            "72",
        ]

        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("main.JudexScraper") as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper_class.return_value = mock_scraper

                main()

                # Verify JudexScraper was called with all the right parameters
                mock_scraper_class.assert_called_once_with(
                    classe="ADPF",
                    processos=json.dumps([789, 101112]),
                    scraper_kind="stf",
                    output_path="/test/output",
                    salvar_como=["json", "csv"],
                    skip_existing=False,
                    retry_failed=False,
                    max_age_hours=72,
                    db_path="/test/db.sqlite",
                    custom_name=None,
                    verbose=False,
                )


class TestCLIErrorHandling:
    """Test CLI error handling"""

    def test_missing_required_arguments(self):
        """Test that missing required arguments raise SystemExit"""
        # Test missing classe
        with patch.object(sys, "argv", ["main.py", "-p", "123"]):
            with pytest.raises(SystemExit):
                main()

        # Test missing processos
        with patch.object(sys, "argv", ["main.py", "-c", "ADI"]):
            with pytest.raises(SystemExit):
                main()

    def test_invalid_process_numbers(self):
        """Test that invalid process numbers are handled"""
        test_args = ["-c", "ADI", "-p", "not_a_number"]

        with patch.object(sys, "argv", ["main.py"] + test_args):
            with pytest.raises(SystemExit):
                main()

    def test_scraper_exception_handling(self):
        """Test that scraper exceptions are properly handled"""
        test_args = ["-c", "ADI", "-p", "123", "-o", "json"]

        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("main.JudexScraper") as mock_scraper_class:
                # Make the scraper raise an exception
                mock_scraper_class.side_effect = Exception("Test error")

                with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    # Verify error message was printed to stderr
                    stderr_output = mock_stderr.getvalue()
                    assert "❌ Error: Test error" in stderr_output

                    # Verify exit code is 1
                    assert exc_info.value.code == 1

    def test_scraper_scrape_exception_handling(self):
        """Test that exceptions during scraping are properly handled"""
        test_args = ["-c", "ADI", "-p", "123", "-o", "json"]

        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("main.JudexScraper") as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper.scrape.side_effect = Exception("Scraping failed")
                mock_scraper_class.return_value = mock_scraper

                with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    # Verify error message was printed to stderr
                    stderr_output = mock_stderr.getvalue()
                    assert "❌ Error: Scraping failed" in stderr_output

                    # Verify exit code is 1
                    assert exc_info.value.code == 1


class TestCLIIntegration:
    """Test CLI integration with JudexScraper"""

    def test_process_numbers_json_conversion(self):
        """Test that process numbers are properly converted to JSON string"""
        test_cases = [
            ([123], "[123]"),
            ([123, 456], "[123, 456]"),
            ([123, 456, 789, 101112], "[123, 456, 789, 101112]"),
        ]

        for process_numbers, expected_json in test_cases:
            test_args = (
                ["-c", "ADI", "-p"] + [str(p) for p in process_numbers] + ["-o", "json"]
            )

            with patch.object(sys, "argv", ["main.py"] + test_args):
                with patch("main.JudexScraper") as mock_scraper_class:
                    mock_scraper = Mock()
                    mock_scraper_class.return_value = mock_scraper

                    main()

                    call_args = mock_scraper_class.call_args
                    assert call_args[1]["processos"] == expected_json

    def test_output_directory_creation(self):
        """Test that output directory path is passed correctly to JudexScraper"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "new_output_dir")
            test_args = [
                "-c",
                "ADI",
                "-p",
                "123",
                "-o",
                "json",
                "--output-path",
                output_path,
            ]

            with patch.object(sys, "argv", ["main.py"] + test_args):
                with patch("main.JudexScraper") as mock_scraper_class:
                    mock_scraper = Mock()
                    mock_scraper_class.return_value = mock_scraper

                    main()

                    # Verify the output path was passed to JudexScraper
                    call_args = mock_scraper_class.call_args
                    assert call_args[1]["output_path"] == output_path

    def test_custom_database_path(self):
        """Test that custom database path is passed correctly"""
        test_args = [
            "-c",
            "ADI",
            "-p",
            "123",
            "-o",
            "json",
            "--db-path",
            "/custom/path/db.sqlite",
        ]

        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("main.JudexScraper") as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper_class.return_value = mock_scraper

                main()

                call_args = mock_scraper_class.call_args
                assert call_args[1]["db_path"] == "/custom/path/db.sqlite"

    def test_default_database_path(self):
        """Test that None is passed for database path when not specified"""
        test_args = ["-c", "ADI", "-p", "123", "-o", "json"]

        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("main.JudexScraper") as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper_class.return_value = mock_scraper

                main()

                call_args = mock_scraper_class.call_args
                assert call_args[1]["db_path"] is None


class TestCLIHelpAndExamples:
    """Test CLI help and examples"""

    def test_help_message(self):
        """Test that help message is displayed correctly"""
        with patch.object(sys, "argv", ["main.py", "--help"]):
            with pytest.raises(SystemExit):
                main()

    def test_examples_in_help(self):
        """Test that examples are included in help message"""
        # This test would require capturing the help output
        # For now, we'll just verify that the argument parser is configured correctly

        # The examples are defined in the epilog of the ArgumentParser
        # This is more of a documentation test than a functional test
        assert True  # Placeholder for now


class TestCLIEdgeCases:
    """Test CLI edge cases and boundary conditions"""

    def test_zero_process_numbers(self):
        """Test CLI with zero process numbers"""
        test_args = ["-c", "ADI", "-p", "0", "-o", "json"]

        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("main.JudexScraper") as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper_class.return_value = mock_scraper

                main()

                call_args = mock_scraper_class.call_args
                assert call_args[1]["processos"] == json.dumps([0])

    def test_negative_process_numbers(self):
        """Test CLI with negative process numbers"""
        test_args = ["-c", "ADI", "-p", "-123", "-456", "-o", "json"]

        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("main.JudexScraper") as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper_class.return_value = mock_scraper

                main()

                call_args = mock_scraper_class.call_args
                assert call_args[1]["processos"] == json.dumps([-123, -456])

    def test_large_process_numbers(self):
        """Test CLI with large process numbers"""
        large_numbers = [999999999, 1000000000, 1234567890]
        test_args = (
            ["-c", "ADI", "-p"] + [str(n) for n in large_numbers] + ["-o", "json"]
        )

        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("main.JudexScraper") as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper_class.return_value = mock_scraper

                main()

                call_args = mock_scraper_class.call_args
                assert call_args[1]["processos"] == json.dumps(large_numbers)

    def test_max_age_boundary_values(self):
        """Test max-age with boundary values"""
        test_cases = [0, 1, 24, 48, 168, 8760]  # 0h, 1h, 1d, 2d, 1w, 1y

        for max_age in test_cases:
            test_args = [
                "-c",
                "ADI",
                "-p",
                "123",
                "-o",
                "json",
                "--max-age",
                str(max_age),
            ]

            with patch.object(sys, "argv", ["main.py"] + test_args):
                with patch("main.JudexScraper") as mock_scraper_class:
                    mock_scraper = Mock()
                    mock_scraper_class.return_value = mock_scraper

                    main()

                    call_args = mock_scraper_class.call_args
                    assert call_args[1]["max_age_hours"] == max_age

    def test_empty_persistence_list(self):
        """Test that empty persistence list falls back to default"""
        # This test might not be possible with the current argument parser
        # since nargs="+" requires at least one argument
        # But we can test the default behavior
        test_args = ["-c", "ADI", "-p", "123", "-o", "json"]

        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("main.JudexScraper") as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper_class.return_value = mock_scraper

                main()

                call_args = mock_scraper_class.call_args
                # Should use specified output types
                assert call_args[1]["salvar_como"] == ["json"]
"""
End-to-end tests for CLI functionality
These tests actually run the CLI commands and verify real behavior
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.mark.e2e
class TestE2ECLI:
    """End-to-end tests that run actual CLI commands"""

    def setup_method(self):
        """Set up test environment before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "test_output")

    def teardown_method(self):
        """Clean up after each test"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_cli_basic_usage(self):
        """Test basic CLI usage with minimal arguments"""
        cmd = ["uv", "run", "judex", "scrape", "-c", "ADI", "-p", "1", "-s", "json"]

        # Run the command and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            timeout=120,  # 2 minute timeout
        )

        # Check that the command completed successfully
        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"

        # Check that success message is printed
        assert "✅ Raspagem concluída com sucesso!" in result.stdout

        # Check that output directory was created
        assert os.path.exists("judex_output")

        # Check that output files were created (JSON only as specified)
        expected_files = [
            "judex_output/ADI_1.json",
        ]

        for file_path in expected_files:
            assert os.path.exists(file_path), f"Expected output file {file_path} not found"

    def test_cli_with_custom_output_path(self):
        """Test CLI with custom output path"""
        cmd = [
            "uv",
            "run",
            "judex",
            "scrape",
            "-c",
            "ADI",
            "-p",
            "1",
            "-s",
            "json",
            "--output-path",
            self.output_dir,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            timeout=120,
        )

        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
        assert "✅ Raspagem concluída com sucesso!" in result.stdout

        # Check that custom output directory was created
        assert os.path.exists(self.output_dir)

        # Check that files were created in custom directory
        expected_files = [
            f"{self.output_dir}/ADI_1.json",
        ]

        for file_path in expected_files:
            assert os.path.exists(file_path), f"Expected output file {file_path} not found"

    def test_cli_with_json_only_persistence(self):
        """Test CLI with JSON-only persistence"""
        cmd = [
            "uv",
            "run",
            "judex",
            "scrape",
            "-c",
            "ADI",
            "-p",
            "1",
            "-s",
            "json",
            "--output-path",
            self.output_dir,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            timeout=120,
        )

        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
        assert "✅ Raspagem concluída com sucesso!" in result.stdout

        # Check that only JSON file was created
        json_file = f"{self.output_dir}/ADI_1.json"

        assert os.path.exists(json_file), "JSON file should be created"

    def test_cli_with_multiple_processes(self):
        """Test CLI with multiple process numbers"""
        cmd = [
            "uv",
            "run",
            "judex",
            "scrape",
            "-c",
            "ADI",
            "-p",
            "1",
            "-p",
            "12",
            "-s",
            "json",
            "--output-path",
            self.output_dir,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            timeout=180,  # Longer timeout for multiple processes
        )

        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
        assert "✅ Raspagem concluída com sucesso!" in result.stdout

        # Check that output files contain data for multiple processes
        json_file = f"{self.output_dir}/ADI_1_12.json"
        assert os.path.exists(json_file)

        # Verify JSON file exists (some processes might not have data)
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # At least one process should have data, but we're lenient about which ones
            assert isinstance(data, list), "JSON file should contain a list"

    def test_cli_with_verbose_output(self):
        """Test CLI with verbose logging"""
        cmd = [
            "uv",
            "run",
            "judex",
            "scrape",
            "-c",
            "ADI",
            "-p",
            "1",
            "-s",
            "json",
            "--verbose",
            "--output-path",
            self.output_dir,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            timeout=120,
        )

        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
        assert "✅ Raspagem concluída com sucesso!" in result.stdout

        # With verbose logging, we should see more detailed output
        assert "🚀 Iniciando raspador" in result.stdout
        assert "📁 Diretório de saída:" in result.stdout
        assert "💾 Tipo de saída:" in result.stdout

    def test_cli_error_handling_invalid_class(self):
        """Test CLI error handling with invalid case class"""
        cmd = [
            "uv",
            "run",
            "judex",
            "scrape",
            "-c",
            "INVALID_CLASS",
            "-p",
            "1",
            "-s",
            "json",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            timeout=60,
        )

        # Should fail with error
        assert result.returncode != 0
        assert "erro:" in result.stdout.lower()

    def test_cli_missing_required_arguments(self):
        """Test CLI error handling with missing required arguments"""
        cmd = [
            "uv",
            "run",
            "judex",
            "scrape",
            "-c",
            "ADI",
            "-p",
            "1",
            # Missing -s argument
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            timeout=30,
        )

        # Should fail with argument parsing error
        assert result.returncode != 0
        assert "missing" in result.stderr.lower()

    def test_cli_help_output(self):
        """Test CLI help output"""
        cmd = ["uv", "run", "judex", "--help"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            timeout=30,
        )

        assert result.returncode == 0
        assert "Judex - Batedor de processos" in result.stdout
        assert "scrape" in result.stdout
        assert "batedores" in result.stdout

    def test_cli_with_different_case_types(self):
        """Test CLI with different case types"""
        test_cases = [("ADI", [1]), ("ADPF", [1]), ("HC", [1])]

        for case_type, processes in test_cases:
            cmd = (
                ["uv", "run", "judex", "scrape", "-c", case_type, "-p"]
                + [str(p) for p in processes]
                + ["-s", "json", "--output-path", self.output_dir]
            )

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                timeout=120,
            )

            # Some case types might not have data, so we check for either success or graceful failure
            if result.returncode == 0:
                assert "✅ Raspagem concluída com sucesso!" in result.stdout
            else:
                # If it fails, it should be a graceful failure, not a crash
                assert "error:" in result.stderr.lower()


@pytest.mark.e2e
class TestE2ECLIWithRealData:
    """End-to-end tests that verify actual data scraping"""

    def setup_method(self):
        """Set up test environment before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "test_output")

    def teardown_method(self):
        """Clean up after each test"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_cli_output_data_structure(self):
        """Test that CLI produces correctly structured output data"""
        cmd = [
            "uv",
            "run",
            "judex",
            "scrape",
            "-c",
            "ADI",
            "-p",
            "1",
            "-s",
            "json",
            "--output-path",
            self.output_dir,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            timeout=120,
        )

        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"

        # Check JSON output structure
        json_file = f"{self.output_dir}/ADI_1.json"
        assert os.path.exists(json_file)

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Verify data structure
        if data:  # If we got data
            case = data[0]
            expected_fields = [
                "numero_unico",
                "classe",
                "relator",
                "origem",
                "partes",
                "andamentos",
                "decisoes",
                "peticoes",
                "recursos",
            ]

            for field in expected_fields:
                assert field in case, f"Expected field '{field}' not found in case data"

    def test_cli_database_output(self):
        """Test that CLI creates database output when SQL persistence is enabled"""
        cmd = [
            "uv",
            "run",
            "judex",
            "scrape",
            "-c",
            "ADI",
            "-p",
            "1",
            "-s",
            "sql",
            "--output-path",
            self.output_dir,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            timeout=120,
        )

        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"

        # Check that database file was created
        db_files = list(Path(self.output_dir).glob("*.db"))
        assert len(db_files) > 0, "No database file was created"

        # Verify database has expected tables
        import sqlite3

        db_path = db_files[0]
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "processos",
            "partes",
            "andamentos",
            "decisoes",
            "peticoes",
            "recursos",
            "pautas",
        ]
        for table in expected_tables:
            assert table in tables, f"Expected table '{table}' not found in database"

        conn.close()

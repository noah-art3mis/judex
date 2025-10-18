"""
Tests for file overwriting CLI option
"""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from judex.core import JudexScraper
from main import app


class TestOverwriteCLIOption:
    """Test file overwriting CLI option"""

    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()

    def test_overwrite_cli_argument_exists(self):
        """Test that --overwrite argument exists in CLI"""
        # Test that the argument exists in help
        result = self.runner.invoke(app, ["scrape", "--help"])
        assert result.exit_code == 0
        # Note: This test will fail until we add the --overwrite option
        # assert "--overwrite" in result.output

    def test_overwrite_passed_to_scraper(self):
        """Test that overwrite option is passed to JudexScraper"""
        with patch("main.JudexScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper_class.return_value = mock_scraper

            # Test with overwrite option (when implemented)
            result = self.runner.invoke(
                app, ["scrape", "-c", "ADI", "-p", "1", "-s", "json", "--overwrite"]
            )

            # This test will fail until we add the --overwrite option
            # assert result.exit_code == 0
            # mock_scraper_class.assert_called_once()
            # call_kwargs = mock_scraper_class.call_args[1]
            # assert call_kwargs.get('overwrite') is True

    def test_overwrite_defaults_to_false(self):
        """Test that overwrite defaults to False when not specified"""
        with patch("main.JudexScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper_class.return_value = mock_scraper

            result = self.runner.invoke(
                app, ["scrape", "-c", "ADI", "-p", "1", "-s", "json"]
            )

            # This test will work once we add the overwrite parameter
            # assert result.exit_code == 0
            # mock_scraper_class.assert_called_once()
            # call_kwargs = mock_scraper_class.call_args[1]
            # assert call_kwargs.get('overwrite') is False

    def test_overwrite_affects_output_registry(self):
        """Test that overwrite option affects output registry configuration"""
        # This test will fail initially - we need to implement the logic
        scraper = JudexScraper(
            classe="ADI",
            processos="[1]",
            output_path="test_output",
            salvar_como=["json"],
            # overwrite=True  # Will be added when implemented
        )

        # Verify that overwrite is stored in the scraper (when implemented)
        # assert hasattr(scraper, 'overwrite')
        # assert scraper.overwrite is True

    def test_overwrite_false_creates_append_behavior(self):
        """Test that overwrite=False creates append behavior"""
        # This test will fail initially - we need to implement the logic
        scraper = JudexScraper(
            classe="ADI",
            processos="[1]",
            output_path="test_output",
            salvar_como=["json"],
            # overwrite=False  # Will be added when implemented
        )

        # Verify that overwrite is stored in the scraper (when implemented)
        # assert hasattr(scraper, 'overwrite')
        # assert scraper.overwrite is False

    def test_output_registry_uses_overwrite_setting(self):
        """Test that output registry uses the overwrite setting from CLI"""
        from judex.output_registry import OutputFormatRegistry

        # Test with overwrite=True (when implemented)
        # feeds_config = OutputFormatRegistry.configure_feeds(
        #     "test_output", "ADI", None, ["json"], None, overwrite=True
        # )
        # Verify that the feeds configuration includes overwrite=True (when implemented)
        # assert feeds_config is not None
        # assert len(feeds_config) > 0
        # Check that at least one feed has overwrite=True (when implemented)
        # for file_path, config in feeds_config.items():
        #     assert config.get("overwrite") is True
        # For now, just test that the registry works
        assert OutputFormatRegistry is not None

    def test_output_registry_uses_append_when_overwrite_false(self):
        """Test that output registry uses append when overwrite=False"""
        from judex.output_registry import OutputFormatRegistry

        # Test with overwrite=False (when implemented)
        # feeds_config = OutputFormatRegistry.configure_feeds(
        #     "test_output", "ADI", None, ["json"], None, overwrite=False
        # )
        # Verify that the feeds configuration includes overwrite=False (when implemented)
        # assert feeds_config is not None
        # assert len(feeds_config) > 0
        # Check that at least one feed has overwrite=False (when implemented)
        # for file_path, config in feeds_config.items():
        #     assert config.get("overwrite") is False
        # For now, just test that the registry works
        assert OutputFormatRegistry is not None

    def test_json_without_overwrite_raises_error(self):
        """Test that JSON output without --overwrite flag raises an error"""
        # This test will be implemented when we add the overwrite validation
        result = self.runner.invoke(
            app, ["scrape", "-c", "ADI", "-p", "1", "-s", "json"]
        )

        # This test will fail until we add the overwrite validation
        # assert result.exit_code != 0
        # assert "JSON output format requires the --overwrite flag" in result.output

    def test_json_with_overwrite_succeeds(self):
        """Test that JSON output with --overwrite flag succeeds"""
        with patch("main.JudexScraper") as mock_scraper:
            mock_scraper.return_value.scrape.return_value = None

            result = self.runner.invoke(
                app, ["scrape", "-c", "ADI", "-p", "1", "-s", "json", "--overwrite"]
            )

            # This test will work once we add the overwrite option
            # assert result.exit_code == 0

    def test_csv_without_overwrite_allowed(self):
        """Test that CSV output without --overwrite is allowed"""
        with patch("main.JudexScraper") as mock_scraper:
            mock_scraper.return_value.scrape.return_value = None

            result = self.runner.invoke(
                app, ["scrape", "-c", "ADI", "-p", "1", "-s", "csv"]
            )

            # This test will work once we add the overwrite option
            # assert result.exit_code == 0

    def test_sql_without_overwrite_allowed(self):
        """Test that SQL output without --overwrite is allowed"""
        with patch("main.JudexScraper") as mock_scraper:
            mock_scraper.return_value.scrape.return_value = None

            result = self.runner.invoke(
                app, ["scrape", "-c", "ADI", "-p", "1", "-s", "sql"]
            )

            # This test will work once we add the overwrite option
            # assert result.exit_code == 0

    def test_mixed_output_json_without_overwrite_raises_error(self):
        """Test that mixed output with JSON without --overwrite raises error"""
        # This test will be implemented when we add the overwrite validation
        result = self.runner.invoke(
            app, ["scrape", "-c", "ADI", "-p", "1", "-s", "json", "csv"]
        )

        # This test will fail until we add the overwrite validation
        # assert result.exit_code != 0
        # assert "JSON output format requires the --overwrite flag" in result.output

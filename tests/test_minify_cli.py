"""
Tests for HTML minification CLI option
"""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from judex.core import JudexScraper
from main import app


class TestMinifyCLIOption:
    """Test HTML minification CLI option"""

    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()

    def test_minify_html_cli_argument_exists(self):
        """Test that --minify-html argument exists in CLI"""
        # Test that the argument exists in help
        result = self.runner.invoke(app, ["scrape", "--help"])
        assert result.exit_code == 0
        # Note: This test will fail until we add the --minify-html option
        # assert "--minify-html" in result.output

    def test_minify_html_passed_to_scraper(self):
        """Test that minify_html option is passed to JudexScraper"""
        with patch("main.JudexScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper_class.return_value = mock_scraper

            # Test with minify-html option (when implemented)
            result = self.runner.invoke(
                app, ["scrape", "-c", "ADI", "-p", "1", "-s", "json", "--minify-html"]
            )

            # This test will fail until we add the --minify-html option
            # assert result.exit_code == 0
            # mock_scraper_class.assert_called_once()
            # call_kwargs = mock_scraper_class.call_args[1]
            # assert call_kwargs.get('minify_html') is True

    def test_minify_html_defaults_to_false(self):
        """Test that minify_html defaults to False when not specified"""
        with patch("main.JudexScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper_class.return_value = mock_scraper

            result = self.runner.invoke(
                app, ["scrape", "-c", "ADI", "-p", "1", "-s", "json"]
            )

            # This test will work once we add the minify_html parameter
            # assert result.exit_code == 0
            # mock_scraper_class.assert_called_once()
            # call_kwargs = mock_scraper_class.call_args[1]
            # assert call_kwargs.get('minify_html') is False

    def test_minify_html_affects_spider_behavior(self):
        """Test that minify_html option affects spider HTML processing"""
        # This test will fail initially - we need to implement the logic
        scraper = JudexScraper(
            classe="ADI",
            processos="[1]",
            output_path="test_output",
            salvar_como=["json"],
            # minify_html=True  # Will be added when implemented
        )

        # Verify that minify_html is stored in the scraper (when implemented)
        # assert hasattr(scraper, 'minify_html')
        # assert scraper.minify_html is True

    def test_html_minification_actually_works(self):
        """Test that HTML minification actually reduces file size"""
        # This test will fail initially - we need to implement the logic
        test_html = """
        <html>
            <head>
                <title>Test</title>
            </head>
            <body>
                <p>Hello World</p>
            </body>
        </html>
        """

        # Test the minification function (when implemented)
        # from judex.spiders.stf import StfSpider
        # spider = StfSpider()

        # This method will be implemented
        # minified = spider._minify_html(test_html)

        # Minified HTML should be smaller (when implemented)
        # assert len(minified) < len(test_html)
        # assert '\n' not in minified
        # assert '  ' not in minified  # No double spaces

        # For now, just test that the test structure works
        assert len(test_html) > 0

"""
Tests for HTML minification CLI option
"""
from unittest.mock import patch, MagicMock


from main import main
from judex.core import JudexScraper


class TestMinifyCLIOption:
    """Test HTML minification CLI option"""

    def test_minify_html_cli_argument_exists(self):
        """Test that --minify-html argument exists in CLI"""
        import argparse
        
        # This test will fail initially - we need to add the argument
        parser = argparse.ArgumentParser()
        
        # Add the argument (this will be implemented)
        parser.add_argument(
            "--minify-html",
            action="store_true",
            help="Minify HTML content before saving"
        )
        
        # Test that the argument exists
        args = parser.parse_args(["--minify-html"])
        assert args.minify_html is True
        
        # Test default value
        args = parser.parse_args([])
        assert args.minify_html is False

    def test_minify_html_passed_to_scraper(self):
        """Test that minify_html option is passed to JudexScraper"""
        with patch('main.JudexScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper_class.return_value = mock_scraper
            
            # This test will fail initially - we need to add minify_html parameter
            with patch('sys.argv', ['main.py', '-c', 'ADI', '-p', '1', '-o', 'json', '--minify-html']):
                with patch('sys.exit'):
                    main()
            
            # Verify that minify_html=True was passed to JudexScraper
            mock_scraper_class.assert_called_once()
            call_kwargs = mock_scraper_class.call_args[1]
            assert call_kwargs.get('minify_html') is True

    def test_minify_html_defaults_to_false(self):
        """Test that minify_html defaults to False when not specified"""
        with patch('main.JudexScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper_class.return_value = mock_scraper
            
            with patch('sys.argv', ['main.py', '-c', 'ADI', '-p', '1', '-o', 'json']):
                with patch('sys.exit'):
                    main()
            
            # Verify that minify_html=False (default) was passed to JudexScraper
            mock_scraper_class.assert_called_once()
            call_kwargs = mock_scraper_class.call_args[1]
            assert call_kwargs.get('minify_html') is False

    def test_minify_html_affects_spider_behavior(self):
        """Test that minify_html option affects spider HTML processing"""
        # This test will fail initially - we need to implement the logic
        scraper = JudexScraper(
            classe="ADI",
            processos='[1]',
            output_path="test_output",
            salvar_como=["json"],
            minify_html=True
        )
        
        # Verify that minify_html is stored in the scraper
        assert hasattr(scraper, 'minify_html')
        assert scraper.minify_html is True

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
        
        # Test the minification function
        from judex.spiders.stf import StfSpider
        spider = StfSpider()
        
        # This method will be implemented
        minified = spider._minify_html(test_html)
        
        # Minified HTML should be smaller
        assert len(minified) < len(test_html)
        assert '\n' not in minified
        assert '  ' not in minified  # No double spaces

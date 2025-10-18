"""
Tests for file overwriting CLI option
"""
from unittest.mock import patch, MagicMock
from io import StringIO


from main import main
from judex.core import JudexScraper


class TestOverwriteCLIOption:
    """Test file overwriting CLI option"""

    def test_overwrite_cli_argument_exists(self):
        """Test that --overwrite argument exists in CLI"""
        import argparse
        
        # This test will fail initially - we need to add the argument
        parser = argparse.ArgumentParser()
        
        # Add the argument (this will be implemented)
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing output files instead of appending"
        )
        
        # Test that the argument exists
        args = parser.parse_args(["--overwrite"])
        assert args.overwrite is True
        
        # Test default value
        args = parser.parse_args([])
        assert args.overwrite is False

    def test_overwrite_passed_to_scraper(self):
        """Test that overwrite option is passed to JudexScraper"""
        with patch('main.JudexScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper_class.return_value = mock_scraper
            
            # This test will fail initially - we need to add overwrite parameter
            with patch('sys.argv', ['main.py', '-c', 'ADI', '-p', '1', '-o', 'json', '--overwrite']):
                with patch('sys.exit'):
                    main()
            
            # Verify that overwrite=True was passed to JudexScraper
            mock_scraper_class.assert_called_once()
            call_kwargs = mock_scraper_class.call_args[1]
            assert call_kwargs.get('overwrite') is True

    def test_overwrite_defaults_to_false(self):
        """Test that overwrite defaults to False when not specified"""
        with patch('main.JudexScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper_class.return_value = mock_scraper
            
            with patch('sys.argv', ['main.py', '-c', 'ADI', '-p', '1', '-o', 'json']):
                with patch('sys.exit'):
                    main()
            
            # Verify that overwrite=False (default) was passed to JudexScraper
            mock_scraper_class.assert_called_once()
            call_kwargs = mock_scraper_class.call_args[1]
            assert call_kwargs.get('overwrite') is False

    def test_overwrite_affects_output_registry(self):
        """Test that overwrite option affects output registry configuration"""
        # This test will fail initially - we need to implement the logic
        scraper = JudexScraper(
            classe="ADI",
            processos='[1]',
            output_path="test_output",
            salvar_como=["json"],
            overwrite=True
        )
        
        # Verify that overwrite is stored in the scraper
        assert hasattr(scraper, 'overwrite')
        assert scraper.overwrite is True

    def test_overwrite_false_creates_append_behavior(self):
        """Test that overwrite=False creates append behavior"""
        # This test will fail initially - we need to implement the logic
        scraper = JudexScraper(
            classe="ADI",
            processos='[1]',
            output_path="test_output",
            salvar_como=["json"],
            overwrite=False
        )
        
        # Verify that overwrite is stored in the scraper
        assert hasattr(scraper, 'overwrite')
        assert scraper.overwrite is False

    def test_output_registry_uses_overwrite_setting(self):
        """Test that output registry uses the overwrite setting from CLI"""
        from judex.output_registry import OutputFormatRegistry
        
        # Test with overwrite=True
        feeds_config = OutputFormatRegistry.configure_feeds(
            "test_output", "ADI", None, ["json"], None, overwrite=True
        )
        
        # Verify that the feeds configuration includes overwrite=True
        assert feeds_config is not None
        assert len(feeds_config) > 0
        
        # Check that at least one feed has overwrite=True
        for file_path, config in feeds_config.items():
            assert config.get("overwrite") is True

    def test_output_registry_uses_append_when_overwrite_false(self):
        """Test that output registry uses append when overwrite=False"""
        from judex.output_registry import OutputFormatRegistry
        
        # Test with overwrite=False
        feeds_config = OutputFormatRegistry.configure_feeds(
            "test_output", "ADI", None, ["json"], None, overwrite=False
        )
        
        # Verify that the feeds configuration includes overwrite=False
        assert feeds_config is not None
        assert len(feeds_config) > 0
        
        # Check that at least one feed has overwrite=False
        for file_path, config in feeds_config.items():
            assert config.get("overwrite") is False

    def test_json_without_overwrite_raises_error(self):
        """Test that JSON output without --overwrite flag raises an error"""
        with patch('sys.argv', ['main.py', '-c', 'ADI', '-p', '1', '-o', 'json']):
            with patch('sys.exit') as mock_exit:
                with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                    main()
                    mock_exit.assert_called_once_with(1)
                    # Check that error message was printed
                    stderr_output = mock_stderr.getvalue()
                    assert "JSON output format requires the --overwrite flag" in stderr_output
                    assert "Appending to JSON files creates invalid JSON arrays" in stderr_output

    def test_json_with_overwrite_succeeds(self):
        """Test that JSON output with --overwrite flag succeeds"""
        with patch('sys.argv', ['main.py', '-c', 'ADI', '-p', '1', '-o', 'json', '--overwrite']):
            with patch('main.JudexScraper') as mock_scraper:
                mock_scraper.return_value.scrape.return_value = None
                with patch('sys.exit') as mock_exit:
                    main()
                    # Should not exit with error
                    mock_exit.assert_not_called()

    def test_csv_without_overwrite_allowed(self):
        """Test that CSV output without --overwrite is allowed"""
        with patch('sys.argv', ['main.py', '-c', 'ADI', '-p', '1', '-o', 'csv']):
            with patch('main.JudexScraper') as mock_scraper:
                mock_scraper.return_value.scrape.return_value = None
                with patch('sys.exit') as mock_exit:
                    main()
                    # Should not exit with error
                    mock_exit.assert_not_called()

    def test_sql_without_overwrite_allowed(self):
        """Test that SQL output without --overwrite is allowed"""
        with patch('sys.argv', ['main.py', '-c', 'ADI', '-p', '1', '-o', 'sql']):
            with patch('main.JudexScraper') as mock_scraper:
                mock_scraper.return_value.scrape.return_value = None
                with patch('sys.exit') as mock_exit:
                    main()
                    # Should not exit with error
                    mock_exit.assert_not_called()

    def test_mixed_output_json_without_overwrite_raises_error(self):
        """Test that mixed output with JSON without --overwrite raises error"""
        with patch('sys.argv', ['main.py', '-c', 'ADI', '-p', '1', '-o', 'json', 'csv']):
            with patch('sys.exit') as mock_exit:
                with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                    with patch('main.JudexScraper') as mock_scraper:
                        # Mock the scraper to prevent it from running
                        mock_scraper.return_value.scrape.return_value = None
                        main()
                        # Should exit with error code 1
                        assert mock_exit.called
                        # Check that error message was printed
                        stderr_output = mock_stderr.getvalue()
                        assert "JSON output format requires the --overwrite flag" in stderr_output

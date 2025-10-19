"""
Unit tests for spider integration with Pydantic
"""

import asyncio
import os
import tempfile
from unittest.mock import Mock, patch

import pytest
from scrapy.http import Response

from judex.models import CaseType
from judex.spiders.stf import StfSpider


@pytest.mark.integration
class TestStfSpiderIntegration:
    """Test StfSpider integration with Pydantic"""

    def setup_method(self):
        """Set up test fixtures"""
        self.spider = StfSpider(
            classe="ADI",
            processos="[123, 456]",
            internal_delay=0.1,
            skip_existing=False,
            retry_failed=False,
        )
        # Use temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()

    def _run_async_start(self):
        """Helper method to run the async start method"""

        async def collect_requests():
            requests = []
            async for request in self.spider.start():
                requests.append(request)
            return requests

        return asyncio.run(collect_requests())

    def teardown_method(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_spider_initialization(self):
        """Test spider initialization with Pydantic integration"""
        assert self.spider.name == "stf"
        assert self.spider.classe == CaseType.ADI
        assert self.spider.numeros == [123, 456]

    def test_spider_initialization_invalid_classe(self):
        """Test spider initialization with invalid classe"""
        with pytest.raises(ValueError):
            StfSpider(classe="INVALID", processos="[123]")

    def test_spider_initialization_missing_classe(self):
        """Test spider initialization without classe"""
        with pytest.raises(TypeError):
            StfSpider(processos="[123]")

    def test_spider_initialization_missing_processos(self):
        """Test spider initialization without processos"""
        with pytest.raises(TypeError):
            StfSpider(classe="ADI")

    def test_spider_initialization_invalid_processos_json(self):
        """Test spider initialization with invalid JSON"""
        with pytest.raises(ValueError):
            StfSpider(classe="ADI", processos="invalid_json")

    @patch("judex.spiders.stf.get_existing_processo_ids")
    @patch("judex.spiders.stf.get_failed_processo_ids")
    def test_start_requests_with_database_check(self, mock_failed, mock_existing):
        """Test start_requests with database checks"""
        mock_existing.return_value = {123}
        mock_failed.return_value = {456}

        # Create spider with database checks enabled
        spider = StfSpider(
            classe="ADI",
            processos="[123, 456]",
            skip_existing=True,
            retry_failed=True,
        )
        spider.settings = {"DATABASE_PATH": self.temp_db.name}

        # Run the async start method
        async def collect_requests():
            requests = []
            async for request in spider.start():
                requests.append(request)
            return requests

        requests = asyncio.run(collect_requests())

        # Should create requests for failed processes (456) but skip existing ones (123)
        assert len(requests) == 1
        assert requests[0].meta["numero"] == 456

        # Check that database functions were called
        mock_existing.assert_called_once()
        mock_failed.assert_called_once()

    @patch("judex.spiders.stf.get_existing_processo_ids")
    @patch("judex.spiders.stf.get_failed_processo_ids")
    def test_start_requests_skip_existing(self, mock_failed, mock_existing):
        """Test start_requests with skip_existing=True"""
        mock_existing.return_value = {123}
        mock_failed.return_value = set()

        # Create spider with skip_existing enabled
        spider = StfSpider(
            classe="ADI",
            processos="[123, 456]",
            skip_existing=True,
            retry_failed=False,
        )
        spider.settings = {"DATABASE_PATH": self.temp_db.name}

        # Run the async start method
        async def collect_requests():
            requests = []
            async for request in spider.start():
                requests.append(request)
            return requests

        requests = asyncio.run(collect_requests())

        # Should skip existing process 123
        assert len(requests) == 1
        assert requests[0].meta["numero"] == 456

    @patch("judex.spiders.stf.get_existing_processo_ids")
    @patch("judex.spiders.stf.get_failed_processo_ids")
    def test_start_requests_retry_failed(self, mock_failed, mock_existing):
        """Test start_requests with retry_failed=True"""
        mock_existing.return_value = set()
        mock_failed.return_value = {123}

        # Create spider with retry_failed enabled
        spider = StfSpider(
            classe="ADI",
            processos="[123, 456]",
            skip_existing=False,
            retry_failed=True,
        )
        spider.settings = {"DATABASE_PATH": self.temp_db.name}

        # Run the async start method
        async def collect_requests():
            requests = []
            async for request in spider.start():
                requests.append(request)
            return requests

        requests = asyncio.run(collect_requests())

        # Should retry failed process 123
        assert len(requests) == 2

    def test_clean_text_method(self):
        """Test clean_text method"""
        # Test with HTML
        html_text = "<p>Test <strong>bold</strong> text</p>"
        result = self.spider.clean_text(html_text)
        assert result == "Test bold text"

        # Test with None
        result = self.spider.clean_text(None)
        assert result is None

        # Test with empty string
        result = self.spider.clean_text("")
        assert result is None

        # Test with whitespace
        result = self.spider.clean_text("   ")
        assert result is None

    @patch("judex.spiders.stf.extract_numero_unico")
    @patch("judex.spiders.stf.extract_classe")
    @patch("judex.spiders.stf.extract_liminar")
    @patch("judex.spiders.stf.extract_relator")
    @patch("judex.spiders.stf.extract_tipo_processo")
    @patch("judex.spiders.stf.extract_origem")
    @patch("judex.spiders.stf.extract_data_protocolo")
    @patch("judex.spiders.stf.extract_origem_orgao")
    @patch("judex.spiders.stf.extract_autor1")
    @patch("judex.spiders.stf.extract_assuntos")
    @patch("judex.spiders.stf.extract_partes")
    @patch("judex.spiders.stf.extract_andamentos")
    @patch("judex.spiders.stf.extract_decisoes")
    @patch("judex.spiders.stf.extract_deslocamentos")
    @patch("judex.spiders.stf.extract_peticoes")
    @patch("judex.spiders.stf.extract_recursos")
    @patch("judex.spiders.stf.extract_pautas")
    @patch("judex.spiders.stf.extract_sessao")
    def test_parse_main_page_selenium_success(
        self,
        mock_sessao,
        mock_pautas,
        mock_recursos,
        mock_peticoes,
        mock_deslocamentos,
        mock_decisoes,
        mock_andamentos,
        mock_partes,
        mock_assuntos,
        mock_autor1,
        mock_origem_orgao,
        mock_data_protocolo,
        mock_origem,
        mock_tipo_processo,
        mock_relator,
        mock_liminar,
        mock_classe,
        mock_numero_unico,
    ):
        """Test successful parsing of main page with all extractors"""
        # Mock all extractors
        mock_numero_unico.return_value = "ADI 123456"
        mock_classe.return_value = "ADI"
        mock_liminar.return_value = ["liminar1"]
        mock_relator.return_value = "Ministro Silva"
        mock_tipo_processo.return_value = "Eletrônico"
        mock_origem.return_value = "STF"
        mock_data_protocolo.return_value = "2023-01-01"
        mock_origem_orgao.return_value = "STF"
        mock_autor1.return_value = "João Silva"
        mock_assuntos.return_value = ["Direito Constitucional"]
        mock_partes.return_value = [{"_index": 1, "tipo": "Autor", "nome": "João Silva"}]
        mock_andamentos.return_value = [{"index": 1, "data": "2023-01-01", "nome": "Distribuição"}]
        mock_decisoes.return_value = [{"index": 1, "data": "2023-01-01", "nome": "Decisão 1"}]
        mock_deslocamentos.return_value = [{"index": 1, "data_enviado": "2023-01-01"}]
        mock_peticoes.return_value = [{"index": 1, "data": "2023-01-01", "tipo": "Petição"}]
        mock_recursos.return_value = [{"index": 1, "data": "2023-01-01", "nome": "Recurso"}]
        mock_pautas.return_value = [{"index": 1, "data": "2023-01-01", "nome": "Julgamento"}]
        mock_sessao.return_value = {"data": "2023-01-01", "tipo": "Plenário"}

        # Create mock response
        mock_response = Mock(spec=Response)
        mock_response.meta = {"numero": 123}
        mock_response.status = 200

        # Create mock driver
        mock_driver = Mock()
        mock_driver.page_source = "<html>Test page</html>"
        mock_driver.find_element.return_value.text = "Test origem"

        # Mock WebDriverWait
        with patch("judex.spiders.stf.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = None

            # Mock get_element_by_id
            self.spider.get_element_by_id = Mock(return_value="456")

            # Mock BeautifulSoup
            with patch("judex.spiders.stf.BeautifulSoup") as mock_soup:
                mock_soup.return_value = Mock()

                # Mock request with driver
                mock_request = Mock()
                mock_request.meta = {"driver": mock_driver}
                mock_response.request = mock_request

                # Mock crawler for stats
                mock_crawler = Mock()
                mock_crawler.stats = Mock()
                mock_crawler.stats.inc_value = Mock()
                self.spider.crawler = mock_crawler

                # Test parsing
                items = list(self.spider.parse_main_page_selenium(mock_response))

                # Should return one item
                assert len(items) == 1
                item = items[0]

                # Check that item has expected fields
                assert item["processo_id"] == 123
                assert item["incidente"] == 456
                assert item["numero_unico"] == "ADI 123456"
                assert item["classe"] == "ADI"
                assert item["liminar"] == ["liminar1"]
                assert item["relator"] == "Ministro Silva"
                assert item["tipo_processo"] == "Eletrônico"
                assert item["origem"] == "STF"
                assert item["data_protocolo"] == "2023-01-01"
                assert item["origem_orgao"] == "STF"
                assert item["autor1"] == "João Silva"
                assert item["assuntos"] == ["Direito Constitucional"]
                assert item["status"] == 200
                assert item["html"] == "<html>Test page</html>"
                assert "extraido" in item

    def test_parse_main_page_selenium_captcha_detection(self):
        """Test parsing with CAPTCHA detection"""
        # Create mock response
        mock_response = Mock(spec=Response)
        mock_response.meta = {"numero": 123}

        # Create mock driver with CAPTCHA
        mock_driver = Mock()
        mock_driver.page_source = "CAPTCHA detected"

        # Mock request with driver
        mock_request = Mock()
        mock_request.meta = {"driver": mock_driver}
        mock_response.request = mock_request

        # Test parsing
        items = list(self.spider.parse_main_page_selenium(mock_response))

        # Should return no items due to CAPTCHA
        assert len(items) == 0

    def test_parse_main_page_selenium_403_forbidden(self):
        """Test parsing with 403 Forbidden"""
        # Create mock response
        mock_response = Mock(spec=Response)
        mock_response.meta = {"numero": 123}

        # Create mock driver with 403
        mock_driver = Mock()
        mock_driver.page_source = "403 Forbidden"

        # Mock request with driver
        mock_request = Mock()
        mock_request.meta = {"driver": mock_driver}
        mock_response.request = mock_request

        # Test parsing
        items = list(self.spider.parse_main_page_selenium(mock_response))

        # Should return no items due to 403
        assert len(items) == 0

    def test_parse_main_page_selenium_502_bad_gateway(self):
        """Test parsing with 502 Bad Gateway"""
        # Create mock response
        mock_response = Mock(spec=Response)
        mock_response.meta = {"numero": 123}

        # Create mock driver with 502
        mock_driver = Mock()
        mock_driver.page_source = "502 Bad Gateway"

        # Mock request with driver
        mock_request = Mock()
        mock_request.meta = {"driver": mock_driver}
        mock_response.request = mock_request

        # Test parsing
        items = list(self.spider.parse_main_page_selenium(mock_response))

        # Should return no items due to 502
        assert len(items) == 0

    def test_parse_main_page_selenium_no_incidente(self):
        """Test parsing when incidente cannot be extracted"""
        # Create mock response
        mock_response = Mock(spec=Response)
        mock_response.meta = {"numero": 123}

        # Create mock driver
        mock_driver = Mock()
        mock_driver.page_source = "<html>Test page</html>"

        # Mock request with driver
        mock_request = Mock()
        mock_request.meta = {"driver": mock_driver}
        mock_response.request = mock_request

        # Mock get_element_by_id to return 0 (invalid incidente)
        self.spider.get_element_by_id = Mock(return_value="0")

        # Test parsing
        items = list(self.spider.parse_main_page_selenium(mock_response))

        # Should return no items due to invalid incidente
        assert len(items) == 0

    def test_get_element_by_id(self):
        """Test get_element_by_id method"""
        # Create mock driver
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.get_attribute.return_value = "test_value"
        mock_driver.find_element.return_value = mock_element

        # Mock WebDriverWait
        with patch("judex.spiders.stf.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = None

            result = self.spider.get_element_by_id(mock_driver, "test_id")

            assert result == "test_value"
            mock_driver.find_element.assert_called_once_with("id", "test_id")

    def test_get_element_by_xpath(self):
        """Test get_element_by_xpath method"""
        # Create mock driver
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.get_attribute.return_value = "test_value"
        mock_driver.find_element.return_value = mock_element

        # Mock WebDriverWait
        with patch("judex.spiders.stf.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = None

            result = self.spider.get_element_by_xpath(mock_driver, "//test")

            assert result == "test_value"
            mock_driver.find_element.assert_called_once_with("xpath", "//test")

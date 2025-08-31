from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
import pytest

from l1nkzip.phishtank import (
    build_phishtank_url,
    delete_old_phishes,
    fetch_phishtank_data,
    get_phish,
    process_phishtank_items,
    update_phishtanks,
)


class TestBuildPhishtankUrl:
    """Test URL building functionality"""

    @patch("l1nkzip.phishtank.settings")
    def test_build_url_anonymous(self, mock_settings):
        """Test URL building with anonymous access"""
        mock_settings.phishtank = "anonymous"
        url = build_phishtank_url()
        assert url == "http://data.phishtank.com/data/online-valid.json"

    @patch("l1nkzip.phishtank.settings")
    def test_build_url_with_api_key(self, mock_settings):
        """Test URL building with API key"""
        mock_settings.phishtank = "test-api-key"
        url = build_phishtank_url()
        assert url == "http://data.phishtank.com/data/test-api-key/online-valid.json"

    @patch("l1nkzip.phishtank.settings")
    def test_build_url_false_setting(self, mock_settings):
        """Test URL building with False setting (disabled)"""
        mock_settings.phishtank = False
        url = build_phishtank_url()
        assert url == "http://data.phishtank.com/data/online-valid.json"

    @patch("l1nkzip.phishtank.settings")
    def test_build_url_none_setting(self, mock_settings):
        """Test URL building with None setting"""
        mock_settings.phishtank = None
        url = build_phishtank_url()
        assert url == "http://data.phishtank.com/data/online-valid.json"


class TestFetchPhishtankData:
    """Test HTTP data fetching functionality"""

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        """Test successful data fetch"""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value=[
                {
                    "phish_id": 1,
                    "url": "http://example.com",
                    "phish_detail_url": "http://detail.com",
                }
            ]
        )
        mock_client.get.return_value = mock_response

        url = "http://test.com/data"
        result = await fetch_phishtank_data(mock_client, url)

        assert result == [
            {
                "phish_id": 1,
                "url": "http://example.com",
                "phish_detail_url": "http://detail.com",
            }
        ]
        mock_client.get.assert_called_once_with(
            url,
            headers={
                "User-Agent": "phishtank/l1nkZip",
                "accept-encoding": "gzip",
            },
            follow_redirects=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_http_error(self):
        """Test HTTP error handling"""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_client.get.return_value = mock_response

        url = "http://test.com/data"

        with pytest.raises(HTTPException) as exc_info:
            await fetch_phishtank_data(mock_client, url)

        exc = exc_info.value
        assert isinstance(exc, HTTPException)
        assert exc.status_code == 404
        assert exc.detail == "Not Found"

    @pytest.mark.asyncio
    async def test_fetch_network_error(self):
        """Test network error handling"""
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Network error")

        url = "http://test.com/data"

        with pytest.raises(Exception, match="Network error"):
            await fetch_phishtank_data(mock_client, url)


class TestProcessPhishtankItems:
    """Test database processing functionality"""

    @patch("l1nkzip.phishtank.PhishTank")
    @patch("l1nkzip.phishtank.utcnow_zone_aware")
    def test_process_new_items(self, mock_utcnow, mock_phishtank_class):
        """Test processing new PhishTank items"""
        mock_utcnow.return_value = "2023-01-01T00:00:00Z"

        # Mock PhishTank.get to return None (new item)
        mock_phishtank_class.get.return_value = None

        items = [
            {
                "phish_id": 1,
                "url": "http://phish.com",
                "phish_detail_url": "http://detail.com",
            }
        ]

        process_phishtank_items(items)

        # Verify PhishTank was created
        mock_phishtank_class.assert_called_once_with(id=1, url="http://phish.com", phish_detail_url="http://detail.com")

    @patch("l1nkzip.phishtank.PhishTank")
    @patch("l1nkzip.phishtank.utcnow_zone_aware")
    def test_process_existing_items(self, mock_utcnow, mock_phishtank_class):
        """Test processing existing PhishTank items"""
        mock_now = MagicMock()
        mock_utcnow.return_value = mock_now

        # Mock existing PhishTank entry
        mock_existing = MagicMock()
        mock_phishtank_class.get.return_value = mock_existing

        items = [
            {
                "phish_id": 1,
                "url": "http://phish.com",
                "phish_detail_url": "http://detail.com",
            }
        ]

        process_phishtank_items(items)

        # Verify updated_at was set
        assert mock_existing.updated_at == mock_now
        # Verify no new PhishTank was created
        mock_phishtank_class.assert_not_called()

    @patch("l1nkzip.phishtank.PhishTank")
    def test_process_empty_items(self, mock_phishtank_class):
        """Test processing empty items list"""
        items = []
        process_phishtank_items(items)

        # Verify no database operations
        mock_phishtank_class.get.assert_not_called()
        mock_phishtank_class.assert_not_called()

    @patch("l1nkzip.phishtank.PhishTank")
    def test_process_malformed_items(self, mock_phishtank_class):
        """Test processing malformed items (missing keys)"""
        mock_phishtank_class.get.return_value = None

        items = [
            {"phish_id": 1}  # Missing url and phish_detail_url
        ]

        with pytest.raises(KeyError):
            process_phishtank_items(items)


class TestUpdatePhishtanks:
    """Test the main update function"""

    @pytest.mark.asyncio
    @patch("l1nkzip.phishtank.build_phishtank_url")
    @patch("l1nkzip.phishtank.fetch_phishtank_data")
    @patch("l1nkzip.phishtank.process_phishtank_items")
    async def test_update_with_provided_client(self, mock_process, mock_fetch, mock_build_url):
        """Test update with provided HTTP client"""
        mock_build_url.return_value = "http://test.com/data"
        mock_fetch.return_value = [{"phish_id": 1, "url": "http://test.com"}]

        mock_client = AsyncMock()
        await update_phishtanks(client=mock_client)

        mock_build_url.assert_called_once()
        mock_fetch.assert_called_once_with(mock_client, "http://test.com/data")
        mock_process.assert_called_once_with([{"phish_id": 1, "url": "http://test.com"}])

    @pytest.mark.asyncio
    @patch("l1nkzip.phishtank.build_phishtank_url")
    @patch("l1nkzip.phishtank.fetch_phishtank_data")
    @patch("l1nkzip.phishtank.process_phishtank_items")
    @patch("l1nkzip.phishtank.httpx.AsyncClient")
    async def test_update_without_client(self, mock_async_client_class, mock_process, mock_fetch, mock_build_url):
        """Test update without provided client (creates new one)"""
        mock_build_url.return_value = "http://test.com/data"
        mock_fetch.return_value = [{"phish_id": 1, "url": "http://test.com"}]

        mock_client = AsyncMock()
        mock_async_client_class.return_value.__aenter__.return_value = mock_client

        await update_phishtanks()

        mock_build_url.assert_called_once()
        mock_fetch.assert_called_once_with(mock_client, "http://test.com/data")
        mock_process.assert_called_once_with([{"phish_id": 1, "url": "http://test.com"}])


class TestGetPhish:
    """Test phishing URL lookup functionality"""

    @patch("l1nkzip.phishtank.PhishTank")
    def test_get_phish_found(self, mock_phishtank_class):
        """Test finding a phishing URL"""
        mock_phish = MagicMock()
        mock_phishtank_class.get.return_value = mock_phish

        url_info = MagicMock()
        url_info.url = "http://phish.com"

        result = get_phish(url_info)

        assert result == mock_phish
        mock_phishtank_class.get.assert_called_once_with(url="http://phish.com")

    @patch("l1nkzip.phishtank.PhishTank")
    def test_get_phish_not_found(self, mock_phishtank_class):
        """Test when phishing URL is not found"""
        mock_phishtank_class.get.return_value = None

        url_info = MagicMock()
        url_info.url = "http://safe.com"

        result = get_phish(url_info)

        assert result is None
        mock_phishtank_class.get.assert_called_once_with(url="http://safe.com")


class TestDeleteOldPhishes:
    """Test old phishing entries deletion functionality"""

    @patch("l1nkzip.phishtank.PhishTank")
    @patch("l1nkzip.phishtank.utcnow_zone_aware")
    def test_delete_old_phishes(self, mock_utcnow, mock_phishtank_class):
        """Test deleting old phishing entries"""
        mock_now = MagicMock()
        mock_utcnow.return_value = mock_now

        # Mock select query
        mock_select = MagicMock()
        mock_phishtank_class.select.return_value = mock_select
        mock_select.count.return_value = 5

        result = delete_old_phishes(days=30)

        assert result == 5
        mock_phishtank_class.select.assert_called_once()
        mock_select.delete.assert_called_once_with(bulk=True)

    @patch("l1nkzip.phishtank.PhishTank")
    @patch("l1nkzip.phishtank.utcnow_zone_aware")
    def test_delete_no_old_phishes(self, mock_utcnow, mock_phishtank_class):
        """Test when no old entries to delete"""
        mock_now = MagicMock()
        mock_utcnow.return_value = mock_now

        # Mock select query with no results
        mock_select = MagicMock()
        mock_phishtank_class.select.return_value = mock_select
        mock_select.count.return_value = 0

        result = delete_old_phishes(days=30)

        assert result == 0
        mock_select.delete.assert_called_once_with(bulk=True)


class TestIntegration:
    """Integration tests for full workflows"""

    @pytest.mark.asyncio
    @patch("l1nkzip.phishtank.build_phishtank_url")
    @patch("l1nkzip.phishtank.fetch_phishtank_data")
    @patch("l1nkzip.phishtank.process_phishtank_items")
    async def test_full_update_workflow(self, mock_process, mock_fetch, mock_build_url):
        """Test the complete update workflow"""
        mock_build_url.return_value = "http://data.phishtank.com/data/online-valid.json"
        mock_fetch.return_value = [
            {
                "phish_id": 12345,
                "url": "http://malicious-site.com",
                "phish_detail_url": "http://phishtank.com/phish_detail.php?phish_id=12345",
            }
        ]

        mock_client = AsyncMock()
        await update_phishtanks(client=mock_client)

        # Verify all functions were called in sequence
        mock_build_url.assert_called_once()
        mock_fetch.assert_called_once()
        mock_process.assert_called_once()

        # Verify the data flow
        call_args = mock_fetch.call_args
        assert call_args[0][0] == mock_client
        assert call_args[0][1] == "http://data.phishtank.com/data/online-valid.json"

        process_args = mock_process.call_args[0][0]
        assert len(process_args) == 1
        assert process_args[0]["phish_id"] == 12345

"""
Unit tests for database models and query functions in l1nkzip.models.
"""

from unittest.mock import MagicMock, patch

from pony.orm import db_session
from pydantic import HttpUrl
import pytest

from l1nkzip.config import ponyorm_settings
from l1nkzip.models import Link, LinkInfo, db, get_visits, insert_link, set_visit


@pytest.fixture(autouse=True)
def setup_db(test_settings):
    """Ensure database is initialized for unit tests."""
    if not db.provider:
        db.bind(**ponyorm_settings[test_settings.db_type])
        db.generate_mapping(create_tables=True)
    yield
    # Clean up table entries after each test
    with db_session:
        Link.select().delete(bulk=True)


class TestGetVisits:
    """Test cases for the get_visits function."""

    def test_get_visits_empty_database(self):
        """Test get_visits returns an empty list when no links exist."""
        results = get_visits()
        assert results == []
        assert isinstance(results, list)

    def test_get_visits_with_data(self):
        """Test get_visits returns formatted LinkInfo list when data exists."""
        # Insert test links
        with db_session:
            link1 = insert_link("https://example.com")
            insert_link("https://python.org")

            # Update visits for link1
            set_visit(link1.link)
            set_visit(link1.link)

        results = get_visits()

        assert len(results) == 2
        assert all(isinstance(item, LinkInfo) for item in results)

        # Find link1 result
        link1_info = next((r for r in results if str(r.url) in ("https://example.com", "https://example.com/")), None)
        assert link1_info is not None, "Expected link for https://example.com was not found in get_visits output"
        assert link1_info.visits == 2
        assert isinstance(link1_info.full_link, HttpUrl)
        assert isinstance(link1_info.url, HttpUrl)

        # Find link2 result
        link2_info = next((r for r in results if str(r.url) in ("https://python.org", "https://python.org/")), None)
        assert link2_info is not None, "Expected link for https://python.org was not found in get_visits output"
        assert link2_info.visits == 0

    def test_get_visits_limit_parameter(self):
        """Test get_visits respects the limit parameter."""
        urls = [f"https://example{i}.com" for i in range(5)]
        with db_session:
            for url in urls:
                insert_link(url)

        # Retrieve with limit=2
        results_limited = get_visits(limit=2)
        assert len(results_limited) == 2

        # Retrieve with limit=10
        results_all = get_visits(limit=10)
        assert len(results_all) == 5

    def test_get_visits_default_limit(self):
        """Test get_visits uses default limit of 100 when called without explicit limit."""
        urls = [f"https://example{i}.com" for i in range(105)]
        with db_session:
            for url in urls:
                insert_link(url)

        results = get_visits()
        assert len(results) == 100

    def test_get_visits_with_mocked_select(self):
        """Test get_visits with mocked Link.select query for isolated unit test."""
        mock_link = MagicMock()
        mock_link.link = "testlink"
        mock_link.full_link = "http://localhost:8000/testlink"
        mock_link.url = "https://example.org"
        mock_link.visits = 42

        # Mock Link.select()[:limit] returning [mock_link]
        mock_query = MagicMock()
        mock_query.__getitem__.return_value = [mock_link]

        with patch.object(Link, "select", return_value=mock_query):
            results = get_visits(limit=10)

        assert len(results) == 1
        assert isinstance(results[0], LinkInfo)
        assert results[0].link == "testlink"
        assert str(results[0].full_link) in ("http://localhost:8000/testlink", "http://localhost:8000/testlink/")
        assert str(results[0].url) in ("https://example.org", "https://example.org/")
        assert results[0].visits == 42
        mock_query.__getitem__.assert_called_once_with(slice(None, 10, None))

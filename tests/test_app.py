"""Unit tests for app.py — covers fetch_metar() and the index route."""

import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from app import app, fetch_metar

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_urlopen(content: bytes) -> MagicMock:
    """Return a MagicMock that behaves as urllib.request.urlopen context manager."""
    mock = MagicMock()
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = False
    mock.read.return_value = content
    return mock


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# fetch_metar — success paths
# ---------------------------------------------------------------------------


class TestFetchMetarSuccess:
    def test_returns_metar_string_on_valid_response(self):
        metar = "KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        with patch(
            "urllib.request.urlopen", return_value=_mock_urlopen(metar.encode())
        ):
            result, error = fetch_metar("KJFK")
        assert result == metar
        assert error is None

    def test_picks_first_valid_metar_line_from_multiline_response(self):
        metar = "KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        body = f"some header line\n{metar}\nsome footer"
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(body.encode())):
            result, error = fetch_metar("KJFK")
        assert result == metar
        assert error is None

    def test_airport_code_is_uppercased_in_request(self):
        metar = "KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        with patch(
            "urllib.request.urlopen", return_value=_mock_urlopen(metar.encode())
        ) as mock_open:
            fetch_metar("kjfk")
        url_used = mock_open.call_args[0][0].full_url
        assert "KJFK" in url_used


# ---------------------------------------------------------------------------
# fetch_metar — error paths
# ---------------------------------------------------------------------------


class TestFetchMetarErrors:
    def test_returns_error_on_http_404(self):
        err = urllib.error.HTTPError(
            url=None, code=404, msg="Not Found", hdrs=None, fp=None
        )
        with patch("urllib.request.urlopen", side_effect=err):
            result, error = fetch_metar("XXXX")
        assert result is None
        assert "HTTP 404" in error

    def test_returns_error_on_network_failure(self):
        with patch(
            "urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")
        ):
            result, error = fetch_metar("KJFK")
        assert result is None
        assert "internet connection" in error.lower()

    def test_returns_error_on_empty_response(self):
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(b"")):
            result, error = fetch_metar("KJFK")
        assert result is None
        assert error is not None


# ---------------------------------------------------------------------------
# index route — GET
# ---------------------------------------------------------------------------


class TestIndexGet:
    def test_returns_200(self, client):
        assert client.get("/").status_code == 200

    def test_renders_search_form(self, client):
        data = client.get("/").data
        assert b"<form" in data
        assert b'name="airport"' in data


# ---------------------------------------------------------------------------
# index route — POST form validation
# ---------------------------------------------------------------------------


class TestIndexPostValidation:
    def test_empty_airport_shows_error(self, client):
        data = client.post("/", data={"airport": ""}).data
        assert b"Please enter an airport code" in data

    def test_too_long_code_shows_error(self, client):
        data = client.post("/", data={"airport": "ABCDE"}).data
        assert b"ICAO airport code" in data

    def test_non_alphanumeric_code_shows_error(self, client):
        data = client.post("/", data={"airport": "K!FK"}).data
        assert b"ICAO airport code" in data


# ---------------------------------------------------------------------------
# index route — POST with mocked fetch
# ---------------------------------------------------------------------------


class TestIndexPostWeather:
    def test_valid_airport_returns_weather_card(self, client):
        metar = "KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        with patch("app.fetch_metar", return_value=(metar, None)):
            response = client.post("/", data={"airport": "KJFK"})
        assert response.status_code == 200
        assert b"KJFK" in response.data

    def test_fetch_error_displays_error_message(self, client):
        with patch("app.fetch_metar", return_value=(None, "Airport not found")):
            data = client.post("/", data={"airport": "ZZZZ"}).data
        assert b"Airport not found" in data

    def test_unparseable_metar_shows_decode_error(self, client):
        with patch("app.fetch_metar", return_value=("GARBAGE", None)):
            with patch("app.parse_metar", return_value=None):
                data = client.post("/", data={"airport": "KJFK"}).data
        assert b"Could not decode" in data

    def test_airport_code_uppercased_in_response(self, client):
        metar = "KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        with patch("app.fetch_metar", return_value=(metar, None)):
            data = client.post("/", data={"airport": "kjfk"}).data
        assert b"KJFK" in data

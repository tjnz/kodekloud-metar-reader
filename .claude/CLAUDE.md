# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt   # needed for tests

# Run the app (http://localhost:5000)
python app.py

# Run all tests
pytest tests/ -v

# Run a single test file / test
pytest tests/test_metar_parser.py -v
pytest tests/test_app.py::TestFetchMetarSuccess::test_returns_metar_string_on_valid_response -v

# Lint
flake8 app.py metar_parser.py tests/

# Format (rewrites files in place; use --check to preview without writing)
black app.py metar_parser.py tests/
```

Flake8 is configured via `.flake8` (max line length 88, `E203`/`W503` ignored since Black's
formatting conflicts with those checks). Black uses its default settings (line length 88).
Run Black before Flake8 — most line-length/formatting issues Flake8 would flag are fixed by
Black automatically.

## Architecture

Two-module Flask app with a strict separation between HTTP/IO and parsing:

- `app.py` — Flask route (`/`) and `fetch_metar()`. `fetch_metar` calls the live Aviation Weather Center API (`aviationweather.gov`) via `urllib.request` and returns a `(raw_metar, error_message)` tuple where exactly one value is `None`. The route validates the submitted airport code with a regex before fetching, then hands the raw METAR string to the parser.
- `metar_parser.py` — `parse_metar(raw)` decodes a raw METAR string into a dict (wind, visibility, weather, sky, temperature, dewpoint, humidity, altimeter, emoji, summary, details) with no external parsing libraries or network access. It is pure and fully unit-testable in isolation from Flask.
- `templates/index.html` — single-page UI rendered by the `/` route; consumes the dict produced by `parse_metar`.

METAR decoding in `metar_parser.py` walks the raw string token-by-token with an `idx` cursor through fixed METAR field order (station → time → wind → visibility → RVR → weather phenomena → sky conditions → temp/dewpoint → altimeter), advancing `idx` only when a token matches the expected pattern for that field. When adding support for a new METAR field or token format, follow this same "match at current idx, advance, else fall through" pattern rather than reordering existing checks.

Tests mirror this split: `tests/test_metar_parser.py` tests the decoder directly with raw METAR strings (no mocking needed), `tests/test_app.py` mocks `urllib.request.urlopen` and Flask's test client to test `fetch_metar()` and the route.

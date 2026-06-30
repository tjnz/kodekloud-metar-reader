"""Flask web app that fetches and displays live METAR aviation weather reports."""

import re
import urllib.request
import urllib.error
from flask import Flask, render_template, request
from metar_parser import parse_metar

app = Flask(__name__)

METAR_URL = "https://aviationweather.gov/api/data/metar?ids={}&format=raw"


def fetch_metar(airport_code):
    """Fetch the raw METAR string for *airport_code* from aviationweather.gov.

    Returns a ``(raw_metar, error_message)`` tuple.  Exactly one of the two
    values will be ``None``: on success ``error_message`` is ``None``; on
    failure ``raw_metar`` is ``None`` and ``error_message`` describes the problem.
    """
    url = METAR_URL.format(urllib.request.quote(airport_code.upper()))
    req = urllib.request.Request(url, headers={"User-Agent": "METAR-Reader/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode("utf-8").strip()
    except urllib.error.HTTPError as e:
        return None, f"Airport lookup failed (HTTP {e.code}). Check the airport code and try again."
    except urllib.error.URLError:
        return None, "Could not reach the weather service. Check your internet connection."

    if not text:
        return None, f'No METAR data found for "{airport_code.upper()}". Make sure you\'re using a valid ICAO airport code (e.g. KSLC, EGLL, KJFK).'

    # The API may return multiple lines; take the first METAR line
    for line in text.splitlines():
        line = line.strip()
        # A valid METAR starts with the station ID or METAR keyword
        if re.match(r'^(METAR\s+)?[A-Z]{4}\s+\d{6}Z', line):
            return line, None

    # Fallback: return first non-empty line and try to parse it
    first = next((l.strip() for l in text.splitlines() if l.strip()), None)
    if first:
        return first, None

    return None, "Received an unrecognisable response from the weather service."


@app.route("/", methods=["GET", "POST"])
def index():
    """Render the search form (GET) and display decoded weather results (POST)."""
    weather = None
    error = None
    airport_code = ""

    if request.method == "POST":
        airport_code = request.form.get("airport", "").strip()
        if not airport_code:
            error = "Please enter an airport code."
        elif not re.match(r'^[A-Za-z0-9]{3,4}$', airport_code):
            error = "Enter a 3- or 4-letter ICAO airport code (e.g. KSLC, KJFK, EGLL)."
        else:
            raw, fetch_error = fetch_metar(airport_code)
            if fetch_error:
                error = fetch_error
            else:
                weather = parse_metar(raw)
                if weather is None:
                    error = "Could not decode the METAR data. Please try a different airport."

    return render_template("index.html", weather=weather, error=error, airport_code=airport_code.upper())


if __name__ == "__main__":
    app.run(debug=True)

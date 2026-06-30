# METAR Reader

A lightweight Flask web app that fetches live aviation weather reports (METARs) and displays them in plain English — no aviation knowledge required.

Enter a 4-letter ICAO airport code and get an instant weather summary with temperature, wind speed and direction, visibility, sky conditions, humidity, and barometric pressure.

![Python](https://img.shields.io/badge/python-3.9%2B-blue) ![Flask](https://img.shields.io/badge/flask-3.1-green)

## What is a METAR?

A METAR (Meteorological Aerodrome Report) is a standardised weather observation used by pilots worldwide. They look like this:

```
KJFK 291551Z 22015KT 10SM FEW055 BKN250 24/14 A2991
```

METAR Reader decodes that into human-readable weather data automatically.

## Features

- Accepts any ICAO airport code — US (`KJFK`, `KSLC`) and international (`EGLL`, `YSSY`, `RJTT`)
- Decodes wind, visibility, weather phenomena, sky layers, temperature, dew point, humidity, and pressure
- Displays a plain-English summary with a matching weather emoji
- Shows the raw METAR string for reference
- No external parsing libraries — the decoder is implemented from scratch in `metar_parser.py`

## Requirements

- Python 3.9 or later
- Internet connection (live data is fetched from [aviationweather.gov](https://aviationweather.gov))

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/tjnz/kodekloud-metar-reader.git
cd kodekloud-metar-reader

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the app
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Usage

1. Type a 4-letter ICAO airport code into the search box (e.g. `KJFK` for New York JFK, `EGLL` for London Heathrow)
2. Click **Get Weather**
3. View the decoded report — temperature, wind, sky conditions, and more

Not sure of the code? ICAO codes can be looked up at [ourairports.com](https://ourairports.com).

## Project structure

```
app.py              # Flask routes — fetches METAR and renders the page
metar_parser.py     # METAR decoder (no external libraries)
templates/
  index.html        # Single-page UI with search form and results card
requirements.txt    # Pinned Python dependencies
```

## Data source

Live METAR data is provided by the [Aviation Weather Center API](https://aviationweather.gov/api/data/metar) (NOAA / US National Weather Service), a free public service.

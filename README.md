# METAR Reader

A Flask web app that fetches live METAR aviation weather reports and displays them in plain English.

Enter a 4-letter ICAO airport code (e.g. `KJFK`, `EGLL`, `YSSY`) and get a human-readable weather summary with temperature, wind, visibility, sky conditions, and more.

## Running locally

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open [http://localhost:5000](http://localhost:5000).

## What it parses

- **Wind** — speed in mph/kt, plain-English direction, gusts
- **Visibility** — statute miles (US) and metres (international), CAVOK
- **Weather** — rain, snow, fog, thunderstorms, haze, ice pellets, with intensity
- **Sky** — Clear/Few/Scattered/Broken/Overcast with heights in feet; CB/TCU flags
- **Temperature** — °F and °C, dew point, relative humidity (Magnus formula)
- **Pressure** — inHg (A-format) and hPa (Q-format)

Works with US airports (`KXXX`) and international ICAO codes.

## Data source

Live METAR data is fetched from the [Aviation Weather Center API](https://aviationweather.gov/api/data/metar).

import re

def celsius_to_fahrenheit(c):
    return round(c * 9 / 5 + 32)

def knots_to_mph(knots):
    return round(knots * 1.15078)

def degrees_to_cardinal(degrees):
    dirs = [
        'north', 'north-northeast', 'northeast', 'east-northeast',
        'east', 'east-southeast', 'southeast', 'south-southeast',
        'south', 'south-southwest', 'southwest', 'west-southwest',
        'west', 'west-northwest', 'northwest', 'north-northwest',
    ]
    return dirs[round(degrees / 22.5) % 16]

WEATHER_DESCRIPTORS = {
    'MI': 'shallow', 'PR': 'partial', 'BC': 'patchy',
    'DR': 'low drifting', 'BL': 'blowing', 'SH': 'showers',
    'TS': 'thunderstorm', 'FZ': 'freezing',
}

WEATHER_PHENOMENA = {
    'DZ': 'drizzle', 'RA': 'rain', 'SN': 'snow', 'SG': 'snow grains',
    'IC': 'ice crystals', 'PL': 'ice pellets', 'GR': 'hail',
    'GS': 'small hail', 'UP': 'unknown precipitation',
    'BR': 'mist', 'FG': 'fog', 'FU': 'smoke', 'VA': 'volcanic ash',
    'DU': 'dust', 'SA': 'sand', 'HZ': 'haze', 'PY': 'spray',
    'PO': 'dust whirls', 'SQ': 'squalls', 'FC': 'tornado/waterspout',
    'SS': 'sandstorm', 'DS': 'dust storm',
}

SKY_CONDITIONS = {
    'CLR':   ('Clear',         'clear skies'),
    'SKC':   ('Clear',         'clear skies'),
    'NSC':   ('Clear',         'no significant clouds'),
    'CAVOK': ('Clear',         'ceiling and visibility OK'),
    'FEW':   ('Partly Cloudy', 'a few clouds'),
    'SCT':   ('Partly Cloudy', 'scattered clouds'),
    'BKN':   ('Mostly Cloudy', 'broken cloud cover'),
    'OVC':   ('Overcast',      'overcast skies'),
    'VV':    ('Obscured',      'sky obscured'),
}

SKY_ORDER = ['CLR', 'SKC', 'NSC', 'CAVOK', 'FEW', 'SCT', 'BKN', 'OVC', 'VV']


def _get_emoji(weather_list, sky_code):
    wx = ' '.join(weather_list).upper()
    if 'TS' in wx or 'thunderstorm' in wx:
        return '⛈️'
    if 'SN' in wx or 'snow' in wx:
        return '❄️'
    if 'FG' in wx or 'fog' in wx:
        return '🌫️'
    if 'RA' in wx or 'DZ' in wx or 'rain' in wx or 'drizzle' in wx:
        return '🌧️'
    if 'HZ' in wx or 'haze' in wx:
        return '🌫️'
    if sky_code in ('OVC', 'BKN'):
        return '☁️'
    if sky_code in ('FEW', 'SCT'):
        return '⛅'
    return '☀️'


def _parse_weather_token(token):
    """Parse a single weather phenomenon token like -TSRA or +SN."""
    m = re.match(
        r'^([+-]|VC)?(MI|PR|BC|DR|BL|SH|TS|FZ)?(DZ|RA|SN|SG|IC|PL|GR|GS|UP|BR|FG|FU|VA|DU|SA|HZ|PY|PO|SQ|FC|SS|DS)+$',
        token,
    )
    if not m:
        return None

    intensity_code = m.group(1)
    descriptor_code = m.group(2)

    # Strip intensity and descriptor to get phenomena string
    phenomena_str = token
    if intensity_code:
        phenomena_str = phenomena_str[len(intensity_code):]
    if descriptor_code:
        phenomena_str = phenomena_str[len(descriptor_code):]

    parts = []
    if intensity_code == '-':
        parts.append('light')
    elif intensity_code == '+':
        parts.append('heavy')
    elif intensity_code == 'VC':
        parts.append('nearby')

    # Parse phenomenon codes greedily (longest first)
    remaining = phenomena_str
    phenomena_parts = []
    while remaining:
        matched = False
        for code in sorted(WEATHER_PHENOMENA, key=len, reverse=True):
            if remaining.startswith(code):
                phenomena_parts.append(WEATHER_PHENOMENA[code])
                remaining = remaining[len(code):]
                matched = True
                break
        if not matched:
            remaining = remaining[1:]

    if descriptor_code == 'TS':
        base = ' '.join(parts + ['thunderstorms'])
        if phenomena_parts:
            base += ' with ' + ' and '.join(phenomena_parts)
        return base
    elif descriptor_code == 'SH':
        base = ' '.join(parts + phenomena_parts + ['showers'])
        return base
    elif descriptor_code:
        desc_text = WEATHER_DESCRIPTORS.get(descriptor_code, descriptor_code)
        parts.append(desc_text)

    parts.extend(phenomena_parts)
    return ' '.join(parts).strip() or None


def parse_metar(raw):
    """Return a dict of decoded weather data, or None if parsing fails."""
    tokens = raw.strip().split()
    if not tokens:
        return None

    result = {
        'raw': raw.strip(),
        'station': None,
        'time_utc': None,
        'auto': False,
        'wind': None,
        'visibility': None,
        'weather': [],
        'sky': [],
        'sky_condition': None,
        'temperature_c': None,
        'temperature_f': None,
        'dewpoint_c': None,
        'dewpoint_f': None,
        'humidity': None,
        'altimeter': None,
        'emoji': '☀️',
        'summary': '',
        'details': [],
    }

    idx = 0

    # Optional type prefix
    if tokens[idx] in ('METAR', 'SPECI'):
        idx += 1

    # Station ID
    if idx < len(tokens):
        result['station'] = tokens[idx]
        idx += 1

    # Date/time DDHHMMz
    if idx < len(tokens) and re.match(r'^\d{6}Z$', tokens[idx]):
        dt = tokens[idx]
        result['time_utc'] = f"{dt[2:4]}:{dt[4:6]} UTC (day {int(dt[0:2])})"
        idx += 1

    # AUTO / COR
    if idx < len(tokens) and tokens[idx] in ('AUTO', 'COR'):
        result['auto'] = tokens[idx] == 'AUTO'
        idx += 1

    # Wind: dddssKT | dddssGssKT | VRBssKT
    if idx < len(tokens):
        wm = re.match(r'^(\d{3}|VRB)(\d{2,3})(G(\d{2,3}))?(KT|MPS|KMH)$', tokens[idx])
        if wm:
            raw_dir, raw_spd, _, raw_gust, unit = wm.group(1), wm.group(2), wm.group(3), wm.group(4), wm.group(5)
            spd = int(raw_spd)
            gust = int(raw_gust) if raw_gust else None
            if unit == 'MPS':
                spd = round(spd * 1.94384)
                gust = round(gust * 1.94384) if gust else None
            elif unit == 'KMH':
                spd = round(spd / 1.852)
                gust = round(gust / 1.852) if gust else None

            if raw_dir == 'VRB':
                direction = 'variable'
                degrees = None
            else:
                degrees = int(raw_dir)
                direction = degrees_to_cardinal(degrees)

            result['wind'] = {
                'direction': direction,
                'degrees': degrees,
                'speed_kt': spd,
                'speed_mph': knots_to_mph(spd),
                'gust_kt': gust,
                'gust_mph': knots_to_mph(gust) if gust else None,
            }

            if spd == 0:
                wind_txt = 'Calm'
            elif gust:
                wind_txt = (
                    f"{knots_to_mph(spd)}–{knots_to_mph(gust)} mph ({spd}–{gust} kt) "
                    f"from the {direction}"
                )
            else:
                wind_txt = f"{knots_to_mph(spd)} mph ({spd} kt) from the {direction}"

            result['details'].append({'icon': '💨', 'label': 'Wind', 'value': wind_txt})
            idx += 1

        # Wind variability e.g. 180V250
        if idx < len(tokens) and re.match(r'^\d{3}V\d{3}$', tokens[idx]):
            idx += 1

    # CAVOK replaces visibility + weather + sky group
    if idx < len(tokens) and tokens[idx] == 'CAVOK':
        result['visibility'] = 10.0
        result['sky_condition'] = 'CAVOK'
        result['details'].append({'icon': '👁️', 'label': 'Visibility', 'value': '10+ km (CAVOK)'})
        result['details'].append({'icon': '🌤️', 'label': 'Sky', 'value': 'Ceiling and visibility OK'})
        idx += 1

    # Visibility
    elif idx < len(tokens):
        token = tokens[idx]
        # whole number SM: 10SM
        m = re.match(r'^(\d+)SM$', token)
        # fraction only SM: 1/2SM
        mf = re.match(r'^(\d+)/(\d+)SM$', token)
        # metric: 4-digit meters e.g. 9999 or 0800 (optionally followed by NDV)
        mm = re.match(r'^(\d{4})(NDV)?$', token)
        if m:
            vis = float(m.group(1))
            vis_txt = f"{int(vis)}+ miles" if vis >= 10 else f"{int(vis)} miles"
            result['visibility'] = vis
            result['details'].append({'icon': '👁️', 'label': 'Visibility', 'value': vis_txt})
            idx += 1
        elif mf:
            vis = int(mf.group(1)) / int(mf.group(2))
            vis_txt = f"{mf.group(1)}/{mf.group(2)} mile"
            result['visibility'] = vis
            result['details'].append({'icon': '👁️', 'label': 'Visibility', 'value': vis_txt})
            idx += 1
        elif mm:
            meters = int(mm.group(1))
            if meters >= 9999:
                vis_txt = "10+ km"
            else:
                vis_txt = f"{meters} m"
            result['visibility'] = meters
            result['details'].append({'icon': '👁️', 'label': 'Visibility', 'value': vis_txt})
            idx += 1
        elif idx + 1 < len(tokens):
            # whole + fraction: "1 1/2SM"
            combined = token + ' ' + tokens[idx + 1]
            mc = re.match(r'^(\d+) (\d+)/(\d+)SM$', combined)
            if mc:
                vis = int(mc.group(1)) + int(mc.group(2)) / int(mc.group(3))
                vis_txt = f"{mc.group(1)} {mc.group(2)}/{mc.group(3)} miles"
                result['visibility'] = vis
                result['details'].append({'icon': '👁️', 'label': 'Visibility', 'value': vis_txt})
                idx += 2

    # RVR — skip
    while idx < len(tokens) and re.match(r'^R\d{2}[LRC]?/', tokens[idx]):
        idx += 1

    # Weather phenomena
    wx_list = []
    while idx < len(tokens):
        decoded = _parse_weather_token(tokens[idx])
        if decoded is not None:
            wx_list.append(decoded)
            idx += 1
        else:
            break

    if wx_list:
        result['weather'] = wx_list
        result['details'].append({
            'icon': '🌦️', 'label': 'Weather',
            'value': ', '.join(wx_list).capitalize(),
        })

    # Sky conditions
    sky_layers = []
    dominant = None
    while idx < len(tokens):
        token = tokens[idx]
        sm = re.match(r'^(CLR|SKC|NSC|CAVOK|FEW|SCT|BKN|OVC|VV)(\d{3})?(CB|TCU)?$', token)
        if sm:
            cover, height_code, cloud_type = sm.group(1), sm.group(2), sm.group(3)
            height_ft = int(height_code) * 100 if height_code else None
            sky_layers.append({'cover': cover, 'height_ft': height_ft, 'type': cloud_type})

            if dominant is None or SKY_ORDER.index(cover) > SKY_ORDER.index(dominant):
                dominant = cover
            idx += 1
        else:
            break

    if sky_layers:
        result['sky'] = sky_layers
        result['sky_condition'] = dominant

        sky_parts = []
        for layer in sky_layers:
            label, _ = SKY_CONDITIONS.get(layer['cover'], (layer['cover'], ''))
            if layer['height_ft']:
                txt = f"{label} at {layer['height_ft']:,} ft"
                if layer['type']:
                    txt += f" ({layer['type']})"
            else:
                txt = label
            sky_parts.append(txt)

        result['details'].append({'icon': '🌤️', 'label': 'Sky', 'value': '; '.join(sky_parts)})

    # Temperature / Dew point
    if idx < len(tokens):
        tm = re.match(r'^(M?\d+)/(M?\d+)$', tokens[idx])
        if tm:
            temp_c = int(tm.group(1).replace('M', '-'))
            dew_c  = int(tm.group(2).replace('M', '-'))
            result['temperature_c'] = temp_c
            result['temperature_f'] = celsius_to_fahrenheit(temp_c)
            result['dewpoint_c']    = dew_c
            result['dewpoint_f']    = celsius_to_fahrenheit(dew_c)
            import math
            es_t = math.exp(17.625 * temp_c / (243.04 + temp_c))
            es_d = math.exp(17.625 * dew_c  / (243.04 + dew_c))
            result['humidity'] = min(100, max(0, round(100 * es_d / es_t)))
            result['details'].append({
                'icon': '🌡️', 'label': 'Temperature',
                'value': f"{result['temperature_f']}°F  ({temp_c}°C)",
            })
            result['details'].append({
                'icon': '💧', 'label': 'Dew Point',
                'value': f"{result['dewpoint_f']}°F  ({dew_c}°C)",
            })
            result['details'].append({
                'icon': '💧', 'label': 'Humidity',
                'value': f"~{result['humidity']}%",
            })
            idx += 1

    # Altimeter
    if idx < len(tokens):
        am = re.match(r'^A(\d{4})$', tokens[idx])
        qm = re.match(r'^Q(\d{4})$', tokens[idx])
        if am:
            alt = int(am.group(1)) / 100
            result['altimeter'] = alt
            result['details'].append({'icon': '📊', 'label': 'Pressure', 'value': f"{alt:.2f} inHg"})
            idx += 1
        elif qm:
            hpa = int(qm.group(1))
            alt = round(hpa * 0.02953, 2)
            result['altimeter'] = alt
            result['details'].append({'icon': '📊', 'label': 'Pressure', 'value': f"{hpa} hPa  ({alt:.2f} inHg)"})
            idx += 1

    result['emoji'] = _get_emoji(result['weather'], result['sky_condition'] or 'CLR')
    result['summary'] = _build_summary(result)
    return result


def _build_summary(d):
    parts = []

    if d['weather']:
        parts.append(d['weather'][0].capitalize())
    elif d['sky_condition']:
        parts.append(SKY_CONDITIONS.get(d['sky_condition'], ('Unknown skies',))[0])

    if d['temperature_f'] is not None:
        parts.append(f"{d['temperature_f']}°F")

    if d['wind']:
        w = d['wind']
        if w['speed_kt'] == 0:
            parts.append('calm winds')
        elif w['gust_mph']:
            parts.append(f"winds {w['speed_mph']}–{w['gust_mph']} mph from the {w['direction']}")
        else:
            parts.append(f"winds {w['speed_mph']} mph from the {w['direction']}")

    return (', '.join(parts) + '.') if parts else 'Weather data parsed.'

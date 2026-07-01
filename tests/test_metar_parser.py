"""Unit tests for metar_parser.py — exercises the decoder with mock METAR strings."""

from metar_parser import (
    parse_metar,
    celsius_to_fahrenheit,
    knots_to_mph,
    degrees_to_cardinal,
)

# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestCelsiusToFahrenheit:
    def test_freezing(self):
        assert celsius_to_fahrenheit(0) == 32

    def test_boiling(self):
        assert celsius_to_fahrenheit(100) == 212

    def test_negative_forty_is_equal_in_both_scales(self):
        assert celsius_to_fahrenheit(-40) == -40

    def test_typical_warm_day(self):
        assert celsius_to_fahrenheit(20) == 68


class TestKnotsToMph:
    def test_zero(self):
        assert knots_to_mph(0) == 0

    def test_known_conversion(self):
        assert knots_to_mph(10) == 12  # 10 * 1.15078 rounds to 12


class TestDegreesToCardinal:
    def test_north(self):
        assert degrees_to_cardinal(0) == "north"

    def test_east(self):
        assert degrees_to_cardinal(90) == "east"

    def test_south(self):
        assert degrees_to_cardinal(180) == "south"

    def test_west(self):
        assert degrees_to_cardinal(270) == "west"

    def test_northeast(self):
        assert degrees_to_cardinal(45) == "northeast"

    def test_southwest(self):
        assert degrees_to_cardinal(225) == "southwest"


# ---------------------------------------------------------------------------
# parse_metar — edge cases
# ---------------------------------------------------------------------------


class TestParseMetarEdgeCases:
    def test_returns_none_for_empty_string(self):
        assert parse_metar("") is None

    def test_metar_keyword_prefix_is_stripped(self):
        raw = "METAR KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        result = parse_metar(raw)
        assert result["station"] == "KJFK"

    def test_raw_string_preserved(self):
        raw = "KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        assert parse_metar(raw)["raw"] == raw

    def test_time_parsed_correctly(self):
        raw = "KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        assert parse_metar(raw)["time_utc"] == "15:51 UTC (day 29)"


# ---------------------------------------------------------------------------
# parse_metar — wind
# ---------------------------------------------------------------------------


class TestWind:
    def test_basic_wind_direction_and_speed(self):
        raw = "KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        wind = parse_metar(raw)["wind"]
        assert wind["degrees"] == 220
        assert wind["speed_kt"] == 15
        assert wind["direction"] == "southwest"
        assert wind["gust_kt"] is None

    def test_wind_with_gusts(self):
        raw = "KJFK 291551Z 18020G35KT 1SM +TSRA OVC010 22/20 A2965"
        wind = parse_metar(raw)["wind"]
        assert wind["speed_kt"] == 20
        assert wind["gust_kt"] == 35
        assert wind["gust_mph"] == knots_to_mph(35)

    def test_calm_winds(self):
        raw = "KSFO 291556Z 00000KT 10SM SKC 15/10 A3012"
        wind = parse_metar(raw)["wind"]
        assert wind["speed_kt"] == 0

    def test_variable_winds(self):
        raw = "KSLC 291553Z VRB03KT 10SM BKN150 32/05 A3002"
        wind = parse_metar(raw)["wind"]
        assert wind["direction"] == "variable"
        assert wind["degrees"] is None

    def test_auto_flag_set(self):
        raw = "KORD 291551Z AUTO 28012KT 10SM CLR 22/14 A2998"
        assert parse_metar(raw)["auto"] is True

    def test_auto_flag_absent(self):
        raw = "KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        assert parse_metar(raw)["auto"] is False


# ---------------------------------------------------------------------------
# parse_metar — visibility
# ---------------------------------------------------------------------------


class TestVisibility:
    def test_statute_miles(self):
        raw = "KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        assert parse_metar(raw)["visibility"] == 10.0

    def test_fractional_statute_miles(self):
        raw = "KSFO 291556Z 31005KT 1/4SM FG OVC002 14/13 A3008"
        result = parse_metar(raw)
        assert abs(result["visibility"] - 0.25) < 0.01

    def test_metric_meters(self):
        raw = "EGLL 291550Z 25015KT 9999 FEW025 SCT060 18/10 Q1013"
        assert parse_metar(raw)["visibility"] == 9999

    def test_cavok_sets_visibility(self):
        raw = "EGLL 291550Z 25012KT CAVOK 20/08 Q1018"
        result = parse_metar(raw)
        assert result["visibility"] == 10.0
        assert result["sky_condition"] == "CAVOK"


# ---------------------------------------------------------------------------
# parse_metar — weather phenomena
# ---------------------------------------------------------------------------


class TestWeatherPhenomena:
    def test_light_rain(self):
        raw = "KJFK 291551Z 22015KT 5SM -RA FEW025 BKN080 18/15 A2985"
        result = parse_metar(raw)
        assert any("rain" in w for w in result["weather"])
        assert result["emoji"] == "🌧️"

    def test_heavy_thunderstorm_with_rain(self):
        raw = "KJFK 291551Z 18020G35KT 1SM +TSRA OVC010 22/20 A2965"
        result = parse_metar(raw)
        assert any("thunderstorm" in w for w in result["weather"])
        assert result["emoji"] == "⛈️"

    def test_light_snow(self):
        raw = "KDEN 291553Z 35015G25KT 2SM -SN BKN020 OVC040 M02/M07 A2985"
        result = parse_metar(raw)
        assert any("snow" in w for w in result["weather"])
        assert result["emoji"] == "❄️"

    def test_fog(self):
        raw = "KSFO 291556Z 31005KT 1/4SM FG OVC002 14/13 A3008"
        result = parse_metar(raw)
        assert any("fog" in w for w in result["weather"])
        assert result["emoji"] == "🌫️"

    def test_no_phenomena_clear_day_emoji(self):
        raw = "KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        assert parse_metar(raw)["emoji"] == "☀️"

    def test_overcast_no_precip_emoji(self):
        raw = "KJFK 291551Z 22015KT 10SM OVC050 18/14 A2985"
        assert parse_metar(raw)["emoji"] == "☁️"

    def test_partly_cloudy_emoji(self):
        raw = "KJFK 291551Z 22015KT 10SM FEW030 24/14 A2991"
        assert parse_metar(raw)["emoji"] == "⛅"


# ---------------------------------------------------------------------------
# parse_metar — sky conditions
# ---------------------------------------------------------------------------


class TestSkyConditions:
    def test_clear(self):
        raw = "KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        assert parse_metar(raw)["sky_condition"] == "CLR"

    def test_overcast(self):
        raw = "KJFK 291551Z 18020G35KT 1SM +TSRA OVC010 22/20 A2965"
        assert parse_metar(raw)["sky_condition"] == "OVC"

    def test_multiple_layers_uses_highest_coverage(self):
        raw = "KJFK 291551Z 22015KT 5SM -RA FEW025 BKN080 18/15 A2985"
        result = parse_metar(raw)
        assert len(result["sky"]) == 2
        assert result["sky_condition"] == "BKN"

    def test_sky_layer_heights(self):
        raw = "KJFK 291551Z 22015KT 5SM -RA FEW025 BKN080 18/15 A2985"
        sky = parse_metar(raw)["sky"]
        assert sky[0]["cover"] == "FEW"
        assert sky[0]["height_ft"] == 2500
        assert sky[1]["cover"] == "BKN"
        assert sky[1]["height_ft"] == 8000


# ---------------------------------------------------------------------------
# parse_metar — temperature, dewpoint, humidity
# ---------------------------------------------------------------------------


class TestTemperatureAndHumidity:
    def test_positive_temperature(self):
        raw = "KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        result = parse_metar(raw)
        assert result["temperature_c"] == 24
        assert result["temperature_f"] == celsius_to_fahrenheit(24)
        assert result["dewpoint_c"] == 14

    def test_negative_temperature(self):
        raw = "KDEN 291553Z 35015G25KT 2SM -SN BKN020 OVC040 M02/M07 A2985"
        result = parse_metar(raw)
        assert result["temperature_c"] == -2
        assert result["dewpoint_c"] == -7
        assert result["temperature_f"] == celsius_to_fahrenheit(-2)

    def test_humidity_at_saturation(self):
        # temp == dewpoint → 100% humidity
        raw = "KSFO 291556Z 31005KT 1SM FG OVC002 14/14 A3008"
        assert parse_metar(raw)["humidity"] == 100

    def test_humidity_low_when_dry(self):
        # large temp/dewpoint spread → low humidity
        raw = "KPHX 291551Z 20010KT 10SM CLR 38/04 A2990"
        assert parse_metar(raw)["humidity"] < 15


# ---------------------------------------------------------------------------
# parse_metar — altimeter
# ---------------------------------------------------------------------------


class TestAltimeter:
    def test_a_format_inhg(self):
        raw = "KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        assert parse_metar(raw)["altimeter"] == 29.91

    def test_q_format_hpa(self):
        raw = "EGLL 291550Z 25015KT 9999 FEW025 SCT060 18/10 Q1013"
        expected = round(1013 * 0.02953, 2)
        assert parse_metar(raw)["altimeter"] == expected


# ---------------------------------------------------------------------------
# parse_metar — details list
# ---------------------------------------------------------------------------


class TestDetailsList:
    def test_full_metar_populates_expected_detail_labels(self):
        raw = "KJFK 291551Z 22015KT 10SM CLR 24/14 A2991"
        labels = [d["label"] for d in parse_metar(raw)["details"]]
        assert "Wind" in labels
        assert "Visibility" in labels
        assert "Sky" in labels
        assert "Temperature" in labels
        assert "Dew Point" in labels
        assert "Humidity" in labels
        assert "Pressure" in labels

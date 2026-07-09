"""Tests for compact numeric label formatting (shwirl.labels)."""
from shwirl.labels import (
    factor_suffix,
    format_plain,
    format_range,
    offset_exponent,
    offset_format,
)


def test_offset_exponent_kicks_in_for_large_values():
    assert offset_exponent([62863, -92723]) == 4


def test_offset_exponent_off_for_ordinary_values():
    # RA (~150 deg) and velocity (~7000 km/s) stay un-offset.
    assert offset_exponent([149.3, 149.8]) == 0
    assert offset_exponent([7100, 7360]) == 0


def test_offset_exponent_handles_empty_and_zero():
    assert offset_exponent([]) == 0
    assert offset_exponent([0, 0]) == 0
    assert offset_exponent([None, float("nan")]) == 0


def test_offset_exponent_small_magnitudes():
    assert offset_exponent([1.2e-5, 3.4e-5]) == -5


def test_offset_format_scales_endpoints():
    exp, (lo, hi) = offset_format(62863, -92723)
    assert exp == 4
    assert lo == "6.3"
    assert hi == "-9.3"


def test_offset_format_plain_when_no_offset():
    exp, (lo, hi) = offset_format(0, 64)
    assert exp == 0
    assert (lo, hi) == ("0", "64")


def test_factor_suffix():
    assert factor_suffix(0) == ""
    assert factor_suffix(4) == "×10⁴"
    assert factor_suffix(-5) == "×10⁻⁵"


def test_format_plain():
    assert format_plain(64.0) == "64"
    assert format_plain(149.34) == "149"
    assert format_plain(0) == "0"


def test_format_range():
    assert format_range(7100, 7360, unit="km/s") == "7100–7360 km/s"
    assert format_range(62863, -92723) == "6.3–-9.3 ×10⁴"


def test_format_range_keeps_small_spans_distinguishable():
    # RA/Dec: a tiny span on a large value must not collapse to one number.
    lo, hi = format_range(180.0, 180.03, unit="deg").split(" deg")[0].split("–")
    assert lo != hi
    assert format_range(149.30, 149.80, unit="deg") == "149.30–149.80 deg"


def test_short_axis_name():
    from shwirl.labels import short_axis_name
    assert short_axis_name("RA---SIN") == "RA"
    assert short_axis_name("DEC--SIN") == "Dec"
    assert short_axis_name("VELO-LSR") == "Vel"
    assert short_axis_name("FREQ") == "Freq"
    assert short_axis_name("") == "?"

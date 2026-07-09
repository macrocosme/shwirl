"""Compact numeric label formatting for the colorbar and 3D axes.

Pure helpers (no Qt/GL) so they are unit-testable. The scheme is an *offset
multiplier*: when a set of values has a large (or very small) magnitude, factor
out a common power of ten, show it once (e.g. ``×10⁴``), and print short scaled
tick numbers -- keeping labels readable and inside the frame.
"""

import math

# Map ASCII digits/sign to Unicode superscripts for a compact "×10ⁿ" suffix.
_SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def offset_exponent(values, threshold=4):
    """Common power of ten to factor out of ``values``.

    Returns 0 (i.e. "show the numbers as-is") unless the largest magnitude has an
    exponent of at least ``threshold`` in absolute value, so ordinary-sized
    numbers (RA in degrees, velocities in km/s, ...) stay untouched while huge or
    tiny ones (raw data units) get an offset.
    """
    mags = []
    for v in values:
        if v is None:
            continue
        try:
            f = abs(float(v))
        except (TypeError, ValueError):
            continue
        if f > 0 and math.isfinite(f):
            mags.append(f)
    if not mags:
        return 0
    exp = math.floor(math.log10(max(mags)))
    return exp if abs(exp) >= threshold else 0


def format_plain(v, sig=3):
    """Format a single value without an offset: integers stay integral."""
    f = float(v)
    if f == int(f):
        return str(int(f))
    return f"{f:.{sig}g}"


def offset_format(vmin, vmax, threshold=4, max_decimals=4):
    """Return ``(exp, [lo_str, hi_str])`` for a value range.

    ``exp`` is the factored-out power of ten (0 when none). Decimal precision is
    chosen from the *span* so the two endpoints stay distinguishable -- important
    for e.g. RA/Dec, where the range is a tiny fraction of a large value. Pure
    integer ranges with no offset are printed without decimals.
    """
    exp = offset_exponent([vmin, vmax], threshold=threshold)
    if exp == 0 and float(vmin).is_integer() and float(vmax).is_integer():
        return 0, [format_plain(vmin), format_plain(vmax)]
    scale = 10.0 ** exp
    a, b = float(vmin) / scale, float(vmax) / scale
    span = abs(b - a)
    if span == 0:
        decimals = 1
    else:
        decimals = min(max_decimals, max(1, -math.floor(math.log10(span)) + 1))
    return exp, [f"{a:.{decimals}f}", f"{b:.{decimals}f}"]


def factor_suffix(exp):
    """`"×10⁴"`-style suffix for a factored exponent; `""` when ``exp`` is 0."""
    if not exp:
        return ""
    return "×10" + str(int(exp)).translate(_SUPERSCRIPT)


def format_range(vmin, vmax, unit=""):
    """Compact one-line range, e.g. ``"6.3–9.8 ×10⁴ Jy"`` or ``"149.3–149.8 deg"``."""
    exp, (lo, hi) = offset_format(vmin, vmax)
    suffix = (" " + factor_suffix(exp)) if exp else ""
    unit = (" " + unit) if unit else ""
    return f"{lo}–{hi}{suffix}{unit}"


# Friendly short names for common FITS CTYPE axes (prefix match, case-insensitive).
_AXIS_SHORT = (
    ("RA", "RA"), ("DEC", "Dec"), ("GLON", "GLon"), ("GLAT", "GLat"),
    ("VELO", "Vel"), ("VRAD", "Vel"), ("VOPT", "Vel"), ("FELO", "Vel"),
    ("FREQ", "Freq"), ("WAVE", "λ"), ("AWAV", "λ"), ("STOKES", "Stokes"),
)


def short_axis_name(ctype):
    """A compact, human-friendly axis name from a FITS CTYPE (e.g. RA---SIN → RA)."""
    c = (ctype or "").strip().upper()
    for key, short in _AXIS_SHORT:
        if c.startswith(key):
            return short
    return (ctype or "?").strip() or "?"

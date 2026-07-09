"""Robust, provenance-agnostic FITS loading and dimension normalisation.

Pure logic only (no Qt), so it can be unit-tested headlessly. The Qt file dialog
and the axis-selection dialog live in :mod:`shwirl.shwirl`; this module turns an
arbitrary FITS file into a clean 3D ``(depth, y, x)`` numpy array plus per-axis
metadata that the renderer and axis labels consume.

Design notes
------------
- FITS stores axes fastest-first: ``NAXIS1`` is the fastest-varying axis, so the
  numpy array returned by astropy has ``shape == (NAXISn, ..., NAXIS2, NAXIS1)``.
  Each axis descriptor therefore carries both its 1-based ``fits_index`` and its
  0-based ``numpy_axis`` position in the current array.
- Degenerate (length-1) axes -- e.g. a single-plane Stokes axis -- are squeezed
  away automatically, which is what collapses most "4D" radio cubes to 3D.
"""

import numpy as np
from astropy.io import fits

# Spectral CTYPE prefixes (FITS WCS paper III + common radio conventions).
SPECTRAL_PREFIXES = (
    "FREQ", "VELO", "VRAD", "VOPT", "FELO", "WAVE",
    "ENER", "WAVN", "AWAV", "ZOPT", "BETA",
)


class FitsLoadError(Exception):
    """Raised when a FITS file cannot be read (truncated, corrupt, no data)."""


def open_fits(path):
    """Open a FITS file, tolerating a missing ``SIMPLE`` card.

    Returns an :class:`astropy.io.fits.HDUList`. Raises :class:`FitsLoadError`
    with a human-friendly message for files that are not FITS at all or that
    fail to open even leniently. Truncation is usually detected later, when the
    data array is accessed (see :func:`find_data_hdu`).
    """
    try:
        return fits.open(path)
    except OSError as exc:
        if "simple" in str(exc).lower():
            try:
                return fits.open(path, ignore_missing_simple=True)
            except Exception as exc2:  # noqa: BLE001 - re-raised as FitsLoadError
                raise FitsLoadError(_friendly(path, exc2)) from exc2
        raise FitsLoadError(_friendly(path, exc)) from exc


def find_data_hdu(hdulist):
    """Return the first HDU that actually holds image/cube data (``NAXIS >= 2``).

    Handles multi-extension files whose primary HDU is empty. Reading the data
    array of a truncated file raises here; it is wrapped in :class:`FitsLoadError`.
    """
    for hdu in hdulist:
        naxis = int(hdu.header.get("NAXIS", 0) or 0)
        if naxis < 2:
            continue
        try:
            data = hdu.data
        except (OSError, TypeError, ValueError, AttributeError) as exc:
            # AttributeError occurs for un-classifiable HDUs (e.g. a file opened
            # leniently because it lacked a SIMPLE card); the rest signal a
            # truncated/corrupt data unit.
            raise FitsLoadError(
                "This FITS file appears truncated or corrupt and cannot be read "
                f"({type(exc).__name__}: {exc})."
            ) from exc
        if data is not None:
            return hdu
    raise FitsLoadError("No image or cube data (NAXIS >= 2) found in this FITS file.")


def describe_axes(header):
    """Return a list of axis descriptors, one per FITS axis, in FITS order.

    Each descriptor: ``fits_index`` (1-based), ``ctype``, ``cunit``, ``crval``,
    ``cdelt``, ``length`` (NAXISn), and ``numpy_axis`` (0-based position in the
    astropy data array). Missing WCS cards are tolerated with sane defaults.
    """
    naxis = int(header.get("NAXIS", 0) or 0)
    axes = []
    for i in range(1, naxis + 1):
        axes.append({
            "fits_index": i,
            "ctype": (header.get(f"CTYPE{i}", "") or "").strip(),
            "cunit": (header.get(f"CUNIT{i}", "") or "").strip(),
            "crval": header.get(f"CRVAL{i}", 0.0),
            "cdelt": header.get(f"CDELT{i}", 1.0),
            "length": int(header.get(f"NAXIS{i}", 0) or 0),
            "numpy_axis": naxis - i,
        })
    return axes


def squeeze_degenerate(data, axes):
    """Drop length-1 axes from ``data`` and ``axes``, keeping them in sync.

    Returns ``(data, kept_axes)`` with ``numpy_axis`` re-based to the squeezed
    array. Raises :class:`FitsLoadError` if fewer than two real axes remain.
    """
    kept = [a for a in axes if a["length"] > 1]
    drop = tuple(a["numpy_axis"] for a in axes if a["length"] <= 1)
    if drop:
        data = np.squeeze(data, axis=drop)
    if len(kept) < 2:
        raise FitsLoadError(
            "This FITS file has fewer than two non-trivial dimensions; "
            "there is nothing to display."
        )
    # Re-base numpy_axis: surviving axes keep their relative order.
    for new_pos, a in enumerate(sorted(kept, key=lambda a: a["numpy_axis"])):
        a["numpy_axis"] = new_pos
    return data, kept


def is_spectral(ctype):
    """True if a CTYPE names a spectral axis (frequency/velocity/wavelength/…)."""
    return (ctype or "").upper().startswith(SPECTRAL_PREFIXES)


def is_ambiguous(axes):
    """True when more than three real axes remain, so the user must choose."""
    return len(axes) > 3


def default_selection(axes):
    """Pick a sensible axis mapping without user input.

    Heuristic: the spectral axis (if any) becomes depth ``z``; the two spatial
    axes become the plane, ``x`` = lower FITS index, ``y`` = higher; any leftover
    axis is fixed at index 0. For a 2D image, ``z`` is ``None`` (single slice).

    Returns a selection dict: ``{"x": axis|None, "y": axis|None, "z": axis|None,
    "fixed": [(axis, index), ...]}``.
    """
    spectral = [a for a in axes if is_spectral(a["ctype"])]
    z = spectral[0] if spectral else None
    remaining = sorted((a for a in axes if a is not z), key=lambda a: a["fits_index"])
    if z is None and len(remaining) >= 3:
        # No spectral axis: treat the highest FITS axis as depth.
        z = remaining[-1]
        remaining = remaining[:-1]
    x = remaining[0] if len(remaining) >= 1 else None
    y = remaining[1] if len(remaining) >= 2 else None
    used = {id(a) for a in (x, y, z) if a is not None}
    fixed = [(a, 0) for a in axes if id(a) not in used]
    return {"x": x, "y": y, "z": z, "fixed": fixed}


def build_cube(data, selection):
    """Reduce/reorder ``data`` into ``(depth, y, x)`` per ``selection``.

    Fixed axes are indexed out, the remaining axes are transposed to
    ``(z, y, x)``, and a 2D plane (``z is None``) is promoted to a depth-1 slab.

    Returns ``(array, axis_info)`` where ``axis_info`` is
    ``{"x": info, "y": info, "z": info}`` and each ``info`` carries
    ``label/ctype/cunit/crval/cdelt/length`` for that display axis.
    """
    x, y, z = selection["x"], selection["y"], selection["z"]
    fixed = selection.get("fixed", [])

    # Slice out fixed axes.
    index = [slice(None)] * data.ndim
    for axis, i in fixed:
        index[axis["numpy_axis"]] = int(i)
    sub = data[tuple(index)]

    fixed_positions = {axis["numpy_axis"] for axis, _ in fixed}

    def new_pos(axis):
        # Position in ``sub`` after the fixed axes were removed.
        return sum(1 for p in range(axis["numpy_axis"]) if p not in fixed_positions)

    order = [a for a in (z, y, x) if a is not None]
    arr = np.transpose(sub, [new_pos(a) for a in order])
    if z is None:
        arr = arr[np.newaxis, ...]
    arr = np.ascontiguousarray(arr)

    zlen, ylen, xlen = arr.shape
    axis_info = {
        "x": _axis_info(x, xlen),
        "y": _axis_info(y, ylen),
        "z": _axis_info(z, zlen),
    }
    return arr, axis_info


def load_fits_cube(path, select=None):
    """Convenience end-to-end loader used by the GUI and tests.

    Opens ``path`` robustly, finds the data HDU, squeezes degenerate axes, then
    builds the cube. ``select`` is a callable ``(axes) -> selection`` used only
    when the axes are ambiguous (>3 real dims); if omitted, the default heuristic
    is used. Returns ``(array, header, axis_info, axes, selection)``.
    """
    hdu = find_data_hdu(open_fits(path))
    axes = describe_axes(hdu.header)
    data, axes = squeeze_degenerate(hdu.data, axes)
    if is_ambiguous(axes) and select is not None:
        selection = select(axes)
    else:
        selection = default_selection(axes)
    arr, axis_info = build_cube(data, selection)
    return arr, hdu.header, axis_info, axes, selection


def _axis_info(axis, length):
    if axis is None:
        return {"label": "slice", "ctype": "", "cunit": "",
                "crval": 0.0, "cdelt": 1.0, "length": length}
    return {"label": axis["ctype"] or "unknown", "ctype": axis["ctype"],
            "cunit": axis["cunit"], "crval": axis["crval"],
            "cdelt": axis["cdelt"], "length": length}


def _friendly(path, exc):
    return (f"Could not open '{path}' as a FITS file. It may be corrupt, "
            f"truncated, or not a FITS file ({type(exc).__name__}: {exc}).")

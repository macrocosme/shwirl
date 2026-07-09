"""Tests for file-type detection and gzipped-FITS reading."""
import gzip

import numpy as np
import pytest
from astropy.io import fits

from shwirl.shwirl import is_filterbank_filename, is_fits_filename


@pytest.mark.parametrize(
    "name",
    [
        "cube.fits",
        "cube.FITS",
        "cube.fit",
        "cube.fts",
        "cube.fits.gz",
        "cube.FITS.GZ",
        "/some/path/511867_red.fits.gz",
        "MyCube.Fits.Gz",
    ],
)
def test_is_fits_filename_accepts(name):
    assert is_fits_filename(name)


@pytest.mark.parametrize("name", ["cube.fil", "notes.txt", "cube.png", "cube.gz", "cube"])
def test_is_fits_filename_rejects(name):
    assert not is_fits_filename(name)


def test_is_filterbank_filename():
    assert is_filterbank_filename("obs.fil")
    assert is_filterbank_filename("OBS.FIL")
    assert not is_filterbank_filename("obs.fits")


def test_astropy_reads_gzipped_fits(tmp_path):
    """shwirl reads FITS via fits.open(); confirm it handles .gz transparently."""
    data = np.arange(2 * 3 * 4, dtype=np.float32).reshape(2, 3, 4)
    plain = tmp_path / "cube.fits"
    fits.PrimaryHDU(data).writeto(plain)

    gzipped = tmp_path / "cube.fits.gz"
    with open(plain, "rb") as f_in, gzip.open(gzipped, "wb") as f_out:
        f_out.write(f_in.read())

    assert is_fits_filename(str(gzipped))
    with fits.open(str(gzipped)) as hdul:
        np.testing.assert_array_equal(hdul[0].data, data)


# ---------------------------------------------------------------------------
# fits_loader: robust opening + dimension normalisation
# ---------------------------------------------------------------------------
from shwirl.fits_loader import (  # noqa: E402
    FitsLoadError,
    build_cube,
    default_selection,
    describe_axes,
    find_data_hdu,
    is_ambiguous,
    load_fits_cube,
    open_fits,
    squeeze_degenerate,
)


def _cube_header(shape, ctypes):
    """A FITS Header describing a cube of `shape` (numpy order) with `ctypes`.

    `ctypes` are given in FITS axis order (CTYPE1 first); numpy shape is reversed.
    """
    hdu = fits.PrimaryHDU(np.zeros(shape, dtype=np.float32))
    h = hdu.header
    for i, ct in enumerate(ctypes, start=1):
        h[f"CTYPE{i}"] = ct
        h[f"CRVAL{i}"] = 0.0
        h[f"CDELT{i}"] = 1.0
    return hdu


def test_open_fits_tolerates_missing_simple(tmp_path):
    """A header lacking the SIMPLE card opens (via the lenient retry) instead of
    raising the raw ``No SIMPLE card`` OSError to the caller."""
    data = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    path = tmp_path / "cube.fits"
    fits.PrimaryHDU(data).writeto(path)

    # Corrupt the mandatory SIMPLE card into something non-standard.
    raw = bytearray(path.read_bytes())
    assert raw[:6] == b"SIMPLE"
    raw[:6] = b"XIMPLE"
    path.write_bytes(raw)

    # open_fits must not raise; the header is still readable.
    with open_fits(str(path)) as hdul:
        assert hdul[0].header["NAXIS"] == 3


def test_find_data_hdu_skips_empty_primary(tmp_path):
    """MEF file with an empty primary HDU: data is found in the image extension."""
    data = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    path = tmp_path / "mef.fits"
    fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(data)]).writeto(path)

    with open_fits(str(path)) as hdul:
        hdu = find_data_hdu(hdul)
        np.testing.assert_array_equal(hdu.data, data)


def test_find_data_hdu_raises_on_truncated(tmp_path):
    """A truncated data block surfaces as a friendly FitsLoadError."""
    data = np.arange(20 * 20 * 20, dtype=np.float32).reshape(20, 20, 20)
    path = tmp_path / "trunc.fits"
    fits.PrimaryHDU(data).writeto(path)
    raw = path.read_bytes()
    # Keep the header block plus only a sliver of the data unit, so the array
    # cannot be formed (mirrors a partial download).
    path.write_bytes(raw[:5000])

    with pytest.raises(FitsLoadError):
        find_data_hdu(open_fits(str(path)))


def test_squeeze_degenerate_collapses_stokes(tmp_path):
    """A 4D (Stokes=1) cube squeezes down to three real axes."""
    # FITS: NAXIS1=X, NAXIS2=Y, NAXIS3=Z(freq), NAXIS4=Stokes(1)
    # numpy shape is reversed: (1, 5, 4, 3)
    hdu = _cube_header((1, 5, 4, 3), ["RA---SIN", "DEC--SIN", "FREQ", "STOKES"])
    axes = describe_axes(hdu.header)
    assert len(axes) == 4
    data, kept = squeeze_degenerate(hdu.data, axes)
    assert data.shape == (5, 4, 3)
    assert len(kept) == 3
    assert not is_ambiguous(kept)


def test_default_selection_puts_spectral_on_depth():
    """For an RA/Dec/FREQ cube the spectral axis becomes depth (z)."""
    hdu = _cube_header((5, 4, 3), ["RA---SIN", "DEC--SIN", "FREQ"])
    axes = describe_axes(hdu.header)
    sel = default_selection(axes)
    assert sel["z"]["ctype"] == "FREQ"
    assert {sel["x"]["ctype"], sel["y"]["ctype"]} == {"RA---SIN", "DEC--SIN"}
    assert sel["fixed"] == []


def test_is_ambiguous_true_for_full_4d():
    """A genuine 4D cube (all axes > 1) requires user selection."""
    hdu = _cube_header((2, 5, 4, 3), ["RA---SIN", "DEC--SIN", "FREQ", "STOKES"])
    axes = describe_axes(hdu.header)
    assert is_ambiguous(axes)


def test_build_cube_promotes_2d_to_single_slice():
    """A 2D image is promoted to a depth-1 volume the renderer can draw."""
    hdu = _cube_header((7, 6), ["RA---SIN", "DEC--SIN"])
    axes = describe_axes(hdu.header)
    data, axes = squeeze_degenerate(hdu.data, axes)
    sel = default_selection(axes)
    assert sel["z"] is None
    arr, info = build_cube(data, sel)
    assert arr.shape == (1, 7, 6)
    assert info["z"]["label"] == "slice"


def test_load_fits_cube_end_to_end_3d(tmp_path):
    """The convenience loader returns a (depth, y, x) array for a 3D cube."""
    hdu = _cube_header((5, 4, 3), ["RA---SIN", "DEC--SIN", "FREQ"])
    hdu.data[:] = np.arange(60, dtype=np.float32).reshape(5, 4, 3)
    path = tmp_path / "cube.fits"
    hdu.writeto(path)
    arr, header, axis_info, axes, selection = load_fits_cube(str(path))
    assert arr.shape == (5, 4, 3)
    assert axis_info["z"]["ctype"] == "FREQ"


def test_build_cube_selection_reorders_and_fixes():
    """User selection can pick display axes and hold an extra axis at an index."""
    # 4D RA/Dec/FREQ/STOKES, Stokes length 2 -> ambiguous.
    hdu = _cube_header((2, 5, 4, 3), ["RA---SIN", "DEC--SIN", "FREQ", "STOKES"])
    hdu.data[:] = np.arange(2 * 5 * 4 * 3, dtype=np.float32).reshape(2, 5, 4, 3)
    axes = describe_axes(hdu.header)
    data, axes = squeeze_degenerate(hdu.data, axes)  # nothing to squeeze (all > 1)
    by_ct = {a["ctype"]: a for a in axes}
    selection = {
        "x": by_ct["RA---SIN"],
        "y": by_ct["DEC--SIN"],
        "z": by_ct["FREQ"],
        "fixed": [(by_ct["STOKES"], 1)],
    }
    arr, info = build_cube(data, selection)
    assert arr.shape == (5, 4, 3)  # (FREQ, DEC, RA)
    # Equivalent manual reduction: Stokes=1 then transpose to (z, y, x).
    expected = np.transpose(hdu.data[1], (0, 1, 2))
    np.testing.assert_array_equal(arr, expected)

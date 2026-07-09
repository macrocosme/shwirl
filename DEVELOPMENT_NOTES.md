# Development notes — 2026-07-08

Changes made **since the pulled GitHub version** (branch `macrocosme/modernize`,
baseline commit `c38be14` "Update CLAUDE.md: VisPy un-vendored; app launches on
macOS"). Everything below is currently **uncommitted** in the working tree.

At the baseline, the app launched and the shaders compiled, but it had never
actually rendered a *real* FITS cube end-to-end (the render test used a synthetic,
native-endian, `grays`-colormapped cube). This round makes real cubes load and
render, adds dynamic-range stretches, and cleans up the on-screen annotation.

### Scope of this note

The macOS revival happened in two layers. The **first layer is already committed**
at/before the baseline `c38be14` and is *not* repeated here: PyQt5 → **PySide6**
(Qt6) migration, **un-vendoring VisPy** (`vispy>=0.16`, resolving the Qt6/`QGLWidget`
blocker), the Python 3.10+ cleanup (dropped `__future__`/`six`/PyQt4 fallback), the
fixed entry point, and the optional-`blimpy` extra. That layer got the app to
*launch* on current macOS. **This note is the second layer** (uncommitted): the
fixes that make it actually *load and render real cubes*, plus the new features.
See `.claude/CLAUDE.md` and the project memory for the committed first-layer detail.

---

## 1. Robust, provenance-agnostic FITS loading  *(new `shwirl/fits_loader.py`)*

Loading was fragile: it assumed data in `HDU[0]`, axis 0 = spectral, a hardcoded
`CTYPE[1,3,2]` order, and a single `data[0]` case for 4D.

- **Reads plain *and* gzipped FITS** (`.fits.gz`, `.fit.gz`, `.fts.gz`) — astropy
  handles the decompression; extension detection is case-insensitive
  (`is_fits_filename`).
- **`open_fits`** tolerates a missing `SIMPLE` card (lenient retry) instead of
  throwing a raw `OSError`.
- **`find_data_hdu`** locates the first HDU that actually holds image/cube data
  (`NAXIS ≥ 2`), so multi-extension files with an empty primary HDU work.
- **Truncated / partial-download files** (e.g. `*.part`, `*.partial-Nof87.fits`)
  now raise a friendly `FitsLoadError` shown in a `QMessageBox`, not a console
  traceback.
- **Degenerate axes squeezed** automatically (e.g. a length-1 Stokes axis collapses
  a "4D" cube to 3D).
- **2D images** are promoted to a single-slice (depth-1) volume and rendered.
- **>3D (ambiguous) cubes** open an **`AxisSelectionDialog`** to map FITS axes to
  display X/Y/Z (+ a fixed index for extra axes). A **"Select axes…"** button
  re-opens it any time to re-slice a loaded cube.
- Both FITS and filterbank data are now wrapped in a small `LoadedCube`
  (`data` / `header` / `axis_info` / `kind`) handed to the renderer.

## 2. Render-pipeline fixes for NumPy 2 / modern VisPy

These bugs blocked real cubes from drawing (the synthetic test path dodged them):

- `np.int` → `int` in the velocity-limit code (`np.int` was removed in NumPy 2; any
  cube with a `CDELT3` axis crashed).
- Big-endian FITS: `np.array(vol, dtype='float32', copy=False)` → `np.asarray(...)`
  in `render_volume.py` (NumPy 2 refuses the unavoidable copy for `>f4` data).
- Colorbar `self.cbar.label_str = …` → `self.cbar.label.text = …` (vispy API drift).
- **Colormap sampler collision:** added the missing
  `shared_program['texture2D_LUT'] = cmap.texture_lut()` in the `RenderVolume`
  `cmap`/`method` setters. Without it, texture-based colormaps (e.g. `hsl`) left
  the LUT sampler at texture unit 0, colliding with the 3D volume texture → GL
  "Samplers of different types use the same texture image unit" (blank canvas on
  macOS core profile).

## 3. Dynamic-range transfer-function stretches  *(Rector et al. 2007)*

The transfer functions were always linear (the scaling machinery was commented out
in both the GLSL and the UI).

- New **"Dynamic range"** dropdown: **Linear, Logarithmic, Square root, Asinh,
  Power**.
- Implemented as a single `applyScale()` GLSL function in the shared `FRAG_SHADER`,
  selected by the `u_color_scale` uniform (via the `color_scale` property /
  `_SCALE_CODES`); `asinh` is expanded manually since GLSL 120 lacks it.
- Every **intensity** `$cmap(...)` across all 7 shaders is wrapped
  `$cmap(applyScale(...))`. Velocity (Moment 1) and RGB colourings keep their hue
  (`$cmap(loc.y)` unstretched) but the stretch is applied to the **intensity that
  drives opacity/alpha** there, so the control works in those modes too.

## 4. Colorbar overhaul

- **Refreshes reliably** when the volume colormap changes (cmap/clim updated even
  while the bar is hidden, so it stays in sync).
- **Compact, in-frame labels** via an **offset multiplier**: large data ranges show
  short tick numbers plus a `×10ⁿ` factor folded into the label
  (e.g. `Jy/beam (×10⁴)`). Root cause of the old clipping: vispy regenerates tick
  text as `str(clim)` every draw, so the fix feeds it already-scaled short `clim`
  values rather than overriding `ticks[i].text`.
- **Title no longer sits on the bar, values no longer run off-canvas:** the bar
  lives in the left column but is created with vispy orientation `'right'` so its
  label/ticks face the canvas interior; column widened and `text_padding_factor`
  bumped so the rotated title clears the bar.

## 5. 3D axes revamp  *("less is more")*

- Replaced the dense, overlapping per-edge WCS ticks (`vispy.scene.visuals.Axis`)
  with just the **cube outline + an orientation triad** (three short coloured arrows
  + short axis names RA/Vel/Dec, rotating with the data).
- Numeric axis ranges moved to a screen-fixed, translucent **info-panel** QLabel
  overlay pinned to the **lower-right** of the canvas (`Canvas3D._update_info_panel`
  / `_reposition_info_panel`), formatted with span-aware precision so tiny RA/Dec
  spans stay distinguishable.

## 6. New shared formatting module  *(`shwirl/labels.py`)*

Pure, unit-tested numeric/label helpers used by both the colorbar and axes:
`offset_exponent` / `offset_format` (offset multiplier, span-aware decimals),
`factor_suffix` (`×10ⁿ`), `format_range`, `short_axis_name` (CTYPE → RA/Dec/Vel/…).

## 7. Tests

- `shwirl/tests/test_file_loading.py` (new) — extension detection, gzip read, HDU
  selection, squeeze, default axis selection, 2D promotion, truncation errors.
- `shwirl/tests/test_labels.py` (new) — offset formatting, span-aware precision,
  short names.
- `shwirl/tests/test_render.py` — opt-in GL test now sweeps all 7 methods × 5
  stretches and uses a texture-LUT colormap (`hsl`) as a regression guard.
- Status: **ruff clean; 45 headless tests pass; opt-in GL render test passes**
  (`SHWIRL_GL_TESTS=1`).

## 8. Housekeeping

- Diagnosed the SAMI test cube failure: the downloaded file is a 339-byte **HTML
  page**, not FITS (re-download needed) — recorded in `.claude/TODO.md`, not "fixed".
- `CLAUDE.md` moved to `.claude/CLAUDE.md` with a 1-line root `CLAUDE.md` importing
  it (`@.claude/CLAUDE.md`); docs updated to describe all of the above.
- `.claude/TODO.md` records deferred items: top-down view stops rendering the galaxy
  (bug); histogram widget + auto-range selection; 3D galaxy modelling (GBKFIT / a
  modern equivalent); SAMI re-download.

---

## Files

**New**
- `shwirl/fits_loader.py` (223 lines)
- `shwirl/labels.py` (97)
- `shwirl/tests/test_file_loading.py` (198)
- `shwirl/tests/test_labels.py` (74)
- `.claude/TODO.md`, `DEVELOPMENT_NOTES.md` (this file)

**Modified**
- `shwirl/shwirl.py` — robust load wiring, `AxisSelectionDialog`, `LoadedCube`,
  colorbar refresh/format/placement, info-panel overlay, dynamic-range combo,
  velocity/axis-label rework, `np.int` fix.
- `shwirl/shaders/render_volume.py` — `applyScale` stretches, endianness/`copy`
  fix, `texture2D_LUT` colormap sampler binding.
- `shwirl/shaders/axes.py` — rewritten `AxesVisual3D` (outline + triad).
- `shwirl/tests/test_render.py` — stretch/colormap sweep.
- `CLAUDE.md` → `.claude/CLAUDE.md` (+ root import shim).

## Verification

Loader checked against the repo's real cubes (`sample_cube.fits` 3D, the 2D
`J0135-41_*` images, a truncated THINGS partial). Full end-to-end render verified
on a live GL context (macOS / Apple Silicon): all 5 stretches, Moment 0 & Moment 1,
colormap switching, and the offset-formatted colorbar / triad / info panel.

## Platform / Linux

There is **no macOS-specific code** in the tree — no `sys.platform`/`darwin`
branches, no Cocoa calls; everything goes through PySide6, VisPy and portable GLSL.
Crucially, the render fixes above are **platform-agnostic correctness fixes** that
should help Linux too:

- `np.int→int` and the big-endian `np.asarray` fix are pure NumPy-2 issues,
  independent of OS.
- The `texture2D_LUT` colormap-sampler binding is the *correct* way to bind the LUT
  on any driver; it merely surfaced first on macOS because its core GL profile
  validates samplers strictly. Binding it properly is if anything *more* robust on
  Linux/Windows.
- The colorbar/axes work is Qt + VisPy scene code with no OS assumptions (the info
  panel is a `QLabel` child of the canvas' native widget — cross-platform).

**Expected to work on Linux, but not yet verified live.** CI already runs
import + `ruff` + headless tests on Linux (Py 3.10–3.12); the opt-in GL render test
is skipped there. What remains unverified on Linux is the **live OpenGL path** — GL
context/driver (Mesa/proprietary), the Qt platform plugin (xcb/wayland), and GLSL
acceptance under whatever GL version VisPy negotiates. Our custom shaders use
legacy-style GLSL (`varying`/`gl_FragColor`, `asinh` expanded by hand for GLSL 120),
which VisPy handles via its version pragma, but this should be confirmed on a real
Linux display. "Linux parity" remains a tracked item (`.claude/TODO.md`,
project memory); Windows later.

## Not done yet

- Nothing here is committed; intended as one or more commits on
  `macrocosme/modernize`. The large real cubes in the repo root / `test-data/`
  should be excluded from any commit; `environment.yml` (untracked, not authored
  here) needs a decision.
- Linux parity check and PyPI re-release (unchanged from prior status).
- Version still `0.2.0` (not bumped).

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**shwirl** is a standalone PyQt5 desktop application that visualises astronomical spectral data cubes with ray-tracing volume rendering. It renders on the GPU via OpenGL/GLSL, driven from Python through a **vendored copy of VisPy** (a Python→OpenGL binding). The scientific point of the tool is exploring *transfer functions* (voxel→colour/opacity mappings) and *GLSL shaders* for meaningful colouring of cubes — see Vohl, Fluke, Barnes & Hassan (2017), MNRAS.

## Run / build / test

Modernization is underway on branch `macrocosme/modernize` (Python 3.10+, PySide6,
`pyproject.toml`). Dev environment uses a `.venv` (created with `uv`):

```bash
uv venv --python 3.12 .venv
uv pip install -e ".[dev]"          # core + pytest/ruff; add ",filterbank" for .fil support
.venv/bin/shwirl                    # launch GUI (entry point → shwirl.shwirl:main)

ruff check .                        # lint (config in pyproject; excludes archive/)
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest   # headless tests
SHWIRL_GL_TESTS=1 .venv/bin/python -m pytest           # + opt-in GL render test (needs a display)
```

- Packaging is `pyproject.toml` (setuptools backend); the old `setup.py` is archived at
  `archive/setup.py.legacy`. Version is `0.2.0`.
- **VisPy is now an ordinary dependency (`vispy>=0.16`)** — the app has been un-vendored.
  The old bundled fork is archived at `archive/extern-vispy-fork/` (not deleted, not imported).
- Tests live in `shwirl/tests/` (shader-string generation + import smoke, always-on; plus an
  opt-in GL render test gated by `SHWIRL_GL_TESTS=1` since headless offscreen GL can segfault).
  CI is `.github/workflows/ci.yml` (ruff + pytest on macOS/Linux × Py3.10–3.12; GL test skipped).
- `blimpy` is an **optional** `[filterbank]` extra, imported lazily (only for `.fil` files).
  It still imports the removed `pkg_resources`, hence the `setuptools<81` pin in that extra.
- Docs are Sphinx (`docs/`, `make html`) published to readthedocs.

**Verified working:** launches on Python 3.12 / PySide6 / Apple Silicon with a live OpenGL
context; all 7 transfer-function shaders compile and render (synthetic cube).

## Architecture

Almost all real logic lives in **three files**.

- `shwirl/shwirl.py` (~1700 lines) — the entire application: `MainWindow` (Qt GUI, all control panels, event handlers), FITS/filterbank loading, and wiring of transfer-function/shader parameters to the renderer. Loading delegates to `fits_loader` (below) for FITS and (lazily) `blimpy.Waterfall` for filterbank data; both are wrapped in a small `LoadedCube` container (`data`/`header`/`axis_info`/`kind`) handed to the renderer. `AxisSelectionDialog` lets the user map axes when a cube is >3D.
- `shwirl/fits_loader.py` — pure (no-Qt, unit-tested) robust FITS loading: `open_fits` (tolerant of missing `SIMPLE`), `find_data_hdu` (skips empty primary HDUs, raises `FitsLoadError` on truncated/corrupt files), `describe_axes`/`squeeze_degenerate` (drops degenerate axes, e.g. Stokes=1), `default_selection`/`is_ambiguous`, and `build_cube` (reduces/reorders to a `(depth, y, x)` array; promotes 2D to a depth-1 slab). Handles plain **and gzipped** (`.fits.gz`) files.
- `shwirl/shaders/render_volume.py` (~1500 lines) — `RenderVolumeVisual`, a standalone subclass of VisPy's base `Visual` (it reimplements volume ray-casting rather than subclassing `VolumeVisual`). This is the core of the project: it holds the **custom GLSL fragment shaders** (as Python string templates, keyed in `frag_dict`) implementing the transfer functions. Modifying rendering behaviour almost always means editing the GLSL here. `RenderVolume = create_visual_node(RenderVolumeVisual)` is the scene-graph node used by the app. Intensity **dynamic-range stretches** (linear/log/sqrt/asinh/power, cf. Rector et al. 2007) live in the shared `FRAG_SHADER` `applyScale()` function, selected by the `u_color_scale` uniform via the `color_scale` property (`_SCALE_CODES`); every *intensity* `$cmap(...)` call is wrapped `$cmap(applyScale(...))`. Velocity (Moment 1) and RGB colourings keep their hue (`$cmap(loc.y)` unstretched), but there the stretch is applied to the **intensity that drives opacity/alpha** (e.g. `gl_FragColor.a = applyScale(maxval)`, `a2 = applyScale(val)*…`) so the dynamic-range control still works in those modes.
- `shwirl/shaders/axes.py` — `AxesVisual3D`, the 3D cube annotation. Revamped to be
  minimal/readable ("less is more"): just the cube outline + an **orientation triad** (three
  short coloured arrows + short axis names, rotates with the data). Numeric axis *ranges* are
  shown by a screen-fixed **info-panel** QLabel overlay pinned to the **lower-right** of the
  canvas, built in `shwirl.shwirl` (`Canvas3D._update_info_panel` / `_reposition_info_panel`,
  child of `Canvas3D.native`), not in the 3D scene. The old dense per-edge
  `vispy.scene.visuals.Axis` ticks were removed.
- `shwirl/labels.py` — pure, unit-tested numeric label formatting shared by the colorbar and
  axes: **offset multiplier** (`offset_format`/`factor_suffix` → factor out a common `×10ⁿ`,
  span-aware decimals so tiny RA/Dec spans stay distinguishable), `format_range`, and
  `short_axis_name` (CTYPE → RA/Dec/Vel/…). The colorbar (`Canvas3D._apply_colorbar`) feeds
  vispy already-scaled short `clim` values (vispy regenerates tick text as `str(clim)` every
  draw, so overriding `ticks[i].text` does not stick) and puts the `×10ⁿ` in the label; it also
  refreshes cmap/clim even while hidden so it stays in sync with the volume colormap. The bar
  lives in the left column but is created with vispy orientation `'right'` so its label/ticks
  face the canvas *interior* (otherwise `'left'` pushes them off the canvas edge); `ColorBarVisual.text_padding_factor` is bumped so the rotated title clears the bar.
- `shwirl/shaders/edge_valley.glsl` — standalone GLSL snippet.
- `shwirl/api.py` — **scriptable, GUI-free Python API**: `Renderer` (offscreen render →
  numpy image / `save()` PNG / `save_movie()` GIF+MP4 fly-arounds / `widget()` ipywidgets
  panel / `canvas()` live jupyter_rfb view) + `demo_cube()` synthetic data. Lazy top-level
  exports via `shwirl.__getattr__` (`from shwirl import Renderer, demo_cube`). Accepts FITS
  paths (via `fits_loader`), 3D arrays, or `LoadedCube`s; same data prep as the GUI. Gotchas
  learned: must pin `app="pyside6"` on the offscreen `SceneCanvas` (in a Jupyter kernel vispy
  auto-picks jupyter_rfb), and must call `camera.set_range()` after adding the volume (else
  the default camera is zoomed into a corner → flat-plane renders). `canvas().render()`
  returns physical (HiDPI-scaled) pixels. Extra: `pip install shwirl[notebook]`
  (ipywidgets+imageio); `imageio-ffmpeg` for MP4; `jupyter_rfb` for live canvas. Example:
  `examples/shwirl_api_demo.ipynb` (executed outputs embedded; rebuild by re-running it).

Data flow: `MainWindow` builds a VisPy `SceneCanvas`, instantiates `RenderVolume` with the loaded cube, and GUI controls push parameters (colormap, thresholds, transfer-function selection, moments) into the shader uniforms, which re-render on the GPU.

Known latent bug: `get_interpolation_fun()` at the end of `render_volume.py` is infinite self-recursion (dead code, unused — left in place per the no-delete rule).

## Modernization status (branch `macrocosme/modernize`)

**Done:** pyproject/CI/tests/hygiene; Python 3.10+ cleanup (dropped `__future__`/`six`/PyQt4
fallback/debug prints); PyQt5→**PySide6** migration; fixed the broken entry point; blimpy made
an optional lazy `[filterbank]` extra; **un-vendored VisPy** (now `vispy>=0.16`, old fork
archived) — resolving the Qt6/`QGLWidget` blocker. App launches and renders all shaders on
macOS/Apple Silicon. **Robust FITS loading** (`fits_loader.py`): plain/gzipped, arbitrary HDU,
2D/3D/4D cubes with an axis-selection dialog for >3D, friendly errors for truncated files.
Fixed three NumPy-2/modern-VisPy render blockers that stopped real cubes drawing:
`np.int`→`int` in the velocity-limit code; big-endian FITS copy (`np.array(copy=False)`→
`np.asarray`); colorbar `label_str`→`label.text`; and the colormap LUT sampler
(`shared_program['texture2D_LUT'] = cmap.texture_lut()`, was missing → GL sampler-unit
collision for texture-based colormaps like `hsl`). Real FITS cubes now render (verified with a
live GL context).

**Linux (headless) verified 2026-07-09:** branch pushed; first-ever CI run surfaced two
issues, both fixed — ubuntu runners need Qt6 system libs (`libegl1 libgl1 libxkbcommon*
libdbus-1-3 libfontconfig1 libglib2.0-0 libopengl0`) via an apt step even for the offscreen
platform, and newer ruff lints `.ipynb` by default (now excluded). **CI fully green:
lint + ubuntu/macos × Py3.10–3.12.**

**Remaining:**
- **Linux live-GL check:** only the opt-in GL render path (`SHWIRL_GL_TESTS=1`) is unverified
  on a real Linux display/GPU. Windows later.
- **Phase 5:** PyPI re-release (bump/tag, build sdist+wheel, publish); PR modernize→master.
- Optional: refresh Sphinx docs/readthedocs; fix the `get_interpolation_fun` dead code.

## Repo conventions

- Do not delete files (see global instructions); move unwanted files to `trash/` or `archive/`.
- Branches are prefixed `macrocosme/`.

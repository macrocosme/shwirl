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

- `shwirl/shwirl.py` (~1700 lines) — the entire application: `MainWindow` (Qt GUI, all control panels, event handlers), FITS/filterbank loading, and wiring of transfer-function/shader parameters to the renderer. Data loading uses `astropy.io.fits` for FITS and (lazily) `blimpy.Waterfall` for filterbank data.
- `shwirl/shaders/render_volume.py` (~1500 lines) — `RenderVolumeVisual`, a standalone subclass of VisPy's base `Visual` (it reimplements volume ray-casting rather than subclassing `VolumeVisual`). This is the core of the project: it holds the **custom GLSL fragment shaders** (as Python string templates, keyed in `frag_dict`) implementing the transfer functions. Modifying rendering behaviour almost always means editing the GLSL here. `RenderVolume = create_visual_node(RenderVolumeVisual)` is the scene-graph node used by the app.
- `shwirl/shaders/axes.py` — `AxesVisual3D`, 3D axis rendering.
- `shwirl/shaders/edge_valley.glsl` — standalone GLSL snippet.

Data flow: `MainWindow` builds a VisPy `SceneCanvas`, instantiates `RenderVolume` with the loaded cube, and GUI controls push parameters (colormap, thresholds, transfer-function selection, moments) into the shader uniforms, which re-render on the GPU.

Known latent bug: `get_interpolation_fun()` at the end of `render_volume.py` is infinite self-recursion (dead code, unused — left in place per the no-delete rule).

## Modernization status (branch `macrocosme/modernize`)

**Done:** pyproject/CI/tests/hygiene; Python 3.10+ cleanup (dropped `__future__`/`six`/PyQt4
fallback/debug prints); PyQt5→**PySide6** migration; fixed the broken entry point; blimpy made
an optional lazy `[filterbank]` extra; **un-vendored VisPy** (now `vispy>=0.16`, old fork
archived) — resolving the Qt6/`QGLWidget` blocker. App launches and renders all shaders on
macOS/Apple Silicon.

**Remaining:**
- **Linux parity:** prep/verify on Linux (CI covers import+lint+headless tests; GL render is
  opt-in). Windows later.
- **Phase 5:** PyPI re-release (bump/tag, build sdist+wheel, publish).
- Optional: refresh Sphinx docs/readthedocs; fix the `get_interpolation_fun` dead code.

## Repo conventions

- Do not delete files (see global instructions); move unwanted files to `trash/` or `archive/`.
- Branches are prefixed `macrocosme/`.

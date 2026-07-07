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

ruff check .                        # lint (config in pyproject; excludes shwirl/extern)
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest   # headless tests
```

- Packaging is `pyproject.toml` (setuptools backend); the old `setup.py` is archived at
  `archive/setup.py.legacy`. Version is `0.2.0`.
- Tests live in `shwirl/tests/` (shader generation + import smoke tests). CI is
  `.github/workflows/ci.yml` (ruff + pytest on macOS/Linux × Py3.10–3.12).
- `blimpy` is an **optional** `[filterbank]` extra, imported lazily (only for `.fil` files).
  It still imports the removed `pkg_resources`, hence the `setuptools<81` pin in that extra.
- Docs are Sphinx (`docs/`, `make html`) published to readthedocs.

### ⚠️ Known blocker (Phase 3, open decision)
The app **imports** cleanly on Py3.12/PySide6/Apple Silicon but does **not launch yet**:
vendored VisPy 0.5.0's Qt backend (`shwirl/extern/vispy/app/backends/_qt.py`) is built on
`QGLWidget`/`QGLFormat` from Qt's old `QtOpenGL` module, both **removed in Qt6/PySide6**
(replaced by `QOpenGLWidget` + `QSurfaceFormat`). Also, VisPy 0.5.0's backend registry has
no PySide6/PyQt6 entry. Resolving this is the un-vendor-vs-port-the-fork decision.

## Architecture

Almost all real logic lives in **three files**; everything else under `shwirl/extern/` is vendored third-party code.

- `shwirl/shwirl.py` (~1700 lines) — the entire application: `MainWindow` (Qt GUI, all control panels, event handlers), FITS/filterbank loading, and wiring of transfer-function/shader parameters to the renderer. Data loading uses `astropy.io.fits` for FITS and `blimpy.Waterfall` for filterbank data.
- `shwirl/shaders/render_volume.py` (~1500 lines) — `RenderVolumeVisual`, a subclass of VisPy's `VolumeVisual`. This is the core of the project: it holds the **custom GLSL fragment shaders** (as Python string templates) implementing the transfer functions and ray-tracing colouring. Modifying rendering behaviour almost always means editing the GLSL here.
- `shwirl/shaders/axes.py` — `AxesVisual3D`, 3D axis rendering.
- `shwirl/shaders/edge_valley.glsl` — standalone GLSL snippet.

Data flow: `MainWindow` builds a VisPy `SceneCanvas`, instantiates `RenderVolumeVisual` with the loaded cube, and GUI controls push parameters (colormap, thresholds, transfer-function selection, moments) into the shader uniforms, which re-render on the GPU.

### Vendored VisPy — important

`shwirl/extern/vispy/` is a **patched fork of VisPy 0.5.0.dev0 (~370 files, 6 MB), not pip-installed upstream.** Imports throughout the code are relative (`from .extern.vispy import app, scene, io`). Current upstream is 0.14.x. After the initial vendoring, only 2 source files were patched by the author (`visuals/colorbar.py`, `visuals/isocurve.py`); the custom rendering work lives *outside* the fork in `shwirl/shaders/`. Modernization has since added Py3.12/arm64 fixes inside the fork (`ext/cocoapy.py`, `geometry/torusknot.py`). Do not casually "upgrade" individual files inside it; changes there interact with the custom shaders.

## Modernization status (branch `macrocosme/modernize`)

**Done:** pyproject/CI/tests/hygiene; Python 3.10+ cleanup (dropped `__future__`/`six`/PyQt4
fallback/debug prints); PyQt5→**PySide6** migration; fixed the broken entry point; blimpy made
an optional lazy `[filterbank]` extra; vendored-vispy fixes so it **imports** on Py3.12 + Apple
Silicon (arm64 `_stret` guards, `math.gcd`).

**Remaining:**
- **Phase 3 (blocked on decision):** the VisPy↔Qt6 OpenGL gap — see "Known blocker" above.
  Two paths: (A) port the fork's `_qt.py` backend to Qt6 `QOpenGLWidget` + add `_pyside6.py`;
  (B) un-vendor onto modern VisPy 0.14 (native PySide6) and forward-port the custom
  `RenderVolumeVisual`/`AxesVisual3D`. A fast fallback is reverting the Qt choice to PyQt5,
  whose `QtOpenGL.QGLWidget` still exists (but Qt5 is EOL / QGLWidget deprecated).
- **Phase 5:** PyPI re-release once it launches.

## Repo conventions

- Do not delete files (see global instructions); move unwanted files to `trash/` or `archive/`.
- Branches are prefixed `macrocosme/`.

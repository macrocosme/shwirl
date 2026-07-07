# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**shwirl** is a standalone PyQt5 desktop application that visualises astronomical spectral data cubes with ray-tracing volume rendering. It renders on the GPU via OpenGL/GLSL, driven from Python through a **vendored copy of VisPy** (a Python→OpenGL binding). The scientific point of the tool is exploring *transfer functions* (voxel→colour/opacity mappings) and *GLSL shaders* for meaningful colouring of cubes — see Vohl, Fluke, Barnes & Hassan (2017), MNRAS.

## Run / build / test

```bash
pip install -e .          # editable install (setup.py based; no pyproject.toml)
shwirl                    # launch GUI (console_scripts entry point → shwirl.shwirl:main)
python main.py            # NOTE: currently broken — see Known breakage below
```

- **No test suite** exists (`shwirl/tests/__init__.py` is empty) and **no CI/CD**.
- **No linter/formatter** configured.
- Docs are Sphinx (`docs/`, `make html`) published to readthedocs.

## Architecture

Almost all real logic lives in **three files**; everything else under `shwirl/extern/` is vendored third-party code.

- `shwirl/shwirl.py` (~1700 lines) — the entire application: `MainWindow` (Qt GUI, all control panels, event handlers), FITS/filterbank loading, and wiring of transfer-function/shader parameters to the renderer. Data loading uses `astropy.io.fits` for FITS and `blimpy.Waterfall` for filterbank data.
- `shwirl/shaders/render_volume.py` (~1500 lines) — `RenderVolumeVisual`, a subclass of VisPy's `VolumeVisual`. This is the core of the project: it holds the **custom GLSL fragment shaders** (as Python string templates) implementing the transfer functions and ray-tracing colouring. Modifying rendering behaviour almost always means editing the GLSL here.
- `shwirl/shaders/axes.py` — `AxesVisual3D`, 3D axis rendering.
- `shwirl/shaders/edge_valley.glsl` — standalone GLSL snippet.

Data flow: `MainWindow` builds a VisPy `SceneCanvas`, instantiates `RenderVolumeVisual` with the loaded cube, and GUI controls push parameters (colormap, thresholds, transfer-function selection, moments) into the shader uniforms, which re-render on the GPU.

### Vendored VisPy — important

`shwirl/extern/vispy/` is a **patched fork of VisPy (~370 files, 6 MB), not pip-installed upstream.** Imports throughout the code are relative (`from .extern.vispy import app, scene, io`). `setup.py` enumerates every vendored subpackage by hand. Treat this as the biggest modernization liability: it pins the project to an old OpenGL-era VisPy. Do not casually "upgrade" individual files inside it; changes there interact with the custom shaders.

## Legacy / modernization context

This code was last touched ~7 years ago and straddles Python 2/3:
- `from __future__ import division`, a `six` dependency, and a `PyQt4` import fallback.
- `setup.py` classifiers still advertise Python 2.7–3.6; packaging is legacy setuptools (no `pyproject.toml`).
- Stray `print(...)` debug statements remain in `shwirl.py`.

### Known breakage
- `shwirl/__init__.py` defines `main()` as `from shwirl import main; main()` — a self-referential no-op. `main.py` at repo root calls `shwirl.main()` and will not work. The functioning entry point is `shwirl.shwirl:main` (the `shwirl` console script).
- `blimpy` is imported by `shwirl.py` but is **missing from `install_requires`** (which lists scipy, numpy, astropy, PyOpenGL, six).
- OpenGL is deprecated on macOS; runtime viability on modern Linux/macOS is unverified.

## Repo conventions

- Do not delete files (see global instructions); move unwanted files to `trash/` or `archive/`.
- Branches are prefixed `macrocosme/`.

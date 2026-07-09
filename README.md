[![CI](https://github.com/macrocosme/shwirl/actions/workflows/ci.yml/badge.svg?branch=macrocosme/modernize)](https://github.com/macrocosme/shwirl/actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/shwirl/badge/?version=latest)](https://shwirl.readthedocs.io/en/latest/)
[![ascl](https://img.shields.io/badge/ascl-1704.003-blue.svg?colorB=262255)](http://ascl.net/1704.003)
[![astropy](https://img.shields.io/badge/powered%20by-AstroPy-orange.svg?style=flat)](https://www.astropy.org/)

About shwirl
=============

**shwirl** is a custom standalone Python program to visualise spectral data cubes with ray-tracing volume rendering.
The program has been developed to investigate transfer functions and graphics shaders as enablers for
scientific visualisation of astronomical data. Details about transfer functions and shaders developed and implemented in
**shwirl** can be found in a full length article by [Vohl, Fluke, Barnes & Hassan (2017)](https://academic.oup.com/mnras/article-lookup/doi/10.1093/mnras/stx1676).

A transfer function is an arbitrary function that combines volumetric elements (or voxels) to set the colour,
intensity, or transparency level of each pixel in the final image. A graphics shader is an algorithmic kernel
used to compute several properties of the final image such as colour, depth, and/or transparency.
Shaders are particularly suited to computing transfer functions, and are an integral part of the graphics
pipeline on Graphics Processing Units.

The program utilises [Astropy](https://www.astropy.org) to handle FITS files and World
Coordinate System, [Qt](https://www.qt.io) (via [PySide6](https://doc.qt.io/qtforpython-6/))
for the user interface, and [VisPy](https://vispy.org), an object-oriented Python
visualisation library binding onto OpenGL. We implemented the algorithms in the fragment
shader using the GLSL language.

Features
--------
- **Desktop app**: interactive ray-traced volume rendering of spectral cubes with seven
  transfer functions (mip, lmip, iso, avip, minip, translucent, additive), colour by
  intensity or velocity (moment-style), smoothing/filtering on the GPU.
- **Robust FITS loading**: plain or gzipped (`.fits.gz`), 2D/3D/4D data, automatic HDU and
  axis-role detection with an axis-selection dialog for higher-dimensional cubes, friendly
  errors for truncated files.
- **Dynamic-range stretches**: linear, logarithmic, square root, asinh, power
  (cf. [Rector et al. 2007](https://ui.adsabs.harvard.edu/abs/2007AJ....133..598R/abstract)).
- **Scriptable Python API + Jupyter**: render cubes headlessly from scripts and notebooks —
  numpy images, publication PNGs, 360° fly-around movies (GIF/MP4), interactive widget.

```python
from shwirl import Renderer

r = Renderer("my_cube.fits")            # also .fits.gz, numpy arrays
r.method, r.stretch, r.cmap = "mip", "asinh", "hsl"
r.save("cube.png", azimuth=35, elevation=20)
r.save_movie("spin.gif")                # fly-around animation
r.widget()                              # sliders in a notebook
```

See [`examples/shwirl_api_demo.ipynb`](examples/shwirl_api_demo.ipynb) for a walkthrough.

Status
------
shwirl (2017) has been modernised (2026) to Python ≥ 3.10, PySide6/Qt6, current
VisPy/NumPy/Astropy. Verified: macOS (Apple Silicon, live OpenGL) and Linux
(continuous integration, headless). Windows untested since modernisation.
A fresh PyPI release is on its way; meanwhile install from source (below).

Documentation
-------------
Documentation can be found at [readthedocs](https://shwirl.readthedocs.io/en/latest/)
*(currently being refreshed for the modernised version)*.

Installation
------------
Requires Python ≥ 3.10. All dependencies (PySide6, VisPy, Astropy, NumPy, SciPy) are
installed automatically:

```bash
git clone https://github.com/macrocosme/shwirl.git
cd shwirl
pip install -e .                # add ".[notebook]" for the Jupyter/API extras
shwirl                          # launch the GUI
```

Or with conda/micromamba: `micromamba create -f environment.yml`.

Optional extras: `[notebook]` (ipywidgets + imageio for the API/widget/movies),
`[filterbank]` (blimpy, for SigProc `.fil` files); `imageio-ffmpeg` for MP4 export,
`jupyter_rfb` for a live in-notebook canvas.

> Note: the version currently on PyPI (`pip install shwirl`) is the legacy 2017
> release and predates the modernisation — prefer the source install above until
> the new release lands.

Issues, requests and general inquiries
--------------------------------------
Please list issues, feature requests and/or general inquiries by creating a [new issue](https://github.com/macrocosme/shwirl/issues).

Want to contribute?
-------------------
Pull requests are welcomed. Development setup and tests:

```bash
pip install -e ".[dev]"
ruff check .                            # lint
QT_QPA_PLATFORM=offscreen pytest        # headless test suite
SHWIRL_GL_TESTS=1 pytest                # + opt-in GL render tests (needs a display)
```

License
-------
shwirl is licensed under the terms of the (new) BSD license. 
A copy of the license is included within this repository.

Copyright
---------
Copyright (c) 2017-2026, Dany Vohl
All rights reserved.


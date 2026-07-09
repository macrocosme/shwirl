"""Scriptable, GUI-free rendering API for shwirl.

Volume-render spectral cubes from scripts and notebooks using the same GLSL
transfer functions as the desktop app::

    from shwirl import Renderer, demo_cube

    r = Renderer("my_cube.fits")        # or Renderer(demo_cube())
    r.method, r.stretch, r.cmap = "mip", "asinh", "hsl"
    img = r.render(azimuth=30, elevation=20)   # (H, W, 4) uint8
    r.save("cube.png")
    r.save_movie("spin.gif")                    # fly-around animation
    r.widget()                                  # ipywidgets UI (notebook)

Rendering happens offscreen through vispy (Qt backend); no shwirl GUI is
created. Optional niceties: ``pip install shwirl[notebook]`` (ipywidgets,
imageio) for ``widget()``/``save_movie()``; ``imageio-ffmpeg`` for MP4;
``jupyter_rfb`` for a live, mouse-rotatable notebook canvas (``canvas()``).
"""

from pathlib import Path

import numpy as np

from .fits_loader import load_fits_cube

# Public parameter values (validated in the setters below).
METHODS = ("mip", "lmip", "iso", "avip", "minip", "translucent2", "additive")
STRETCHES = ("linear", "log", "sqrt", "asinh", "power")
COLOR_METHODS = ("Moment 0", "Moment 1", "Sigmas", "rgb_cube")

_MAX_TEXTURE_EXTENT = 2048  # same GPU-texture cap as the GUI


def demo_cube(shape=(64, 96, 96), n_blobs=5, seed=0):
    """Synthetic spectral cube: Gaussian blobs drifting across channels + noise.

    Returns a float32 array of ``shape`` (channels, y, x) — a stand-in for an
    HI cube so examples run without downloading data.
    """
    rng = np.random.default_rng(seed)
    nz, ny, nx = shape
    z, y, x = np.mgrid[0:nz, 0:ny, 0:nx].astype(np.float32)
    cube = rng.normal(0.0, 0.02, shape).astype(np.float32)
    for _ in range(n_blobs):
        cx, cy = rng.uniform(0.2, 0.8) * nx, rng.uniform(0.2, 0.8) * ny
        cz = rng.uniform(0.25, 0.75) * nz
        drift = rng.uniform(-0.15, 0.15) * nx   # velocity gradient across channels
        sx = rng.uniform(0.04, 0.10) * nx
        sz = rng.uniform(0.10, 0.25) * nz
        amp = rng.uniform(0.5, 1.0)
        xc = cx + drift * (z - cz) / nz
        cube += amp * np.exp(-(((x - xc) ** 2 + (y - cy) ** 2) / (2 * sx ** 2)
                               + (z - cz) ** 2 / (2 * sz ** 2)))
    return cube


def _ensure_qt_app():
    """Create (or fetch) the Qt application vispy's default backend needs."""
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


class Renderer:
    """Offscreen volume renderer around shwirl's ``RenderVolume`` visual.

    Parameters
    ----------
    source : str | pathlib.Path | numpy.ndarray | LoadedCube
        FITS file path (plain or .gz; loaded via :mod:`shwirl.fits_loader`),
        a 3D array in (channels/z, y, x) order, or an existing ``LoadedCube``.
    size : tuple(int, int)
        Canvas (width, height) in pixels.
    bgcolor : str
        Canvas background colour.
    """

    def __init__(self, source, size=(800, 600), bgcolor="#404040"):
        data, self._axis_info = self._load(source)
        # Same orientation prep + texture cap as the GUI (Canvas3D.set_volume_scene).
        data = data[:_MAX_TEXTURE_EXTENT, :_MAX_TEXTURE_EXTENT, :_MAX_TEXTURE_EXTENT]
        self._data = np.flipud(np.rollaxis(data, 1))

        _ensure_qt_app()
        from vispy import scene

        from .shaders import RenderVolume

        # Pin the Qt backend: inside a Jupyter kernel vispy would otherwise
        # auto-select jupyter_rfb for this *offscreen* canvas too.
        self._canvas = scene.SceneCanvas(keys=None, size=size, show=False,
                                         bgcolor=bgcolor, app="pyside6")
        self._view = self._canvas.central_widget.add_view()
        self._view.camera = scene.cameras.TurntableCamera(fov=60)
        self._volume = RenderVolume(self._data, parent=self._view.scene,
                                    threshold=0.225, emulate_texture=False)
        # Frame the whole cube (the camera otherwise stays at its default,
        # zoomed into a corner of the data volume).
        self._view.camera.set_range()
        self._method = "mip"
        self._stretch = "linear"
        self._cmap = "hsl"
        self._color_method = "Moment 0"
        self.cmap = self._cmap  # bind the colormap LUT texture

    # -- loading ------------------------------------------------------------
    @staticmethod
    def _load(source):
        if isinstance(source, np.ndarray):
            if source.ndim != 3:
                raise ValueError(
                    f"array source must be 3D (z, y, x); got ndim={source.ndim}")
            return np.asarray(source, dtype="float32"), None
        if isinstance(source, (str, Path)):
            arr, _header, axis_info, _axes, _sel = load_fits_cube(str(source))
            return arr, axis_info
        # LoadedCube-like (duck-typed: .data + .axis_info)
        data = getattr(source, "data", None)
        if data is not None and getattr(data, "ndim", 0) == 3:
            return np.asarray(data, dtype="float32"), getattr(source, "axis_info", None)
        raise TypeError(
            "source must be a FITS path, a 3D numpy array, or a LoadedCube; "
            f"got {type(source).__name__}")

    # -- rendering parameters -------------------------------------------------
    @property
    def method(self):
        """Transfer function: one of METHODS."""
        return self._method

    @method.setter
    def method(self, value):
        if value not in METHODS:
            raise ValueError(f"method must be one of {METHODS}; got {value!r}")
        self._method = value
        self._volume.method = value
        # Assigning .frag wholesale resets stretch uniforms; re-apply.
        self._volume.color_scale = self._stretch

    @property
    def stretch(self):
        """Intensity dynamic-range stretch: one of STRETCHES."""
        return self._stretch

    @stretch.setter
    def stretch(self, value):
        if value not in STRETCHES:
            raise ValueError(f"stretch must be one of {STRETCHES}; got {value!r}")
        self._stretch = value
        self._volume.color_scale = value

    @property
    def cmap(self):
        """Colormap name (any vispy colormap, e.g. 'hsl', 'hot', 'viridis')."""
        return self._cmap

    @cmap.setter
    def cmap(self, value):
        self._volume.cmap = value  # vispy raises KeyError for unknown names
        self._cmap = value

    @property
    def color_method(self):
        """Colouring mode: one of COLOR_METHODS (intensity vs velocity, ...)."""
        return self._color_method

    @color_method.setter
    def color_method(self, value):
        if value not in COLOR_METHODS:
            raise ValueError(
                f"color_method must be one of {COLOR_METHODS}; got {value!r}")
        self._color_method = value
        self._volume.color_method = value

    @property
    def threshold(self):
        """Normalised [0, 1] threshold used by 'lmip' and 'iso'."""
        return self._volume.threshold

    @threshold.setter
    def threshold(self, value):
        self._volume.threshold = float(value)

    @property
    def density_factor(self):
        """Density regulator used by 'avip' and 'translucent2'."""
        return self._volume.density_factor

    @density_factor.setter
    def density_factor(self, value):
        self._volume.density_factor = float(value)

    @property
    def clim(self):
        """(min, max) data values mapped to the colormap (read-only)."""
        return tuple(self._volume.clim)

    @property
    def axis_info(self):
        """Per-display-axis WCS info from the FITS header (None for arrays)."""
        return self._axis_info

    # -- rendering ------------------------------------------------------------
    def render(self, azimuth=None, elevation=None, distance=None, fov=None,
               size=None):
        """Render offscreen and return an (H, W, 4) uint8 RGBA image.

        Camera arguments are optional; unspecified ones keep their value, so
        successive calls compose (e.g. only sweep ``azimuth`` for a movie).
        ``size`` is in logical pixels; on HiDPI screens the returned image is
        scaled by the device pixel ratio (e.g. 2x on Retina).
        """
        cam = self._view.camera
        if azimuth is not None:
            cam.azimuth = azimuth
        if elevation is not None:
            cam.elevation = elevation
        if distance is not None:
            cam.distance = distance
        if fov is not None:
            cam.fov = fov
        if size is not None and tuple(size) != tuple(self._canvas.size):
            self._canvas.size = tuple(size)
        return np.asarray(self._canvas.render())

    def save(self, path, **camera):
        """Render and write a PNG. ``**camera`` as in :meth:`render`."""
        from vispy.io import write_png
        write_png(str(path), self.render(**camera))
        return Path(path)

    def save_movie(self, path, n_frames=72, fps=20, elevation=None, **camera):
        """Write a 360° azimuth fly-around as GIF or MP4 (by file extension).

        GIF needs ``imageio`` (``pip install shwirl[notebook]``); MP4 also
        needs ``imageio-ffmpeg``.
        """
        try:
            import imageio.v2 as imageio
        except ImportError as exc:
            raise ImportError(
                "save_movie requires imageio: pip install 'shwirl[notebook]'"
            ) from exc

        suffix = Path(path).suffix.lower()
        if suffix not in (".gif", ".mp4"):
            raise ValueError(f"movie format must be .gif or .mp4; got {suffix!r}")

        start = self._view.camera.azimuth
        frames = []
        for i in range(n_frames):
            frames.append(self.render(azimuth=start + 360.0 * i / n_frames,
                                      elevation=elevation, **camera))
        self._view.camera.azimuth = start

        if suffix == ".gif":
            imageio.mimsave(str(path), frames, duration=1000.0 / fps, loop=0)
        else:
            try:
                writer = imageio.get_writer(str(path), fps=fps)
            except Exception as exc:
                raise ImportError(
                    "MP4 output needs imageio-ffmpeg: pip install imageio-ffmpeg"
                ) from exc
            with writer:
                for frame in frames:
                    writer.append_data(frame[..., :3])
        return Path(path)

    # -- notebook helpers -------------------------------------------------------
    def widget(self):
        """ipywidgets control panel: dropdowns + sliders re-render inline.

        Requires ``pip install shwirl[notebook]``.
        """
        try:
            import imageio.v3 as iio
            import ipywidgets as w
        except ImportError as exc:
            raise ImportError(
                "widget() requires ipywidgets and imageio: "
                "pip install 'shwirl[notebook]'") from exc
        from vispy.color import get_colormaps

        image = w.Image(format="png")

        def redraw(method, cmap, stretch, color_method, azimuth, elevation,
                   threshold, density_factor):
            self.method = method
            self.cmap = cmap
            self.stretch = stretch
            self.color_method = color_method
            self.threshold = threshold
            self.density_factor = density_factor
            frame = self.render(azimuth=azimuth, elevation=elevation)
            image.value = iio.imwrite("<bytes>", frame, extension=".png")

        controls = w.interactive(
            redraw,
            method=w.Dropdown(options=METHODS, value=self.method),
            cmap=w.Dropdown(options=sorted(get_colormaps(), key=str.lower),
                            value=self.cmap),
            stretch=w.Dropdown(options=STRETCHES, value=self.stretch),
            color_method=w.Dropdown(options=COLOR_METHODS,
                                    value=self.color_method),
            azimuth=w.FloatSlider(min=-180, max=180, step=2,
                                  value=self._view.camera.azimuth),
            elevation=w.FloatSlider(min=-90, max=90, step=2,
                                    value=self._view.camera.elevation),
            threshold=w.FloatSlider(min=0.0, max=1.0, step=0.01,
                                    value=float(self.threshold)),
            density_factor=w.FloatSlider(min=0.0, max=1.0, step=0.005,
                                         value=float(self.density_factor)),
        )
        controls.update()  # first draw
        return w.HBox([w.VBox(controls.children[:-1]), image])

    def canvas(self, size=None):
        """Live, mouse-rotatable canvas in a notebook (needs ``jupyter_rfb``).

        Builds a fresh scene on vispy's jupyter backend with the same data and
        current parameters; returns the canvas (display it as the cell result).
        """
        try:
            import jupyter_rfb  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "canvas() requires jupyter_rfb: pip install jupyter_rfb") from exc
        from vispy import scene

        from .shaders import RenderVolume

        canvas = scene.SceneCanvas(keys=None, size=size or self._canvas.size,
                                   bgcolor=self._canvas.bgcolor,
                                   app="jupyter_rfb")
        view = canvas.central_widget.add_view()
        view.camera = scene.cameras.TurntableCamera(
            fov=self._view.camera.fov,
            azimuth=self._view.camera.azimuth,
            elevation=self._view.camera.elevation)
        volume = RenderVolume(self._data, parent=view.scene,
                              threshold=float(self.threshold),
                              emulate_texture=False)
        view.camera.set_range()
        volume.method = self.method
        volume.cmap = self.cmap
        volume.color_scale = self.stretch
        volume.color_method = self.color_method
        volume.density_factor = float(self.density_factor)
        return canvas

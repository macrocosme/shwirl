"""Tests for the scriptable rendering API (shwirl.api).

Parameter validation and data handling are always-on. Anything that touches a
real GL context (render/save/movie) is gated behind SHWIRL_GL_TESTS=1, matching
test_render.py.
"""
import os

import numpy as np
import pytest

from shwirl.api import METHODS, STRETCHES, demo_cube
from shwirl.fits_loader import FitsLoadError

needs_gl = pytest.mark.skipif(
    os.environ.get("SHWIRL_GL_TESTS") != "1",
    reason="GL render test is opt-in; set SHWIRL_GL_TESTS=1 (needs a real GL context)",
)


def test_demo_cube_shape_and_signal():
    cube = demo_cube(shape=(16, 24, 20), n_blobs=3, seed=1)
    assert cube.shape == (16, 24, 20)
    assert cube.dtype == np.float32
    # blobs must rise well above the noise floor
    assert cube.max() > 5 * cube.std()


def test_lazy_top_level_exports():
    import shwirl
    assert shwirl.Renderer is not None
    assert shwirl.demo_cube is demo_cube
    with pytest.raises(AttributeError):
        shwirl.no_such_attribute  # noqa: B018


# ---------------------------------------------------------------------------
# GL-gated: construction and rendering need a context
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def renderer():
    from shwirl.api import Renderer
    return Renderer(demo_cube(shape=(24, 32, 32)), size=(160, 120))


@needs_gl
def test_source_validation():
    from shwirl.api import Renderer
    with pytest.raises(ValueError):
        Renderer(np.zeros((4, 4), dtype=np.float32))  # 2D array
    with pytest.raises(TypeError):
        Renderer(12345)
    with pytest.raises(FitsLoadError):
        Renderer("/no/such/cube.fits")


@needs_gl
def test_param_validation(renderer):
    with pytest.raises(ValueError):
        renderer.method = "not-a-method"
    with pytest.raises(ValueError):
        renderer.stretch = "not-a-stretch"
    with pytest.raises(ValueError):
        renderer.color_method = "not-a-mode"


@needs_gl
def test_render_shape_and_content(renderer):
    img = renderer.render(azimuth=30, elevation=20)
    assert img.dtype == np.uint8
    assert img.ndim == 3 and img.shape[2] == 4
    # canvas size is in logical pixels; HiDPI screens render at an integer
    # multiple (device pixel ratio), so check the aspect ratio instead.
    assert img.shape[1] / img.shape[0] == pytest.approx(160 / 120)
    assert img[..., :3].std() > 1  # not a blank frame


@needs_gl
def test_camera_changes_pixels(renderer):
    a = renderer.render(azimuth=0, elevation=10)
    b = renderer.render(azimuth=90, elevation=10)
    assert not np.array_equal(a, b)


@needs_gl
def test_all_methods_and_stretches_render(renderer):
    for method in METHODS:
        renderer.method = method
        renderer.render()
    renderer.method = "mip"
    for stretch in STRETCHES:
        renderer.stretch = stretch
        renderer.render()
    renderer.stretch = "linear"


@needs_gl
def test_save_png(renderer, tmp_path):
    out = renderer.save(tmp_path / "frame.png", azimuth=45)
    assert out.exists() and out.stat().st_size > 1000


@needs_gl
def test_save_movie_gif(renderer, tmp_path):
    imageio = pytest.importorskip("imageio.v2")
    out = renderer.save_movie(tmp_path / "spin.gif", n_frames=6, fps=10)
    assert out.exists()
    frames = imageio.mimread(out)
    assert len(frames) == 6


@needs_gl
def test_save_movie_bad_extension(renderer, tmp_path):
    pytest.importorskip("imageio.v2")
    with pytest.raises(ValueError):
        renderer.save_movie(tmp_path / "spin.avi")

"""End-to-end render test for the custom RenderVolume shaders.

This exercises the real GPU pipeline (Texture3D upload + GLSL compile + draw),
so it needs a working OpenGL context. A headless offscreen stack can *crash*
(segfault) rather than raise when it tries to render, which would take down the
whole test process — so this test is opt-in: set ``SHWIRL_GL_TESTS=1`` to run it
on a machine with a real display/GPU. CI leaves it unset and skips.
"""
import os

import numpy as np
import pytest

METHODS = ["mip", "lmip", "iso", "avip", "minip", "translucent2", "additive"]

pytestmark = pytest.mark.skipif(
    os.environ.get("SHWIRL_GL_TESTS") != "1",
    reason="GL render test is opt-in; set SHWIRL_GL_TESTS=1 (needs a real GL context)",
)


@pytest.fixture(scope="module")
def qt_app():
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app


@pytest.fixture(scope="module")
def canvas(qt_app):
    scene = pytest.importorskip("vispy.scene")
    c = scene.SceneCanvas(keys=None, size=(200, 200), show=False)
    c.render()  # force context creation
    yield c
    c.close()


def test_all_shader_methods_render(canvas):
    from shwirl.shaders import RenderVolume

    view = canvas.central_widget.add_view()
    import vispy.scene as scene
    view.camera = scene.cameras.TurntableCamera()

    rng = np.random.default_rng(0)
    vol = (rng.random((16, 16, 16)).astype(np.float32) ** 3) * 10.0
    volume = RenderVolume(vol, parent=view.scene, threshold=0.5)

    for method in METHODS:
        volume.method = method
        canvas.render()  # compiles the GLSL for this method and draws

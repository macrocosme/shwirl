"""Tests for the GLSL transfer-function shader generation.

These exercise the non-GPU logic in ``shwirl.shaders.render_volume``: they check
that every transfer-function method produces a fully-formatted shader string.
No OpenGL context or display is required.
"""
import pytest

render_volume = pytest.importorskip("shwirl.shaders.render_volume")

EXPECTED_METHODS = {
    "mip",
    "lmip",
    "iso",
    "avip",
    "minip",
    "translucent2",
    "additive",
}


def test_frag_dict_has_expected_methods():
    assert set(render_volume.frag_dict) == EXPECTED_METHODS


@pytest.mark.parametrize("method", sorted(EXPECTED_METHODS))
def test_shader_is_fully_formatted(method):
    src = render_volume.frag_dict[method]
    assert isinstance(src, str)
    assert src.strip(), f"empty shader for {method}"
    # A fragment shader must have an entry point.
    assert "void main" in src
    # After .format(**SNIPPETS) there must be no leftover single-brace
    # placeholders (GLSL literal braces are escaped as ``{{`` / ``}}``).
    assert "{}" not in src, f"unformatted placeholder in {method} shader"

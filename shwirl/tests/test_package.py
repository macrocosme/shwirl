"""Smoke tests for package importability and the console entry point.

Importing ``shwirl.shwirl`` pulls in PySide6 and the vendored VisPy. Under a
headless environment set ``QT_QPA_PLATFORM=offscreen`` (the CI does this) so no
physical display is needed.
"""
import importlib

import pytest


def test_package_exposes_main():
    shwirl = importlib.import_module("shwirl")
    assert callable(shwirl.main)


def test_shwirl_module_imports():
    mod = pytest.importorskip("shwirl.shwirl")
    # The GUI window and the console entry point must be present.
    assert hasattr(mod, "MainWindow")
    assert callable(mod.main)

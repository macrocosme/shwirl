def main():
    from .shwirl import main as _main
    _main()


def __getattr__(name):
    # Lazy exports so `import shwirl` stays light (no Qt/vispy import cost)
    # while `from shwirl import Renderer, demo_cube` works for API users.
    if name in ("Renderer", "demo_cube"):
        from . import api
        return getattr(api, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

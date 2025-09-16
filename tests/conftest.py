import pathlib
import pytest


def pytest_ignore_collect(path: pathlib.Path, config) -> bool:
    # Mirror prior behavior: ignore files marked as *.skip.py
    return str(path).endswith(".skip.py")


def pytest_collection_modifyitems(config, items):
    # Mark files named *-broken.py as xfail (strict), mirroring previous expectations.
    for item in items:
        nodeid = item.nodeid
        if "-broken.py" in nodeid:
            item.add_marker(
                pytest.mark.xfail(
                    reason="Marked broken by filename (*-broken.py)",
                    strict=True,
                )
            )


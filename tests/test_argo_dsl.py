from os import path
from pathlib import Path

import toml

from argo_dsl import __version__


PROJECT_ROOT = path.dirname(path.dirname(__file__))


def test_version():
    with open(Path(PROJECT_ROOT) / "pyproject.toml") as f:
        config = toml.load(f)

    assert config["tool"]["poetry"]["version"] == __version__

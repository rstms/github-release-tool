"""Top-level package for github-release-tool."""

from .cli import cli
from .release import Release
from .version import __author__, __email__, __timestamp__, __version__

__all__ = ["cli", "Release", __version__, __timestamp__, __author__, __email__]

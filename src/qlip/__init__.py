"""qlip — print page metadata (url, title, site, date, description) for a URL."""

from .extract import extract, fetch
from .render import render

__version__ = "0.1.0"
__all__ = ["extract", "fetch", "render", "__version__"]

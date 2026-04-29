"""pipewatch.sources — built-in metric source registry.

Importing this package automatically registers all bundled sources so that
``get_source('http')``, ``get_source('db')``, and ``get_source('file')``
work without explicit imports by callers.
"""

from pipewatch.sources.base import BaseSource, get_source, register_source  # noqa: F401

# Trigger registration of built-in sources.
import pipewatch.sources.db_source    # noqa: F401
import pipewatch.sources.file_source  # noqa: F401
import pipewatch.sources.http_source  # noqa: F401

__all__ = ["BaseSource", "get_source", "register_source"]

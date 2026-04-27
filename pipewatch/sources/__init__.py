"""pipewatch.sources — built-in metric source implementations."""

# Import built-in sources so their @register_source decorators run
# and they are available via get_source() without explicit imports.
from pipewatch.sources import http_source  # noqa: F401

__all__ = ["http_source"]

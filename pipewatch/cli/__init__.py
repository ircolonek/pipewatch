"""pipewatch.cli — command-line interface package.

This package provides the command-line interface for pipewatch, a tool
for monitoring and filtering piped data streams.

Usage::

    $ pipewatch --help
    $ some-command | pipewatch [OPTIONS]
"""
from pipewatch.cli.commands import main

__all__ = ["main"]

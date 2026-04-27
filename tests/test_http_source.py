"""Tests for pipewatch.sources.http_source."""

import json
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch

from pipewatch.sources.http_source import HttpSource
from pipewatch.sources.base import get_source
from pipewatch.metrics.models import Metric


SAMPLE_PAYLOAD = [
    {"name": "pipeline.lag", "value": 15.5, "tags": {"env": "prod"}},
    {"name": "pipeline.errors", "value": 3.0, "tags": {}},
]


def _mock_response(payload):
    body = json.dumps(payload).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestHttpSourceRegistration(unittest.TestCase):
    def test_registered_under_http_key(self):
        cls = get_source("http")
        self.assertIs(cls, HttpSource)


class TestHttpSourceFetch(unittest.TestCase):
    @patch("pipewatch.sources.http_source.urllib.request.urlopen")
    def test_returns_metric_objects(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(SAMPLE_PAYLOAD)
        source = HttpSource(url="http://example.com/metrics")
        metrics = source.fetch()
        self.assertEqual(len(metrics), 2)
        self.assertIsInstance(metrics[0], Metric)

    @patch("pipewatch.sources.http_source.urllib.request.urlopen")
    def test_metric_values_parsed_correctly(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(SAMPLE_PAYLOAD)
        source = HttpSource(url="http://example.com/metrics")
        metrics = source.fetch()
        names = {m.name for m in metrics}
        self.assertIn("pipeline.lag", names)
        self.assertIn("pipeline.errors", names)
        lag = next(m for m in metrics if m.name == "pipeline.lag")
        self.assertAlmostEqual(lag.value, 15.5)
        self.assertEqual(lag.tags, {"env": "prod"})

    @patch("pipewatch.sources.http_source.urllib.request.urlopen")
    def test_metric_prefix_applied(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(SAMPLE_PAYLOAD)
        source = HttpSource(url="http://example.com/metrics", metric_prefix="myteam.")
        metrics = source.fetch()
        for m in metrics:
            self.assertTrue(m.name.startswith("myteam."), m.name)

    @patch("pipewatch.sources.http_source.urllib.request.urlopen")
    def test_network_error_raises_runtime_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("connection refused")
        source = HttpSource(url="http://unreachable.invalid/metrics")
        with self.assertRaises(RuntimeError):
            source.fetch()

    @patch("pipewatch.sources.http_source.urllib.request.urlopen")
    def test_invalid_json_raises_value_error(self, mock_urlopen):
        bad_resp = MagicMock()
        bad_resp.read.return_value = b"not-json"
        bad_resp.__enter__ = lambda s: s
        bad_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = bad_resp
        source = HttpSource(url="http://example.com/metrics")
        with self.assertRaises(ValueError):
            source.fetch()

    def test_source_name_property(self):
        source = HttpSource(url="http://example.com/metrics")
        self.assertEqual(source.source_name, "http")


if __name__ == "__main__":
    unittest.main()

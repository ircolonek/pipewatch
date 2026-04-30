"""Tests for PipelineScheduler."""

from __future__ import annotations

import time
import pytest

from pipewatch.pipeline.scheduler import PipelineScheduler


class TestPipelineScheduler:
    def test_raises_on_non_positive_interval(self):
        with pytest.raises(ValueError, match="positive"):
            PipelineScheduler(name="bad", interval=0, task=lambda: None)

    def test_start_and_stop(self):
        calls = []
        scheduler = PipelineScheduler(
            name="test", interval=0.05, task=lambda: calls.append(1)
        )
        scheduler.start()
        assert scheduler.is_running
        time.sleep(0.18)
        scheduler.stop(timeout=2.0)
        assert not scheduler.is_running
        assert len(calls) >= 2

    def test_double_start_is_safe(self):
        scheduler = PipelineScheduler(
            name="double", interval=0.1, task=lambda: None
        )
        scheduler.start()
        scheduler.start()  # should not raise or spawn second thread
        assert scheduler.is_running
        scheduler.stop()

    def test_task_exception_does_not_crash_scheduler(self):
        def bad_task():
            raise RuntimeError("boom")

        scheduler = PipelineScheduler(name="err", interval=0.05, task=bad_task)
        scheduler.start()
        time.sleep(0.15)
        assert scheduler.is_running
        scheduler.stop(timeout=2.0)

    def test_is_running_false_before_start(self):
        scheduler = PipelineScheduler(
            name="idle", interval=1.0, task=lambda: None
        )
        assert not scheduler.is_running

"""Simple interval-based scheduler for running pipelines repeatedly."""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable

logger = logging.getLogger(__name__)


class PipelineScheduler:
    """Runs a callable on a fixed interval in a background thread."""

    def __init__(self, name: str, interval: float, task: Callable[[], None]) -> None:
        if interval <= 0:
            raise ValueError("interval must be a positive number")
        self.name = name
        self.interval = interval
        self.task = task
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the scheduler in a daemon background thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("[%s] scheduler already running", self.name)
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop, name=f"scheduler-{self.name}", daemon=True
        )
        self._thread.start()
        logger.info("[%s] scheduler started (interval=%.1fs)", self.name, self.interval)

    def stop(self, timeout: float = 5.0) -> None:
        """Signal the scheduler to stop and wait for the thread to finish."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        logger.info("[%s] scheduler stopped", self.name)

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.task()
            except Exception as exc:  # noqa: BLE001
                logger.error("[%s] task raised an error: %s", self.name, exc)
            self._stop_event.wait(self.interval)

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

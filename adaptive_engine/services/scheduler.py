from __future__ import annotations

import threading
import time
from typing import Callable, Optional


class RepeatingTimer:
    """Simple repeating timer that runs a callable every interval seconds in a daemon thread."""

    def __init__(self, interval_sec: int, func: Callable[[], None]):
        self.interval_sec = max(1, int(interval_sec))
        self.func = func
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _loop():
            while not self._stop.is_set():
                try:
                    self.func()
                except Exception:
                    # best-effort; keep going
                    pass
                self._stop.wait(self.interval_sec)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

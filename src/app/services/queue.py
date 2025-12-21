"""Request queue management for TTS synthesis."""

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar, cast

import structlog

from app.config import get_config
from app.models.errors import APIError, ErrorCode

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class RequestQueue:
    """Bounded async queue for synthesis requests."""

    def __init__(self, max_size: int | None = None) -> None:
        """Initialize request queue.

        Args:
            max_size: Maximum queue size. Uses config if not specified.
        """
        if max_size is None:
            config = get_config()
            max_size = config.server.max_queue_size

        self._max_size = max_size
        self._queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=max_size)
        self._active_count = 0
        self._lock = asyncio.Lock()

    @property
    def size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    @property
    def max_size(self) -> int:
        """Get maximum queue size."""
        return self._max_size

    @property
    def is_full(self) -> bool:
        """Check if queue is full."""
        return self._queue.full()

    @property
    def active_count(self) -> int:
        """Get count of actively processing requests."""
        return self._active_count

    async def submit(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Submit a task to the queue and wait for result.

        Args:
            func: Function to execute.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Result of the function.

        Raises:
            APIError: If queue is full.
        """
        if self.is_full:
            logger.warning(
                "queue.full",
                queue_size=self.size,
                max_size=self._max_size,
            )
            raise APIError(
                ErrorCode.SERVICE_BUSY,
                "Service is busy, please try again later",
                {"queue_size": self.size, "max_size": self._max_size},
            )

        async with self._lock:
            self._active_count += 1

        try:
            # Execute the function (synchronous synthesis runs in thread pool)
            result: T
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                loop = asyncio.get_event_loop()
                result = cast(
                    T, await loop.run_in_executor(None, lambda: func(*args, **kwargs))
                )
            return result
        finally:
            async with self._lock:
                self._active_count -= 1


# Global queue instance
_request_queue: RequestQueue | None = None


def get_request_queue() -> RequestQueue:
    """Get the global request queue.

    Returns:
        Global request queue.
    """
    global _request_queue
    if _request_queue is None:
        _request_queue = RequestQueue()
    return _request_queue


def reset_request_queue() -> None:
    """Reset the global request queue. Used for testing."""
    global _request_queue
    _request_queue = None

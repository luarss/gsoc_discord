"""Rate limit handling for Discord API."""

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

logger = logging.getLogger(__name__)


@dataclass
class RateLimitInfo:
    """Rate limit information from Discord API."""

    remaining: int
    reset_after: float
    limit: int


class RateLimiter:
    """Handles Discord API rate limits with exponential backoff."""

    def __init__(self, max_retries: int = 5, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._global_lock = asyncio.Lock()
        self._global_reset_time: float = 0

    async def wait_for_global_reset(self) -> None:
        """Wait if there's a global rate limit in effect."""
        if self._global_reset_time > 0:
            now = asyncio.get_event_loop().time()
            wait_time = self._global_reset_time - now
            if wait_time > 0:
                logger.warning(f"Global rate limit - waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

    def set_global_reset(self, reset_after: float) -> None:
        """Set global rate limit reset time."""
        self._global_reset_time = asyncio.get_event_loop().time() + reset_after

    @asynccontextmanager
    async def retry_on_rate_limit(self) -> AsyncIterator[None]:
        """Context manager that handles rate limit retries."""
        await self.wait_for_global_reset()
        retries = 0
        while True:
            try:
                yield
                break
            except Exception as e:
                if not self._is_rate_limit_error(e):
                    raise
                if retries >= self.max_retries:
                    logger.error("Max retries exceeded for rate limit")
                    raise

                delay = self.base_delay * (2**retries)
                logger.warning(
                    f"Rate limit hit, retry {retries + 1}/{self.max_retries} "
                    f"after {delay:.1f}s"
                )
                await asyncio.sleep(delay)
                retries += 1

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if an exception is a rate limit error."""
        error_name = type(error).__name__
        return error_name == "RateLimited" or "rate" in str(error).lower()


# Global rate limiter instance
rate_limiter = RateLimiter()

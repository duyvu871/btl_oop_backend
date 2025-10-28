"""
Rate limiter for API requests to ensure we don't exceed rate limits.
"""

import asyncio
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class RateLimiterStatus:
    """
    Status information for the rate limiter.
    """
    current_requests: int
    max_requests: int
    remaining_capacity: int
    time_window_seconds: float
    optimal_delay_seconds: float
    total_requests_made: int


@dataclass
class ProcessingEstimate:
    """
    Estimated processing time for batch operations.
    """
    total_batches: int
    max_requests_per_minute: int
    estimated_minutes: float
    estimated_seconds: float


@dataclass
class ProcessingStats:
    """
    Statistics for batch processing operations.
    """
    processed_count: int
    elapsed_seconds: float
    current_rpm: float
    max_rpm: int


class RateLimiter:
    """
    Rate limiter to control the number of requests per time window.
    Uses sliding window algorithm for precise rate limiting.
    """

    def __init__(self, max_requests: int = 95, time_window: float = 60.0):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in the time window (RPM)
            time_window: Time window in seconds (default: 60 seconds = 1 minute)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self._lock = asyncio.Lock()
        self._request_count = 0

    async def acquire(self) -> None:
        """
        Wait if necessary to ensure we don't exceed rate limits.
        This should be called before making each API request.
        """
        async with self._lock:
            now = time.time()

            # Remove requests outside the time window
            while self.requests and now - self.requests[0] >= self.time_window:
                self.requests.popleft()

            # If we're at the limit, wait until we can make another request
            if len(self.requests) >= self.max_requests:
                # Calculate how long to wait
                oldest_request = self.requests[0]
                wait_time = self.time_window - (now - oldest_request) + 0.1  # Add small buffer

                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Clean up again after waiting
                    now = time.time()
                    while self.requests and now - self.requests[0] >= self.time_window:
                        self.requests.popleft()

            # Record this request
            self.requests.append(now)
            self._request_count += 1

    def get_delay_between_requests(self) -> float:
        """
        Calculate the optimal delay between requests to stay under the limit.

        Returns:
            Delay in seconds
        """
        return self.time_window / self.max_requests

    def reset(self) -> None:
        """
        Reset the rate limiter.
        """
        self.requests.clear()
        self._request_count = 0

    def get_status(self) -> RateLimiterStatus:
        """
        Get current status of the rate limiter.

        Returns:
            RateLimiterStatus object with current request count and remaining capacity
        """
        now = time.time()
        # Remove old requests
        while self.requests and now - self.requests[0] >= self.time_window:
            self.requests.popleft()

        return RateLimiterStatus(
            current_requests=len(self.requests),
            max_requests=self.max_requests,
            remaining_capacity=self.max_requests - len(self.requests),
            time_window_seconds=self.time_window,
            optimal_delay_seconds=self.get_delay_between_requests(),
            total_requests_made=self._request_count,
        )


class BatchRateLimiter:
    """
    Rate limiter specifically for batch operations.
    Calculates optimal batch size to stay under rate limits.
    Supports processing multiple items with controlled RPM.
    """

    def __init__(
        self,
        max_requests_per_minute: int = 95,
        max_tokens_per_minute: int = None
    ):
        """
        Initialize batch rate limiter.

        Args:
            max_requests_per_minute: Maximum number of requests per minute (RPM)
            max_tokens_per_minute: Maximum number of tokens per minute (TPM)
                                   If set, will also enforce token-based rate limiting
        """
        self.rate_limiter = RateLimiter(max_requests=max_requests_per_minute, time_window=60.0)
        self.max_requests_per_minute = max_requests_per_minute
        self.max_tokens_per_minute = max_tokens_per_minute
        self._processed_count = 0
        self._start_time = None

        # Token tracking
        self._token_requests = deque()  # (timestamp, token_count) tuples
        self._total_tokens_processed = 0

    def calculate_batch_size(self, total_items: int, target_time_minutes: float | None = None) -> int:
        """
        Calculate optimal batch size to process items under rate limits.

        Args:
            total_items: Total number of items to process
            target_time_minutes: Target time to complete (optional)

        Returns:
            Recommended batch size
        """
        if target_time_minutes:
            # Calculate batch size based on target time
            requests_available = int(self.max_requests_per_minute * target_time_minutes)
            return max(1, total_items // requests_available)
        else:

            # For embedding APIs, typically 100-500 items per request
            return min(100, max(1, total_items // 10))

    async def acquire_with_tokens(self, token_count: int) -> None:
        """
        Wait if necessary before making the next batch request.
        Enforces both request rate and token rate limits.

        Args:
            token_count: Number of tokens in this request
        """
        if self._start_time is None:
            self._start_time = time.time()

        # First, check request rate limit
        await self.rate_limiter.acquire()

        # Then, check token rate limit if configured
        if self.max_tokens_per_minute is not None:
            now = time.time()

            # Remove token requests outside the time window
            while self._token_requests and now - self._token_requests[0][0] >= 60.0:
                self._token_requests.popleft()

            # Calculate current tokens in window
            current_tokens = sum(tokens for _, tokens in self._token_requests)

            # If adding this request would exceed limit, wait
            if current_tokens + token_count > self.max_tokens_per_minute:
                # Calculate wait time based on oldest token request
                if self._token_requests:
                    oldest_time = self._token_requests[0][0]
                    wait_time = 60.0 - (now - oldest_time) + 0.5  # Add buffer

                    if wait_time > 0:
                        print(f"\n⏸️  Token limit approaching: {current_tokens:,}/{self.max_tokens_per_minute:,} TPM")
                        print(f"   Waiting {wait_time:.1f}s to avoid rate limit...")
                        await asyncio.sleep(wait_time)

                        # Clean up again after waiting
                        now = time.time()
                        while self._token_requests and now - self._token_requests[0][0] >= 60.0:
                            self._token_requests.popleft()

            # Record this token request
            self._token_requests.append((now, token_count))
            self._total_tokens_processed += token_count

        self._processed_count += 1

    async def acquire(self) -> None:
        """
        Wait if necessary before making the next batch request.
        Tracks processing statistics.
        """
        if self._start_time is None:
            self._start_time = time.time()

        await self.rate_limiter.acquire()
        self._processed_count += 1

    def get_processing_estimate(self, total_batches: int) -> ProcessingEstimate:
        """
        Estimate how long it will take to process all batches.

        Args:
            total_batches: Total number of batches to process

        Returns:
            ProcessingEstimate object with time estimates
        """
        minutes_needed = total_batches / self.max_requests_per_minute

        return ProcessingEstimate(
            total_batches=total_batches,
            max_requests_per_minute=self.max_requests_per_minute,
            estimated_minutes=round(minutes_needed, 2),
            estimated_seconds=round(minutes_needed * 60, 2),
        )

    def get_stats(self) -> ProcessingStats:
        """
        Get current processing statistics.

        Returns:
            ProcessingStats object with processing stats
        """
        if self._start_time is None:
            return ProcessingStats(
                processed_count=0,
                elapsed_seconds=0.0,
                current_rpm=0.0,
                max_rpm=self.max_requests_per_minute,
            )

        elapsed = time.time() - self._start_time
        current_rpm = (self._processed_count / elapsed * 60) if elapsed > 0 else 0

        return ProcessingStats(
            processed_count=self._processed_count,
            elapsed_seconds=round(elapsed, 2),
            current_rpm=round(current_rpm, 2),
            max_rpm=self.max_requests_per_minute,
        )

    async def process_batches(
        self,
        items: list[Any],
        batch_size: int,
        process_func: Callable[[list[Any]], Any]
    ) -> list[Any]:
        """
        Process items in batches with automatic rate limiting.

        Args:
            items: List of items to process
            batch_size: Size of each batch
            process_func: Async function to process each batch

        Returns:
            List of results from each batch
        """
        results = []
        num_batches = (len(items) + batch_size - 1) // batch_size

        for i in range(0, len(items), batch_size):
            await self.acquire()
            batch = items[i:i + batch_size]
            result = await process_func(batch)
            results.append(result)

        return results

    def reset(self) -> None:
        """
        Reset the batch rate limiter statistics.
        """
        self.rate_limiter.reset()
        self._processed_count = 0
        self._start_time = None


from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(
        self,
        max_requests: int = 1000,
        window_seconds: int = 60,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)

    def check(
        self,
        request: Request,
    ) -> None:

        client = request.client

        if client is None:
            client_id = "unknown"
        else:
            client_id = client.host

        now = monotonic()

        request_times = self.requests[client_id]

        while (
            request_times
            and now - request_times[0]
            >= self.window_seconds
        ):
            request_times.popleft()

        if len(request_times) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Rate limit exceeded. "
                    "Please try again later."
                ),
            )

        request_times.append(now)


rate_limiter = RateLimiter(
    max_requests=1000,
    window_seconds=60,
)
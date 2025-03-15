"""
Rate Limiting Middleware Module

This module provides rate limiting capabilities for the Molecular Data Management and
CRO Integration Platform. It implements configurable rate limits to protect against API abuse
and ensure fair resource allocation across users and clients.

The module supports both in-memory and Redis-based rate limiters, making it suitable for
single-server deployments and distributed environments. It integrates with FastAPI as middleware
to apply rate limits to incoming requests based on client IP or user identity.

Features:
- Configurable rate limits based on requests per time window
- Support for in-memory and Redis-based rate limiting strategies
- Path-based exclusions for specific endpoints
- Custom client identification strategies
- Standard rate limit headers in API responses
- Graceful handling of Redis connection failures
"""

import time
import asyncio
from collections import defaultdict
from typing import Dict, List, Optional, Callable, Any, Tuple

import redis  # redis 4.5.0+
from fastapi import Request, Response  # fastapi 0.95+
from starlette import status  # starlette 0.27.0+

from ..core.config import settings
from ..core.logging import get_logger
from ..core.exceptions import RateLimitException
from ..constants.error_messages import SYSTEM_ERRORS

# Initialize logger
logger = get_logger(__name__)


class RateLimiter:
    """Abstract base class for rate limiter implementations."""
    
    def __init__(self, rate_limit: int, time_window: int):
        """
        Initialize the rate limiter with limit and time window.
        
        Args:
            rate_limit: Maximum number of requests allowed in the time window
            time_window: Time window in seconds
        """
        self.rate_limit = rate_limit
        self.time_window = time_window
    
    def is_rate_limited(self, client_id: str) -> Tuple[bool, int, int]:
        """
        Check if a client has exceeded their rate limit.
        
        Args:
            client_id: Identifier for the client (IP address or user ID)
            
        Returns:
            Tuple containing:
              - bool: True if client is rate limited
              - int: Number of remaining requests allowed
              - int: Seconds until the rate limit resets
        """
        raise NotImplementedError("Subclasses must implement is_rate_limited method")


class InMemoryRateLimiter(RateLimiter):
    """In-memory implementation of rate limiting using collections.defaultdict."""
    
    def __init__(self, rate_limit: int, time_window: int):
        """
        Initialize the in-memory rate limiter.
        
        Args:
            rate_limit: Maximum number of requests allowed in the time window
            time_window: Time window in seconds
        """
        super().__init__(rate_limit, time_window)
        # Dictionary mapping client_ids to lists of request timestamps
        self.client_requests: Dict[str, List[float]] = defaultdict(list)
    
    def is_rate_limited(self, client_id: str) -> Tuple[bool, int, int]:
        """
        Check if a client has exceeded their rate limit.
        
        Args:
            client_id: Identifier for the client (IP address or user ID)
            
        Returns:
            Tuple containing:
              - bool: True if client is rate limited
              - int: Number of remaining requests allowed
              - int: Seconds until the rate limit resets
        """
        current_time = time.time()
        
        # Remove timestamps outside the current time window
        self._clean_old_requests(client_id, current_time)
        
        # Get the current requests in the time window
        requests = self.client_requests[client_id]
        
        # If no requests or empty after cleaning, reset is zero
        if not requests:
            reset_time = 0
            remaining = self.rate_limit
        else:
            # Calculate the earliest timestamp in the window
            earliest_timestamp = min(requests) if requests else current_time
            # Calculate time until window resets
            reset_time = int(max(0, earliest_timestamp + self.time_window - current_time))
            # Calculate remaining requests
            remaining = max(0, self.rate_limit - len(requests))
        
        # Check if rate limited
        is_limited = len(requests) >= self.rate_limit
        
        # If not limited, add the current request
        if not is_limited:
            self.client_requests[client_id].append(current_time)
        
        return is_limited, remaining, reset_time
    
    def _clean_old_requests(self, client_id: str, current_time: float) -> None:
        """
        Remove request timestamps outside the current time window.
        
        Args:
            client_id: Identifier for the client
            current_time: Current timestamp
        """
        cutoff_time = current_time - self.time_window
        self.client_requests[client_id] = [
            timestamp for timestamp in self.client_requests[client_id]
            if timestamp > cutoff_time
        ]


class RedisRateLimiter(RateLimiter):
    """Redis-based implementation of rate limiting for distributed deployments."""
    
    def __init__(self, rate_limit: int, time_window: int, redis_client: redis.Redis = None, key_prefix: str = "rate_limit:"):
        """
        Initialize the Redis-based rate limiter.
        
        Args:
            rate_limit: Maximum number of requests allowed in the time window
            time_window: Time window in seconds
            redis_client: Initialized Redis client (if None, will create from settings)
            key_prefix: Prefix for Redis keys
        """
        super().__init__(rate_limit, time_window)
        
        # If no Redis client is provided, create one from settings
        if redis_client is None:
            try:
                self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                raise
        else:
            self.redis_client = redis_client
            
        self.key_prefix = key_prefix
    
    def is_rate_limited(self, client_id: str) -> Tuple[bool, int, int]:
        """
        Check if a client has exceeded their rate limit using Redis.
        
        Args:
            client_id: Identifier for the client (IP address or user ID)
            
        Returns:
            Tuple containing:
              - bool: True if client is rate limited
              - int: Number of remaining requests allowed
              - int: Seconds until the rate limit resets
        """
        try:
            # Generate Redis key for this client
            redis_key = self._get_redis_key(client_id)
            
            # Get the current count
            current_count = self.redis_client.get(redis_key)
            
            # If key doesn't exist, initialize it
            if current_count is None:
                pipeline = self.redis_client.pipeline()
                pipeline.set(redis_key, 1)
                pipeline.expire(redis_key, self.time_window)
                pipeline.execute()
                remaining = self.rate_limit - 1
                reset_time = self.time_window
            else:
                # Increment the counter (atomic operation)
                new_count = self.redis_client.incr(redis_key)
                
                # Ensure TTL is set
                ttl = self.redis_client.ttl(redis_key)
                if ttl < 0:
                    self.redis_client.expire(redis_key, self.time_window)
                    ttl = self.time_window
                
                remaining = max(0, self.rate_limit - new_count)
                reset_time = ttl if ttl > 0 else 0
            
            # Check if rate limited
            is_limited = remaining <= 0
            
            return is_limited, remaining, reset_time
            
        except redis.RedisError as e:
            # Log the error but don't rate limit in case of Redis failures
            logger.error(f"Redis error in rate limiter: {str(e)}")
            # In case of Redis failure, we don't rate limit (fail open)
            return False, self.rate_limit, 0
    
    def _get_redis_key(self, client_id: str) -> str:
        """
        Generate Redis key for a client.
        
        Args:
            client_id: Identifier for the client
            
        Returns:
            Redis key string
        """
        # Use a key that includes the time window to ensure
        # that different rate limit configurations don't conflict
        return f"{self.key_prefix}{client_id}:{self.rate_limit}:{self.time_window}"


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting API requests."""
    
    def __init__(
        self, 
        rate_limiter: RateLimiter,
        get_client_id: Optional[Callable] = None,
        exclude_paths: Optional[List[str]] = None
    ):
        """
        Initialize the rate limit middleware.
        
        Args:
            rate_limiter: Rate limiter implementation to use
            get_client_id: Function to extract client identifier from request
            exclude_paths: List of path prefixes to exclude from rate limiting
        """
        self.rate_limiter = rate_limiter
        self.get_client_id = get_client_id or self._default_client_id
        self.exclude_paths = exclude_paths or []
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request through the middleware.
        
        Args:
            request: FastAPI request object
            call_next: Function to call the next middleware or endpoint
            
        Returns:
            FastAPI response object
            
        Raises:
            RateLimitException: If the client has exceeded their rate limit
        """
        # Check if the path should be excluded from rate limiting
        path = request.url.path
        for excluded_path in self.exclude_paths:
            if path.startswith(excluded_path):
                return await call_next(request)
        
        # Get client identifier
        client_id = self.get_client_id(request)
        
        # Check if client is rate limited
        is_limited, remaining, reset_time = self.rate_limiter.is_rate_limited(client_id)
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            raise RateLimitException(
                message=SYSTEM_ERRORS["RATE_LIMIT_EXCEEDED"],
                retry_after=reset_time
            )
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers to the response
        self._add_rate_limit_headers(response, remaining, reset_time)
        
        return response
    
    def _default_client_id(self, request: Request) -> str:
        """
        Default function to extract client identifier from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client identifier (usually IP address)
        """
        # Try to get the real IP if behind a proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs in a comma-separated list
            # The first one is the client, the rest are proxies
            return forwarded_for.split(",")[0].strip()
        
        # If no X-Forwarded-For, use the direct client IP
        return request.client.host if request.client else "unknown"
    
    def _add_rate_limit_headers(self, response: Response, remaining: int, reset_time: int) -> None:
        """
        Add rate limit information to response headers.
        
        Args:
            response: FastAPI response object
            remaining: Number of remaining requests allowed
            reset_time: Seconds until the rate limit resets
        """
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
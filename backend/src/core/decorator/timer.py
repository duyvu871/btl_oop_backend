import time
from functools import wraps


def timer(func):
    """Custom decorator for timing async functions."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print(f"Function {func.__name__!r} executed in {end_time - start_time:.4f}s")
        return result
    return wrapper

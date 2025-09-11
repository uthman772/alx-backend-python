import time
import functools
import random

def retry_on_failure(retries=3, delay=2):
    """
    Decorator to retry a function if it raises an exception.
    Args:
        retries (int): Number of times to retry.
        delay (int): Delay in seconds between retries.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < retries - 1:
                        time.sleep(delay)
            # If all retries fail, raise the last exception
            raise last_exception
        return wrapper
    return decorator

# Example usage:
if __name__ == "__main__":

    @retry_on_failure(retries=5, delay=1)
    def unstable_db_query():
        """Simulates a transient database failure."""
        if random.random() < 0.7:
            raise Exception("Transient DB error")
        return "Query succeeded!"

    try:
        result = unstable_db_query()
        print(result)
    except Exception as e:
        print(f"Operation failed after retries: {e}")
import json
import functools
import os
import time
import io
from typing import Any

NORMALIZABLE_TYPES = (str, int, float, bool)
CACHE_FILE_DIR = ".cache"

if not os.path.exists(CACHE_FILE_DIR):
    os.mkdir(CACHE_FILE_DIR)


def _normalize_cache_key(v):
    if isinstance(v, type):
        return v.__name__
    if isinstance(v, bytes):
        return v.decode()
    if isinstance(v, (list, set)):
        return "-".join(map(_normalize_cache_key, v))
    if v is None or isinstance(v, NORMALIZABLE_TYPES):
        return str(v)
    raise ValueError(f"Only support cache keys of types {[t.__name__ for t in NORMALIZABLE_TYPES]}")


def _make_key(func, *args, **kwargs):
    keys = [_normalize_cache_key(v) for v in args]
    keys += sorted((f"{k}={_normalize_cache_key(v)}" for k, v in kwargs.items()))
    return f"{func.__module__}.{func.__name__}.{'.'.join(keys)}"


def _serialization(data) -> str:
    return json.dumps(data)


def _deserialization(file: io.TextIOWrapper):
    return json.load(file)


class Cacher:
    """
    直接把返回值缓存在磁盘中，超方便！

    Usage:
        @Cacher(timeout=60)
        def fun(a, b, c):
            return a+b+c
    """

    def __init__(self, timeout=60*5):
        self.timeout = timeout

    def __call__(self, *args, **kwargs):
        func = args[0]
        return self.decorator(func)

    def decorator(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cahe_key = _make_key(func, *args, **kwargs)
            cache_file_path = os.path.join(CACHE_FILE_DIR, cahe_key)
            value = self.read_from_disk(cache_file_path)
            if not value:
                value = func(*args, **kwargs)
                self.save_in_disk(cache_file_path=cache_file_path, data=value)
            return value
        return wrapper

    def read_from_disk(self, cache_file_path: str):
        if os.path.exists(cache_file_path):
            file_created_at = os.stat(cache_file_path).st_ctime
            file_expiration = file_created_at + self.timeout
            if file_expiration > time.time():
                with open(cache_file_path) as file:
                    return _deserialization(file)
            else:
                os.remove(cache_file_path)
        return None

    def save_in_disk(self, cache_file_path: str, data: Any) -> None:
        with open(cache_file_path, 'w') as file:
            file.write(_serialization(data))

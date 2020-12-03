import json
import functools
import os
import time
import io

NORMALIZABLE_TYPES = (str, int, float, bool)
DEFAULT_CACHE_FILE_DIR = ".cache"


if not os.path.exists(DEFAULT_CACHE_FILE_DIR):
    os.mkdir(DEFAULT_CACHE_FILE_DIR)


class Cacher:
    """
    直接把返回值缓存在磁盘中，超方便！

    Args:
        timeout: 可选参数，默认 5*60 秒
        cache_file_path: 可选参数，保存缓存文件的绝对路径

    Usage:
        @Cacher(timeout=5*60, cache_file_path="/Users/bytedance/Desktop/xxx.cache")
        def fun(a, b, c):
            return a+b+c
    """

    def __init__(self, timeout=5*60, cache_file_path: str=""):
        self.timeout = timeout
        self.custom_cache_file_path = cache_file_path

    def __call__(self, *args, **kwargs):
        func = args[0]
        return self.decorator(func)

    def decorator(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cahe_key = Cacher.make_key(func, *args, **kwargs)
            cache_file_path = self.custom_cache_file_path or os.path.join(DEFAULT_CACHE_FILE_DIR, cahe_key)
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
                    return Cacher.deserialization(file)
            else:
                os.remove(cache_file_path)
        return None

    def save_in_disk(self, cache_file_path: str, data) -> None:
        with open(cache_file_path, 'w') as file:
            file.write(Cacher.serialization(data))

    @staticmethod
    def make_key(func, *args, **kwargs):
        return f"{func.__module__}.{func.__qualname__}.{str(args)}.{str(kwargs)}"

    @staticmethod
    def serialization(data) -> str:
        return json.dumps(data)

    @staticmethod
    def deserialization(file: io.TextIOWrapper):
        return json.load(file)

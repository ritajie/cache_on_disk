# cache_on_disk
一个装饰器，直接把函数返回值缓存在磁盘中，超方便！
```python
from cache_on_disk import Cacher

@Cacher(timeout=5*60, cache_file_path="/Users/bytedance/Desktop/xxx.cache")
def fun(a):
    return 1 
```

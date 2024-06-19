import asyncio
import functools
import pickle
import threading
import time
from json import JSONDecodeError
from typing import Any

from flask import Flask

from src.config import config_instance
from src.logger import init_logger
from src.utils import camel_to_snake

MEM_CACHE_SIZE = config_instance().CACHE_SETTINGS.MAX_CACHE_SIZE
EXPIRATION_TIME = config_instance().CACHE_SETTINGS.CACHE_DEFAULT_TIMEOUT


async def create_key(method: str, kwargs: dict[str, str | int]) -> str:
    """
        used to create keys for cache redis handler
    """
    if not kwargs:
        _key = "all"
    else:
        _key = ".".join(f"{key}={str(value)}" for key, value in kwargs.items() if value).lower()
    return f"{method}.{_key}"


class Caching:

    def __init__(self, cache_name: str = "mem_cache", max_size: int = MEM_CACHE_SIZE,
                 expiration_time: int = EXPIRATION_TIME):
        self.max_size = max_size
        self.expiration_time = expiration_time
        self._cache_name = cache_name
        self._cache = {}
        self.check_expired = asyncio.Event()
        self._cache_lock = threading.Lock()
        self.event_loop = asyncio.get_event_loop()
        self._cache_action_timeout = 3
        self._logger = init_logger(camel_to_snake(self.__class__.__name__))

    def init_app(self, app: Flask):
        self._logger.info("starting memory management daemon ")
        self.event_loop.create_task(self.daemon_memory_management())

    async def clear_mem_cache(self):
        """will completely empty mem cache"""
        with self._cache_lock:
            self._cache = {}

    @functools.lru_cache(maxsize=1024)
    async def _serialize_value(self, value: Any, default=None) -> str | bytes:
        """
            Serialize the given value to a json string.
        """
        try:
            return pickle.dumps(value)
        except (JSONDecodeError, pickle.PicklingError):
            config_instance().DEBUG and self._logger.error(f"Serializer Error")
            return default
        except TypeError:
            config_instance().DEBUG and self._logger.error(f"Serializer Error")
            return default

    @functools.lru_cache(maxsize=1024)
    async def _deserialize_value(self, value: any, default=None) -> Any:
        """
            Deserialize the given json string to a python object.
        """
        try:
            return pickle.loads(value)
        except (JSONDecodeError, pickle.UnpicklingError):
            config_instance().DEBUG and self._logger.error(f"Error Deserializing Data")
            return default
        except TypeError:
            config_instance().DEBUG and self._logger.error(f"Error Deserializing Data")
            return default

    async def delete_memcache_key(self, key):
        """ Note: do not use pop"""
        with self._cache_lock:
            del self._cache[key]

    async def _remove_oldest_entry(self):
        """
        **in-case memory is full remove oldest entries
             Remove the oldest entry in the in-memory cache.
        :return:
        """
        with self._cache_lock:
            # Find the oldest entry
            oldest_entry = None
            for key, value in self._cache.items():
                if oldest_entry is None:
                    oldest_entry = key
                elif value['timestamp'] < self._cache[oldest_entry]['timestamp']:
                    oldest_entry = key

            # Remove the oldest entry from all caches
            if oldest_entry is not None:
                await self.delete_memcache_key(key=oldest_entry)

    async def _set_mem_cache(self, key: str, value: Any, ttl: int = 0):
        """
            **_set_mem_cache**
                private method never call this code directly
        :param key:
        :param value:
        :param ttl:
        :return:
        """
        with self._cache_lock:
            # If the cache is full, remove the oldest entry
            if len(self._cache) >= self.max_size:
                await self._remove_oldest_entry()

            # creates a mem_cache item and set the timestamp and time to live based on given value or default
            self._cache[key] = {'value': value, 'timestamp': time.monotonic(), 'ttl': ttl}

    async def set(self, key: str, value: Any, ttl: int = 0):
        """
             Store the value in the cache. If the key already exists, the value is updated.

            :param key: str - a unique identifier for the cached value
            :param value: Any - the value to be cached
            :param ttl: int, optional - the time-to-live of the cached value in seconds;
                       if not provided, the default expiration time of the cache is used.

            If use_redis=True the value is stored in Redis, otherwise it is stored in-memory.

            :return: None
        """
        # value = await self._serialize_value(value, value)
        # setting expiration time
        exp_time = ttl if ttl else self.expiration_time

        if len(self._cache) > self.max_size:
            await self._remove_oldest_entry()

        try:
            await asyncio.wait_for(self._set_mem_cache(key=key, value=value, ttl=exp_time),
                                   timeout=self._cache_action_timeout)
            # await self._set_mem_cache(key=key, value=value, ttl=exp_time)
        except (KeyError, asyncio.TimeoutError, asyncio.CancelledError) as e:
            self._logger.error(f"Failure Setting Cache Value for Key: {key}")

    async def _get_memcache(self, key: str) -> Any:
        """
            # called by get and set should not be called by user
        :param key:
        :return:
        """
        entry = self._cache.get(key, {})
        if entry and time.monotonic() - entry['timestamp'] < self.expiration_time:
            value = entry['value']
        else:
            # await self.delete_key(key)
            value = None
        return value

    # 1 second timeout default
    async def get(self, key: str) -> Any:
        """
            *GET*
                NOTE This method will time-out in 1 second if no value is returned from any cache
                    Retrieve the value associated with the given key within the allocated time.
                    If use_redis=True the value is retrieved from Redis, only if that key is not also on local memory.

            :param key = a key used to find the value to search for.
        """
        try:
            value = await asyncio.wait_for(self._get_memcache(key=key), timeout=self._cache_action_timeout)
        except (asyncio.TimeoutError, asyncio.CancelledError) as e:
            self._logger.error(f"Error while fetching Cached Value for Key : {key}")
            value = None

        return value if value else None

    async def memcache_ttl_cleaner(self) -> int:
        """
            **memcache_ttl_cleaner**
                will run every ten minutes to clean up every expired mem cache item
                expiration is dependent on ttl
        :return:
        """
        now = time.monotonic()
        # Cache Items are no more than 1024 therefore this is justifiable
        t_c = 0
        for key in list(self._cache.keys()):
            # Time has progressed past the allocated time for this resource
            # NOTE for those values where timeout is not previously declared the Assumption is 1 Hour
            value = self._cache[key]
            if value.get('timestamp', 0) + value.get('ttl', 60 * 60) < now:
                await self.delete_memcache_key(key=key)
                await asyncio.sleep(self._cache_action_timeout)
                t_c += 1
        return t_c

    def cached_ttl(self, ttl: int = 60 * 60 * 1):
        """
            Caching decorator with a time-to-live (TTL) parameter that stores the function's return value in Redis for fast retrieval
            and sets an expiration time for the cached value.
        """

        def _mem_cached(func):
            @functools.wraps(func)
            async def _wrapper(*args, **kwargs):

                new_kwargs = {}
                for arg_index, arg_value in enumerate(args):
                    if isinstance(arg_value, (tuple, list)):
                        for i, val in enumerate(arg_value):
                            new_kwargs[f'arg{arg_index}_{i}'] = val
                    elif isinstance(arg_value, str):
                        new_kwargs[f'arg{arg_index}'] = arg_value
                    else:
                        # handle other data types here
                        pass

                new_kwargs.update({k: v for k, v in kwargs.items() if k != 'session'})
                _key = await create_key(method=func.__name__, kwargs=new_kwargs)
                _data = await self.get(_key)

                if _data is None:
                    result = await func(*args, **kwargs)
                    if result:
                        await self.set(key=_key, value=result, ttl=ttl)
                    return result
                return _data

            return _wrapper

        return _mem_cached

    async def daemon_memory_management(self):
        """
        :return:
        """
        max_time_to_run_mem_cleaner = 60 * 1  # 1 minutes
        time_to_sleep_between_cleaning = 60 * 60 * 1  # 1 hour
        while True:
            try:
                self._logger.info("Started Running Memory management Daemon")
                await asyncio.wait_for(self.memcache_ttl_cleaner(), timeout=max_time_to_run_mem_cleaner)
                self._logger.info("Completed Running Memory Management Daemon")
            except (asyncio.TimeoutError, asyncio.CancelledError) as e:
                self._logger.info(f"Going to Sleep for {time_to_sleep_between_cleaning}")
            await asyncio.sleep(delay=time_to_sleep_between_cleaning)


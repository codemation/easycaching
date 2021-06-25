from typing import AsyncGenerator
from aiopyql.data import Database
from aiopyql.table import Table
from easycaching.db import get_cache_db


class EasyQueue:
    def __init__(self, parent):
        self.parent = parent
    async def put(self, queue, data):
        return await self.parent.db['ec_queue_put'](
           'q_' + queue,
           data
        )
    async def get(self, queue):
        return await self.parent.db['ec_queue_get'](
           'q_' + queue,
        )
    def __getitem__(self, queue):
        return Queue(queue, self.parent)
    async def clear(self, queue):
        return await self.parent.db['ec_clear_queue'](
           'q_' + queue
        )


class Queue(EasyQueue):
    def __init__(self, name, parent):
        super().__init__(parent)
        self.name = name
    async def put(self, data):
        return await super().put(self.name, data)
    async def get(self):
        return await super().get(self.name)
    async def clear(self):
        return await super().clear(self.name)

class EasyCache:
    def __init__(self, parent):
        self.parent = parent
    async def set(self, cache, key, value):
        return await self.parent.db['ec_cache_set'](
            cache,
            key, 
            value
        )
    async def get(self, cache, key):
        return await self.parent.db['ec_cache_get'](
            cache,
            key
        )

    async def contains(self, cache, key) -> bool:
        return await self.get(cache, key) is not None
    
    async def delete(self, cache, key) -> None:
        return await self.parent.db['ec_cache_delete'](
            cache,
            key
        )

    async def clear(self, cache):
        return await self.parent.db['ec_cache_clear'](cache)
    
    def __getitem__(self, cache) -> object:
        return Cache(cache, self.parent)
        async def gen():
            async for item in await self.parent.db['ec_cache_get_all'](cache):
                yield item

        return gen()

class Cache(EasyCache):
    def __init__(self, name, parent):
        self.name = name
        super().__init__(parent)
    async def set(self, key, value):
        return await super().set(self.name, key, value)
    async def get(self, key):
        return await super().get(self.name, key)
    async def contains(self, key):
        return await super().get(self.name, key) is not None
    async def clear(self):
        return await super().clear(self.name)
    async def delete(self, key):
        return await super().delete(self.name, key)
    def __getitem__(self, key):
        return self.get(key)
    def __aiter__(self):
        async def gen():
            async for item in await self.parent.db['ec_cache_get_all'](self.name):
                yield item

        return gen()
    

class EasyCacheManager:
    def __init__(self,
        name: str,
        default_size: int = 500
    ):
        self.name = name
        self.size = default_size
        self.cache = EasyCache(self)
        self.queues = EasyQueue(self)
    @classmethod
    async def create(cls,
        name,
        default_size: int = 500
    ):
        cache = cls(
            name,
            default_size
        )

        cache.db = await get_cache_db(cache)

        # create queues table
        await cache.cache_setup()

        await cache.load_cache()
        await cache.load_queues()

        return cache
    async def close(self):
        self.proxy_manager.cancel()
        await self.proxy_manager

    async def cache_setup(self) -> None:
        await self.db['ec_cache_setup']()

    async def create_cache(self, name) -> Cache:

        # create cache table
        await self.db['ec_create_cache'](
            name,
            self.size
        )
        return Cache(name, self)
    
    async def load_cache(self) -> None:
        await self.db['ec_load_cache']()

    async def load_queues(self) -> None:
        await self.db['ec_load_queues']()
    
    async def create_queue(self, name: str ) -> Queue:

        result = await self.db['ec_create_queue'](
            'q_'+ name
        )
        return Queue(name, self)
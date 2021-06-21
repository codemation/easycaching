from aiopyql.data import Database
from aiopyql.table import Table
from easycaching.db import get_cache_db

class EasyCache:
    def __init__(self,
        name: str,
        default_size: int = 500
    ):
        self.name = name
        self.size = default_size
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

        # create cache table

        tables = await cache.db.create_table(
            name, 
            [
                ['cache_key', 'str', 'UNIQUE NOT NULL'],
                ['value', 'str'],
            ],
            'cache_key',
            cache_enabled=True,
            max_cache_len=default_size
        )
        return cache

    async def set(self, key, value):
        cache = self.db.tables[self.name]
        existing = await cache[key]
        if existing is None:
            await cache.insert(
                cache_key=key,
                value=value
            )
        else:
            await cache.update(
                value=value,
                where={
                    'cache_key': key
                }
            )
    async def get(self, key):
        return await self.db.tables[self.name][key]

    def __getitem__(self, key):
        return self.get(key)
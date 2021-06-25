## Cache
EasyCaching Cache is shared & persistent a Key / Value store, backed by a familiar RBDMS. 

### Basic Usage


#### Create EasyCacheManager
```python
import asyncio
from easycaching import EasyCacheManager

async def main():
    # create EasyCache instance
    cache = await EasyCacheManager.create(
        'test'
    )
```

#### Create Cache instance

```python
    # inside main()
    test = await cache.create_cache('test')

```

#### Adding Data to Cache

```python
    # set
    await test.set('foo', 'bar')
```

#### Getting Data from Cache

```python

    cached_value = await test.get('foo')
```

#### Checking if Key Exists
```python
    # boolean
    exists = await test.contains('foo')
```

#### Delete data from Cache
Removing a single Key
```python
    # delete
    await test.delete('foo')
```

Removing all entries from a cache

```python
    await test.clear()
```



#### Iterating over data in Cache
```python
    async for cache_item in test:
        print(cache_item)
```
```bash
{'foo': 'bar'}
{'is': 'basic'}
```

#### Accessing Cache via Manager
If a cache already exists, it is also accessible via manager

```python
    await cache.cache['test'].set('first', 'worst')
    await cache.cache['test'].set('second', 'best')
    await cache.cache['test'].set('third', 'treasure chest')
```

#### Safely Exiting EasyCacheManager 
To ensure Easycaching correctly exits, ensure that .close() is awaited each time. 

```python
    await cache.close()

```
### FastAPI Usage

EasyCaching integrates very easily into the FastAPI ecosystem

```python
# basic.py
from fastapi import FastAPI
from easycaching import EasyCacheManager

app = FastAPI()

@app.on_event('startup')
async def start_cache():
    app.cache = await EasyCacheManager.create(
        'test'
    )
    # create cache instance
    await app.cache.create_cache('test')


@app.get('/cache')
async def view_cache(key: str):
    return {
        key:  await app.cache.cache['test'][key]
    }

@app.post('/cache')
async def set_cache(key: str, value: str):
    return await app.cache.cache['test'].set(
        key, 
        {'json': value}
    )

```
```bash
uvicorn --host 0.0.0.0 --port 8220 --workers 5 basic:app
```

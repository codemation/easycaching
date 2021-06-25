![](docs/images/logo.png)

#

Shared, persistent, and smart caching 

[![Documentation Status](https://readthedocs.org/projects/easycache/badge/?version=latest)](https://easycache.readthedocs.io/en/latest/?badge=latest)
 [![PyPI version](https://badge.fury.io/py/easycaching.svg)](https://badge.fury.io/py/easycaching)
 [![Test EasyCaching](https://github.com/codemation/easycaching/actions/workflows/main.yaml/badge.svg)](https://github.com/codemation/easycaching/actions/workflows/main.yaml)

<h2>Documentation</h1> 

[https://easycache.readthedocs.io/en/latest/](https://easycache.readthedocs.io/en/latest/)

## What is it?
easycaching provides a single shared interface for storing and retreiving data from memory among many processes(forks) of an application.

## Features
- fast and shared access to data
- persistent cache backed by a database
- auto-forking
- python syntax 

## Get Started
```bash
pip install easycaching
```

## Cache Usage

```python
import asyncio
from easycaching import EasyCacheManager

async def main():
    # create EasyCache instance
    cache = await EasyCacheManager.create(
        'test'
    )

    test = await cache.create_cache('test')

    # set
    await test.set('foo', 'bar')


    # get
    cached_value = await test.get('foo')

    # boolean
    exists = await test.contains('foo')

    # iterate over cache items
    async for cache_item in test:
        print(cache_item)
    
    # delete
    await test.delete('foo')

    # clear all cache
    await test.clear()

    # access via manager
    await cache.cache['test'].set('first', 'worst')
    await cache.cache['test'].set('second', 'best')
    await cache.cache['test'].set('third', 'treasure chest')

    # safely exit
    await cache.close()

asyncio.run(main())

```

## Queue Usage

```python
import asyncio
from easycaching import EasyCacheManager

async def main():
    # create EasyCache instance
    cache = await EasyCacheManager.create(
        'test'
    )

    test_queue = await cache.create_queue('test')

    # add items to queue
    await test_queue.put('first')
    await test_queue.put('second')
    await test_queue.put('third')

    # grab items from queue
    result = await test_queue.get()

    await test_queue.get() # second
    await test_queue.get() # third
    result = await test_queue.get() # empty
    {'warning': 'queue empty'}

    # empty a queue
    await test_queue.clear()

    # accessing via manager

    await cache.queues['test'].put('fourth')
    await cache.queues['test'].put('fifth') 

    # safely exit
    await cache.close()

```


## FastAPI Usage - Cache

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
uvicorn --host 0.0.0.0 --port 8230 basic:app --workers=5
```

## FastAPI Usage - Queue

```python
#basic.py
from fastapi import FastAPI
from easycaching import EasyCache

app = FastAPI()

@app.on_event('startup')
async def start_cache():
    app.cache = await EasyCacheManager.create(
        'test'
    )
    await app.cache.create_queue('test')

@app.post('/queue')
async def create_queue(name: str):
    queue = await app.cache.create_queue(name)
    return f"queue {name} created"

@app.post('/queue/{queue}')
async def add_to_queue(queue: str, data: dict):
    return await cache.queues[queue].put(data)

@app.get('/queue/{queue}')
async def pull_from_queue(queue: str):
    return await cache.queues[queue].get()
```

```bash
uvicorn --host 0.0.0.0 --port 8220 --workers 5 basic:app
```



## Under the Hood
easycaching utilizes the smart caching of [aiopyql](https://github.com/codemation/aiopyql) to provide cache acesss, cache storage, and perhaps most importantly updates and invalidation.

Data access sharing is made possible via proxy methods using [easyrpc](https://github.com/codemation/easyrpc). A cache background task is created & managed by gunicorn which main application workers access via proxies. 

![](docs/images/easycaching-arch.png
)


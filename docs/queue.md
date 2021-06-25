## Queues

EasyCaching Queue is shared & persistent a Queue, backed by a familiar RBDMS.

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

#### Create Queue

```python
    # create queue
    test_queue = await cache.create_queue('test')
```

#### Adding Data to a Queue

```python
    # add items to queue
    await test_queue.put('first')
    await test_queue.put('second')
    await test_queue.put('third')
```

#### Consuming Data from a Queue
Data in queues persist until consumed via .get()

```python
    # grab items from queue
    result = await test_queue.get()
    print(result)
```
```bash
'first'
```

```python
    await test_queue.get() # second
    await test_queue.get() # third
    result = await test_queue.get() # empty
    print(result)
```
```bash
{'warning': 'queue empty'}
```

#### Clearing a Queue
Data is removed when consumed or via .clear()

```python
    await test_queue.clear()
```

#### Accessing Queue via Manager 
Like Cache, Queue is accessible, if already created, via Manager:

```python
    await cache.queues['test'].put('fourth')
    await cache.queues['test'].put('fifth')    
```

#### Safely Exiting EasyCacheManager
```python
    await cache.close()
```


### FastAPI Usage

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
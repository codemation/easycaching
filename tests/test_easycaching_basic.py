import asyncio
import pytest
from easycaching import EasyCacheManager

@pytest.mark.asyncio
async def test_basic_easycache():

    # create EasyCache instance
    cache = await EasyCacheManager.create(
        'test'
    )

    # create cache 
    test = await cache.create_cache('test')
    test_queue = await cache.create_queue('test')

    await test.clear()
    await test_queue.clear()

    # set
    await test.set('foo', 'bar')

    # get
    cached_value = await test.get('foo')
    assert cached_value == 'bar', f"expected value of bar"

    # contains
    assert await test.contains('foo'), f"foo should exist"

    # delete
    await test.delete('foo')
    assert not await test.contains('foo'), f"foo should not exist"


    await test.set('foo', 'bar')
    await test.set('is', 'basic')
    
    # iterating
    KEYS = {'foo', 'is'}
    VALUES = {'bar', 'basic'}

    async for cache_item in test:
        print(cache_item)
        for key, value in cache_item.items():
            assert key in KEYS, f"missing expected key {key}"
            assert value in VALUES, f"mising expected value {value}"

    await test.clear()

    for key in KEYS:
        assert not await test.contains(key), f"{key} should not exist"

    # create queue
    test_queue = await cache.create_queue('test')

    # add items to queue
    await test_queue.put('first')
    await test_queue.put('test1')
    await test_queue.put('test2')

    # grab items from queue
    result = await test_queue.get()
    assert result == 'first', f"expected 'first' as result"

    await test_queue.get()
    await test_queue.get()
    result = await test_queue.get()
    assert 'warning' in result, f"expected queue empty warning, not {result}"

    await test.set('foo', 'bar')
    await test.set('is', 'basic')

    # access items cache via manager

    async for cache_item in cache.cache['test']:
        for key, value in cache_item.items():
            assert key in KEYS, f"missing expected key {key}"
            assert value in VALUES, f"mising expected value {value}"

    
    item = await cache.queues['test'].get()
    assert 'warning' in item, f"expected queue empty warning"

    await cache.queues['test'].put({'test': 'test'})
    item = await cache.queues['test'].get()
    assert 'test' in item, f"expected 'test' in item"

    # load queue & cache for next tests
    await cache.queues['test'].put('first')
    await cache.queues['test'].put('second')
    await cache.queues['test'].put('third')

    await cache.cache['test'].set('first', 'worst')
    await cache.cache['test'].set('second', 'best')
    await cache.cache['test'].set('third', 'treasure chest')

    await cache.close()
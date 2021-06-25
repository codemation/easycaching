import asyncio
import pytest
from easycaching import EasyCacheManager

@pytest.mark.asyncio
async def test_basic_easycache():
    """
    test should follow test_easycaching_basic
    this test should verify persistence of data created
    in first tests.
    """

    # create EasyCache instance
    cache = await EasyCacheManager.create(
        'test'
    )

    await cache.cache['test'].set('first', 'worst')
    await cache.cache['test'].set('second', 'best')
    await cache.cache['test'].set('third', 'treasure chest')

    order = [
        {'first': 'worst'},
        {'second': 'best'},
        {'third': 'treasure chest'}
    ]

    for key_values in order:
        for key, value in key_values.items():
            assert await cache.cache['test'].get(key) == value, (
                f"expected key {key} == {value}"
            )
    
    for value in ['first', 'second', 'third']:
        assert await cache.queues['test'].get() == value, (
            f"expected value {value}"
        )
    
    await cache.close()
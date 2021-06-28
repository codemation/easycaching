import os
import asyncio
import subprocess, signal
from easyrpc.tools.database import EasyRpcProxyDatabase
from easycaching.quorum import quorum_setup

async def get_cache_db(cache, db_proxy_port: int = 8191) -> EasyRpcProxyDatabase:

    await quorum_setup(cache)

    DB_NAME = cache.name
    os.environ['DB_NAME'] = DB_NAME

    if cache.leader:
        # create subprocess for db_proxy
        async def proxy_sub():
            proxy = subprocess.Popen(
                f"gunicorn easycaching.db_proxy:server -w 1 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:{db_proxy_port}".split(' ')
            )
            while True:
                try:
                    status = yield proxy
                    if status == 'finished':
                        proxy.send_signal(signal.SIGINT)
                        proxy.wait()
                        break
                except asyncio.CancelledError:
                    proxy.send_signal(signal.SIGINT)
                    proxy.wait()
                    break
        async def proxy_manager():
            proxy = proxy_sub()
            await proxy.asend(None)
            while True:
                try:
                    await asyncio.sleep(60)
                except asyncio.CancelledError:
                    try:
                        await proxy.asend('finished')
                    except StopAsyncIteration:
                        pass
                    break
        cache.proxy_manager = asyncio.create_task(proxy_manager())

        await asyncio.sleep(3)
    
    RPC_SECRET = os.environ['RPC_SECRET']

    cache_db = await EasyRpcProxyDatabase.create(
        '127.0.0.1', 
        db_proxy_port,
        f'/ws/{DB_NAME}', 
        server_secret=RPC_SECRET,
        namespace=f'{DB_NAME}'
    )

    # check for completeness of db setup
    while not 'liveness' in cache_db.tables:
        print(f"waiting for db setup to complete")
        await asyncio.sleep(2)
    
    if not cache.leader:
        while not 'cache' in cache_db.tables:
            print(f"waiting for leader to complete - db setup")
            await asyncio.sleep(5)
    return cache_db
import os
import asyncio
import subprocess, signal
from typing import AsyncIterable
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
                        proxy.send_signal(signal.SIG_INT)
                        proxy.wait()
                        break
                except asyncio.CancelledError:
                    proxy.send_signal(signal.SIG_INT)
                    proxy.wait()
                    break
        async def proxy_manager():
            proxy = proxy_sub()
            await proxy.asend(None)
            while True:
                try:
                    await asyncio.sleep(60)
                except asyncio.CancelledError:
                    await proxy.asend('finished')
                    break

        asyncio.create_task(proxy_manager())

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
        while not cache.name in cache_db.tables:
            print(f"waiting for leader to complete - db setup")
            await asyncio.sleep(2)
        await cache.quorum_db.tables['quorum'].update(
            ready=True,
            where={'member_id': os.environ['member_id']}
        )
        await asyncio.sleep(1)
        await cache.quorum_db.close()
    else:
        async def db_cleanup():
            while not len(
                await cache.quorum_db.tables['quorum'].select('ready', where={'ready': False})
            ) == 0:
                # leader waiting for members to complete - db setup
                await asyncio.sleep(1)
            await cache.quorum_db.run('drop table quorum')
            await cache.quorum_db.run('drop table env')
            await asyncio.sleep(1)
            await cache.quorum_db.close()
        asyncio.create_task(db_cleanup())
    
    return cache_db
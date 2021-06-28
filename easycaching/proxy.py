import asyncio
import os, time
from asyncio import Queue
from easyrpc.server import EasyRpcServer
from aiopyql.data import Database

def db_proxy_setup(server):

    @server.on_event('startup')
    async def db_setup():
        
        db_config = {}
        # get database type
        db_type = os.environ.get('DB_TYPE')
        db_type = 'sqlite' if not db_type else db_type
        
        db_name = os.environ.get('DB_NAME')
        if not db_name:
            raise Exception(f"missing required DB_NAME environment variable")

        db_config['db_type'] = db_type
        db_config['database'] = db_name
        if db_type in {'mysql', 'postgres'}:
            for cfg in {'HOST','PORT', 'USER', 'PASSWORD'}:
                db_config[cfg.lower()] = os.environ.get(f"DB_{cfg}")
                if not db_config[cfg.lower()]:
                    raise Exception(f"missing required DB_{cfg} environment variable")
        else:
            sqlite_db_path = os.environ.get('DB_LOCAL_PATH')
            if sqlite_db_path:
                db_config['database'] = f"{sqlite_db_path}/{db_name}"
                
        db_config['cache_enabled'] = True
            
        rpc_config = {}
        
        rpc_secret = os.environ.get('RPC_SECRET')

        if not rpc_secret:
            raise Exception(f"missing required RPC_SECRET environment variable")
        rpc_path = os.environ.get('RPC_PATH')

        rpc_config['origin_path'] = rpc_path if rpc_path else f'/ws/{db_name}'
        rpc_config['server_secret'] = rpc_secret

        rcp_enryption = os.environ.get('RPC_ENCRYPTION')
        if rcp_enryption:
            rpc_config['encryption_enabled'] = True if rcp_enryption == 1 else False
        
        rpc_debug = os.environ.get('RPC_DEBUG')
        if rpc_debug:
            rpc_config['debug'] = True if rpc_debug == 'True' else False

        # Rpc Server
        db_server = await EasyRpcServer.create(
            server,
            **rpc_config
        )

        # insert logger
        db_config['log'] = db_server.log

        # Database Conection
        db = await Database.create(
            **db_config
        )

        # register each func table namespace
            
        def register_table(table):
            async def insert(**kwargs):
                return await db.tables[table].insert(**kwargs)
            insert.__name__ = f"{table}_insert"

            async def select(*args, **kwargs):
                return await db.tables[table].select(*args, **kwargs)
            select.__name__ = f"{table}_select"

            async def update(**kwargs):
                return await db.tables[table].update(**kwargs)
            update.__name__ = f"{table}_update"
            
            async def delete(**kwargs):
                return await db.tables[table].delete(**kwargs)
            delete.__name__ = f"{table}_delete"

            async def set_item(key, values):
                return await db.tables[table].set_item(key, values)
            set_item.__name__ = f"{table}_set_item"

            async def get_item(key_val):
                return await db.tables[table][key_val]
            get_item.__name__ = f"{table}_get_item"

            async def get_schema():
                return {
                    table: {
                        "primary_key": db.tables[table].prim_key,
                        "foreign_keys": db.tables[table].foreign_keys,
                        "columns": [
                            {
                                "name": col.name, "type": str(col.type.__name__), "mods": col.mods 
                            } for k, col in db.tables[table].columns.items() 
                        ],
                        "cache_enabled": db.tables[table].cache_enabled,
                        "max_cache_len": db.tables[table].max_cache_len
                    }
                }
            get_schema.__name__ = f"{table}_get_schema"

            for func in {insert, update, select, delete, select, get_schema, set_item, get_item}:
                db_server.origin(func, namespace=db_name)
        for table in db.tables:
            register_table(table)

        @db_server.origin(namespace=db_name)
        async def show_tables():
            table_list = []
            for table in db.tables:
                for func in {'insert', 'select', 'update', 'delete', 'set_item', 'get_item', 'get_schema'}:
                    if not f"{table}_{func}" in db_server.namespaces[db_name]:
                        register_table(table)
                        break
                table_list.append(table)
            return table_list
        
        @db_server.origin(namespace=db_name)
        async def drop_table(table: str):
            result = await db.remove_table(table)
            print(f"drop table result: {result}")
            return f"drop table {table} completed"


        @db_server.origin(namespace=db_name)
        async def create_table(
            name: str, 
            columns: list, 
            prim_key: str,
            **kw
        ):
            result = await db.create_table(
                name=name, 
                columns=columns, 
                prim_key=prim_key, 
                **kw
            )
            await show_tables()
            return result

        server.queues = {}

        cache_ns = db_name

        @db_server.origin(namespace=cache_ns)
        async def ec_cache_setup():
            await db.create_table(
                'queues', 
                [
                    ['queue', 'str', 'UNIQUE NOT NULL'],
                    ['created', 'float']
                ],
                'queue',
                cache_enabled=True
            )

            # create cache table

            await db.create_table(
                'cache', 
                [
                    ['cache', 'str', 'UNIQUE NOT NULL'],
                    ['created', 'float']
                ],
                'cache',
                cache_enabled=True
            )

        @db_server.origin(namespace=cache_ns)
        async def ec_create_cache(cache, cache_size):
            if cache in db.tables:
                raise Exception(f"cache name {cache} already exists")
            
            await db.create_table(
                cache,
                [
                    ['cache_key', 'str', 'UNIQUE NOT NULL'],
                    ['value', 'str'],
                ],
                'cache_key',
                cache_enabled=True,
                max_cache_len=cache_size
            )

            await db.tables['cache'].insert(
                cache=cache,
                created=time.time()
            )

        @db_server.origin(namespace=cache_ns)
        async def ec_create_queue(queue):
            if queue in server.queues:
                raise Exception(f"queue name {queue} already exists")

            server.queues[queue] = Queue()
            await db.create_table(
                name=queue, 
                columns=[
                    ['timestamp', 'float', 'UNIQUE NOT NULL'],
                    ['data', str]
                ], 
                prim_key='timestamp', 
                cache_enabled=True,
            )
            await db.tables['queues'].insert(
                queue=queue
            )
            return f"queue {queue}  created"
        @db_server.origin(namespace=cache_ns)
        async def ec_clear_queue(queue) -> None:
            if not queue in db.tables:
                raise Exception(f"queue name {queue} does not exist")
            items = await db.tables[queue].select('timestamp')
            for item in items:
                await db.tables[queue].delete(
                    where={'timestamp': item['timestamp']}
                )
            server.queues[queue] = Queue()

        @db_server.origin(namespace=cache_ns)
        async def ec_load_cache() -> None:
            caches = await db.tables['cache'].select(
                '*'
            )
            for cache in caches:
                keys = await db.tables[cache['cache']].select('cache_key')
                for key in keys:
                    await db.tables[cache['cache']][key]

        @db_server.origin(namespace=cache_ns)
        async def ec_load_queues():
            queues = await db.tables['queues'].select(
                '*'
            )
            for queue in queues:
                queue_name = queue['queue']

                # create queue
                if not queue_name in server.queues:
                    server.queues[queue_name] = Queue()
                
                # load queue
                queued_items = await db.tables[queue_name].select('*')
                print(queued_items)
                for item in queued_items:
                    timestamp = item['timestamp']
                    await server.queues[queue_name].put({'time': timestamp, 'data': item['data']})
            print(server.queues[queue_name])
            return [queue['queue'] for queue in queues]
        
        @db_server.origin(namespace=cache_ns)
        async def ec_queue_put(queue, data):
            # add data to db
            time_now = time.time()
            await db.tables[queue].insert(
                timestamp=time_now,
                data=data
            )
            await server.queues[queue].put({'time': time_now, 'data': data})
            return {'message': 'added to queue'}

        @db_server.origin(namespace=cache_ns)
        async def ec_queue_get(queue):
            try:
                item = server.queues[queue].get_nowait()
                asyncio.create_task(
                    db.tables[queue].delete(
                        where={'timestamp': item['time']}
                    )
                )
                
                return item['data']
            except asyncio.queues.QueueEmpty:
                return {'warning': 'queue empty'}

        @db_server.origin(namespace=cache_ns)
        async def ec_cache_set(cache_name: str, key: str, value) -> str:
            cache = db.tables[cache_name]
            existing = await cache[key]
            if existing is None:
                result =  await cache.insert(
                    cache_key=key,
                    value=value
                )
                return f"value for {key} added to {cache_name}"
            else:
                result = await cache.update(
                    value=value,
                    where={
                        'cache_key': key
                    }
                )
                return f"value for {key} updated in {cache_name}"
            
        @db_server.origin(namespace=cache_ns)
        async def ec_cache_get(cache: str, key):
            return await db.tables[cache][key]
        
        @db_server.origin(namespace=cache_ns)
        async def ec_cache_get_all(cache):
            for item in await db.tables[cache].select('*'):
                yield {item['cache_key']: item['value']}
            
        
        @db_server.origin(namespace=cache_ns)
        async def ec_cache_delete(cache, key) -> str:
            result =  await db.tables[cache].delete(
                where={'cache_key': key}
            )
            return f"{key} deleted from {cache}"
    
        @db_server.origin(namespace=cache_ns)
        async def ec_cache_clear(cache) -> str:
            keys = await db.tables[cache].select('cache_key')
            for key in keys:
                await db.tables[cache].delete(
                    where={'cache_key': key['cache_key']}
                )
            return f"cache {cache} cleared"

        db_server.origin(db.run, namespace=db_name)

        server.db_server = db_server
        server.db = db


    @server.on_event('shutdown')
    async def shutdown():
        await server.db.close()
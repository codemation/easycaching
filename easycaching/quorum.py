import os, uuid
import asyncio
import subprocess
from aiopyql import data

import random, string
def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

async def quorum_setup(cache): 
    quorum_db = await data.Database.create(
        database='quorum'
    )

    member_id = str(uuid.uuid4())
    cache.member_id = member_id
    os.environ['member_id'] = member_id
    # create table
    await quorum_db.create_table(
        'quorum',
        [
            ('member_id', str, 'UNIQUE NOT NULL'),
            ('leader', bool),
            ('ready', bool)
        ],
        'member_id',
    )

    await quorum_db.create_table(
        'env',
        [
            ('key', str, 'UNIQUE NOT NULL'),
            ('value', str),
        ],
        'key',
    )

    await quorum_db.tables['quorum'].insert(
        member_id=member_id,
        leader=False,
        ready=False
    )
    # waiting for other members to join quorum
    await asyncio.sleep(2)

    # elect leader - first member to join
    
    members = await quorum_db.tables['quorum'].select('*')
    cache.leader = False
    # declare self as leader, since inserted first
    if members[0]['member_id'] == member_id:
        print(f"declaring {member_id} as leader")
        cache.leader = True
        await quorum_db.tables['quorum'].update(
            leader=True,
            ready=True,
            where={'member_id': member_id}
        )

        RPC_SECRET = get_random_string(12)
        await quorum_db.tables['env'].insert(
            key='RPC_SECRET', value=RPC_SECRET
        )

        os.environ['RPC_SECRET'] = RPC_SECRET
        await asyncio.sleep(0.3)

    else:
        await asyncio.sleep(5)
        RPC_SECRET = await quorum_db.tables['env']['RPC_SECRET']
        os.environ['RPC_SECRET'] = RPC_SECRET
    
    cache.quorum_db = quorum_db

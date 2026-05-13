import json
import os
import asyncpg
from enum import Enum


class ExporterSQL(Enum):

    async def execute(self, conn: asyncpg.Connection, *args) -> list[asyncpg.Record]:
        return await conn.fetch(self.value, *args)


def get_env_or_raise(key: str) -> str:
    try:
        return os.environ[key]
    except KeyError:
        print(f'Expected envar {key} was not found')
        print('Provide it please in .env')
        raise RuntimeError


pool: asyncpg.Pool | None = None


async def _init_conn(conn: asyncpg.Connection):
    for pg_type in ('json', 'jsonb'):
        await conn.set_type_codec(
            pg_type,
            encoder=json.dumps,
            decoder=json.loads,
            schema='pg_catalog'
        )


async def connect() -> asyncpg.Pool:
    global pool
    if pool:
        return pool

    pool = await asyncpg.create_pool(
        host=get_env_or_raise('PG_HOST'),
        port=int(get_env_or_raise('PG_PORT')),
        user=get_env_or_raise('PG_USER'),
        password=get_env_or_raise('PG_PASSWORD'),
        database=get_env_or_raise('PG_DBNAME'),
        min_size=int(get_env_or_raise('PG_MIN_CONN_CNT')),
        max_size=int(get_env_or_raise('PG_MAX_CONN_CNT')),
        init=_init_conn
    )

    return pool


async def disconnect():
    global pool

    if pool:
        await pool.close()
        pool = None

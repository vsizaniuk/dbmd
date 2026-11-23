import os
import oracledb
from enum import Enum


class ExporterSQL(Enum):

    def execute(self, cursor: oracledb.Cursor, parameters: tuple = ()):
        cursor.execute(self.value, parameters)


def get_env_or_raise(key: str):
    try:
        return os.environ[key]
    except KeyError:
        print(f'Expected envar {key} was not found')
        print('Provide it please in .env')
        raise RuntimeError


_client_path = os.environ.get('ORA_INSTA_CLIENT_PATH')
_tns_path = os.environ.get('ORA_TNS_PATH')
if _client_path:
    # Thick mode: tnsnames.ora location must be given here (or via TNS_ADMIN);
    # config_dir passed to connect/pool params is ignored by the Instant Client.
    oracledb.init_oracle_client(lib_dir=_client_path, config_dir=_tns_path)


def _pool_params() -> oracledb.PoolParams:
    kwargs = dict(
        user=get_env_or_raise('ORA_USER'),
        password=get_env_or_raise('ORA_PASSWORD'),
        min=int(get_env_or_raise('ORA_MIN_CONN_CNT')),
        max=int(get_env_or_raise('ORA_MAX_CONN_CNT')),
        increment=1,
    )
    if not _client_path and _tns_path:
        # Thin mode: config_dir is honoured only here.
        kwargs['config_dir'] = _tns_path
    return oracledb.PoolParams(**kwargs)


pool: oracledb.ConnectionPool | None = None


def connect():
    global pool
    if pool:
        return pool

    pool = oracledb.create_pool(dsn=get_env_or_raise('ORA_DSN'), params=_pool_params())

    return pool


def disconnect():
    global pool

    if pool:
        pool.close()
        pool = None
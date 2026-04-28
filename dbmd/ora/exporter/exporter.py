import json
import logging
import os
import aiofiles

from abc import ABC, abstractmethod
from typing import AsyncGenerator
from .serializers import MDBaseModel, Dependency, Parameter
from .sql import connect, get_env_or_raise

logger = logging.getLogger(__name__)


class Exporter(ABC):


    def __init__(self, schema: str = None, subdir: str = None):
        self.schema = schema or get_env_or_raise('ORA_SCHEMA')
        self.pool = connect()
        self.connections = []
        self.subdir = subdir

    @staticmethod
    def read_clob_json(clob_json):
        if not clob_json:
            return None

        res = clob_json
        if not isinstance(res, str):
            res = res.read()
        res = json.loads(res)

        return res

    @staticmethod
    def read_clob_str(clob):
        if not clob:
            return None

        res = clob
        if not isinstance(res, str):
            res = res.read()
        return res


    def convert_dependencies(self, dependencies):
        if not isinstance(dependencies, list):
            dependencies = self.read_clob_json(dependencies) or []

        return [Dependency(db_schema=d['db_schema'],
                           type=d['type'],
                           name=d['name']) for d in dependencies]


    def convert_parameters(self, params):
        if not isinstance(params, list):
            params = self.read_clob_json(params) or []

        return [Parameter(name=p['name'],
                          type=p['type'],
                          mode=p['mode'],
                          default=p.get('default')) for p in params]

    @abstractmethod
    def gather_data(self) -> AsyncGenerator[tuple[MDBaseModel, str | None]]:
        ...

    def cleanup(self):
        for conn in self.connections:
            conn.close()
        self.connections.clear()

    async def export_md(self):
        path = os.path.join('.', 'mddb', self.schema, self.subdir)
        os.makedirs(path, exist_ok=True)

        logger.info(f'Starting export: {self.schema}/{self.subdir}')
        count = 0

        async for obj, definition in self.gather_data():
            logger.debug(f'Writing {obj.name}')
            definition_path = None

            if definition:
                definition_path = os.path.join(path, 'definitions', f'{obj.name}.sql')
                os.makedirs(os.path.dirname(definition_path), exist_ok=True)
                async with aiofiles.open(definition_path, 'w', encoding='utf-8') as f:
                    await f.write(definition)

            file_path = os.path.join(path, f'{obj.name}.md')
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(obj.render_md(definition_path=definition_path))

            count += 1

        logger.info(f'Finished export: {self.schema}/{self.subdir} — {count} objects written')

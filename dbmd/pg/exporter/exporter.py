import logging
import os
import aiofiles

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from dbmd.serializers import MDBaseModel, Dependency
from dbmd.pg.exporter.serializers import Parameter
from dbmd.pg.exporter.sql import get_env_or_raise

logger = logging.getLogger(__name__)


class Exporter(ABC):

    def __init__(self, schema: str = None, subdir: str = None):
        self.schema = schema or get_env_or_raise('PG_SCHEMA')
        self.subdir = subdir
        self.name: str | None = None

    @staticmethod
    def convert_dependencies(deps: list | None) -> list[Dependency]:
        if not deps:
            return []
        return [Dependency(type=d['type'], db_schema=d['db_schema'], name=d['name']) for d in deps]

    @staticmethod
    def convert_parameters(params: list | None) -> list[Parameter]:
        if not params:
            return []
        return [Parameter(name=p['name'], type=p['type'], mode=p['mode']) for p in params]

    @abstractmethod
    def gather_data(self) -> AsyncGenerator[tuple[MDBaseModel, str | None]]:
        ...

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

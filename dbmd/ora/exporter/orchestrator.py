import asyncio
import logging
import os

import aiofiles

from dbmd.serializers import SchemaIndex
from .exporter import Exporter
from .sql import get_env_or_raise
from .tables.tables import TablesExporter
from .views.views import ViewsExporter
from .routines.routines import RoutinesExporter
from .packages.packages import PackagesExporter
from .triggers.triggers import TriggersExporter
from .types.object_types import TypesExporter
from .index.sql import get_index

logger = logging.getLogger(__name__)


class Orchestrator:

    def __init__(self, schema: str = None):
        self.schema = schema or get_env_or_raise('ORA_SCHEMA')
        self.tables = TablesExporter(self.schema)
        self.views = ViewsExporter(self.schema)
        self.routines = RoutinesExporter(self.schema)
        self.packages = PackagesExporter(self.schema)
        self.triggers = TriggersExporter(self.schema)
        self.types = TypesExporter(self.schema)

    @staticmethod
    async def _run(exporter: Exporter, name: str | None = None):
        exporter.name = name
        try:
            await exporter.export_md()
        except Exception as e:
            logger.error(f'Export failed for {exporter.subdir}: {e}', exc_info=True)

    async def export_index(self):
        logger.info(f'Starting index export for schema: {self.schema}')

        def query():
            conn = self.tables.pool.acquire()
            try:
                return get_index(conn, self.schema)
            finally:
                conn.close()

        data = await asyncio.to_thread(query)
        index = SchemaIndex(db_schema=self.schema, **data)

        path = os.path.join('.', 'mddb', self.schema)
        os.makedirs(path, exist_ok=True)
        async with aiofiles.open(os.path.join(path, f'{self.schema}.md'), 'w', encoding='utf-8') as f:
            await f.write(index.render_md())

        logger.info(f'Index export complete for schema: {self.schema}')

    async def export_all(self):
        logger.info(f'Starting full export for schema: {self.schema}')
        await asyncio.gather(*[self._run(e) for e in [
            self.tables, self.views, self.routines,
            self.packages, self.triggers, self.types
        ]])
        await self.export_index()
        logger.info(f'Full export complete for schema: {self.schema}')

    async def export_tables(self, name: str | None = None):
        logger.info(f'Starting tables export for schema: {self.schema}')
        await self._run(self.tables, name)
        logger.info(f'Tables export complete for schema: {self.schema}')

    async def export_views(self, name: str | None = None):
        logger.info(f'Starting views export for schema: {self.schema}')
        await self._run(self.views, name)
        logger.info(f'Views export complete for schema: {self.schema}')

    async def export_routines(self, name: str | None = None):
        logger.info(f'Starting routines export for schema: {self.schema}')
        await self._run(self.routines, name)
        logger.info(f'Routines export complete for schema: {self.schema}')

    async def export_packages(self, name: str | None = None):
        logger.info(f'Starting packages export for schema: {self.schema}')
        await self._run(self.packages, name)
        logger.info(f'Packages export complete for schema: {self.schema}')

    async def export_triggers(self, name: str | None = None):
        logger.info(f'Starting triggers export for schema: {self.schema}')
        await self._run(self.triggers, name)
        logger.info(f'Triggers export complete for schema: {self.schema}')

    async def export_types(self, name: str | None = None):
        logger.info(f'Starting types export for schema: {self.schema}')
        await self._run(self.types, name)
        logger.info(f'Types export complete for schema: {self.schema}')

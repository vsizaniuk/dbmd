import asyncio
import logging
import os

import aiofiles

from dbmd.serializers import SchemaIndex
from .exporter import Exporter
from .sql import get_env_or_raise, connect, disconnect
from .tables.tables import TablesExporter
from .views.views import ViewsExporter
from .routines.routines import RoutinesExporter
from .triggers.triggers import TriggersExporter
from .types.types import TypesExporter
from .index.sql import get_index

logger = logging.getLogger(__name__)


class Orchestrator:

    def __init__(self, schema: str = None):
        self.schema   = schema or get_env_or_raise('PG_SCHEMA')
        self.tables   = TablesExporter(self.schema)
        self.views    = ViewsExporter(self.schema)
        self.routines = RoutinesExporter(self.schema)
        self.triggers = TriggersExporter(self.schema)
        self.types    = TypesExporter(self.schema)

    @staticmethod
    async def _run(exporter: Exporter, name: str | None = None):
        exporter.name = name
        try:
            await exporter.export_md()
        except Exception as e:
            logger.error(f'Export failed for {exporter.subdir}: {e}', exc_info=True)

    async def export_index(self):
        logger.info(f'Starting index export for schema: {self.schema}')
        try:
            pool = await connect()
            async with pool.acquire() as conn:
                data = await get_index(conn, self.schema)

            index = SchemaIndex(db_schema=self.schema, **data)

            path = os.path.join('.', 'mddb', self.schema)
            os.makedirs(path, exist_ok=True)
            async with aiofiles.open(os.path.join(path, f'{self.schema}.md'), 'w', encoding='utf-8') as f:
                await f.write(index.render_md())
        finally:
            await disconnect()

        logger.info(f'Index export complete for schema: {self.schema}')

    async def export_all(self):
        logger.info(f'Starting full export for schema: {self.schema}')
        try:
            await asyncio.gather(
                *[self._run(e) for e in [
                    self.tables, self.views, self.routines, self.triggers, self.types
                ]],
                return_exceptions=True
            )
            await self.export_index()
        finally:
            await disconnect()
        logger.info(f'Full export complete for schema: {self.schema}')

    async def export_tables(self, name: str | None = None):
        try:
            await self._run(self.tables, name)
        finally:
            await disconnect()

    async def export_views(self, name: str | None = None):
        try:
            await self._run(self.views, name)
        finally:
            await disconnect()

    async def export_routines(self, name: str | None = None):
        try:
            await self._run(self.routines, name)
        finally:
            await disconnect()

    async def export_triggers(self, name: str | None = None):
        try:
            await self._run(self.triggers, name)
        finally:
            await disconnect()

    async def export_types(self, name: str | None = None):
        try:
            await self._run(self.types, name)
        finally:
            await disconnect()

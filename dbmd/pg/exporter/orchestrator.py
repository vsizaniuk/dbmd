import asyncio
import logging

from .exporter import Exporter
from .sql import get_env_or_raise, disconnect
from .tables.tables import TablesExporter
from .views.views import ViewsExporter
from .routines.routines import RoutinesExporter
from .triggers.triggers import TriggersExporter
from .types.types import TypesExporter

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
    async def _run(exporter: Exporter):
        try:
            await exporter.export_md()
        except Exception as e:
            logger.error(f'Export failed for {exporter.subdir}: {e}', exc_info=True)

    async def export_all(self):
        logger.info(f'Starting full export for schema: {self.schema}')
        try:
            await asyncio.gather(
                *[self._run(e) for e in [
                    self.tables, self.views, self.routines, self.triggers, self.types
                ]],
                return_exceptions=True
            )
        finally:
            await disconnect()
        logger.info(f'Full export complete for schema: {self.schema}')

    async def export_tables(self):
        try:
            await self._run(self.tables)
        finally:
            await disconnect()

    async def export_views(self):
        try:
            await self._run(self.views)
        finally:
            await disconnect()

    async def export_routines(self):
        try:
            await self._run(self.routines)
        finally:
            await disconnect()

    async def export_triggers(self):
        try:
            await self._run(self.triggers)
        finally:
            await disconnect()

    async def export_types(self):
        try:
            await self._run(self.types)
        finally:
            await disconnect()

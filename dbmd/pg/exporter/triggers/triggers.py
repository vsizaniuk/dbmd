from typing import AsyncGenerator

from dbmd.serializers import MDBaseModel
from dbmd.pg.exporter.exporter import Exporter
from dbmd.pg.exporter.sql import connect
from dbmd.pg.exporter.triggers import sql
from .serializer import TriggerDetails


class TriggersExporter(Exporter):

    def __init__(self, schema: str = None, subdir: str = 'triggers'):
        super().__init__(schema, subdir)

    async def gather_data(self) -> AsyncGenerator[tuple[MDBaseModel, str | None]]:
        pool = await connect()
        async with pool.acquire() as conn:
            triggers = await sql.get_triggers(conn, self.schema)

        for row in triggers:
            trigger = TriggerDetails(
                db_schema=row['db_schema'],
                name=row['trigger_name'],
                table_name=row['table_name'],
                trigger_type=row['trigger_type'],
                timing=row['timing'],
                events=list(row['events']),
                enabled=row['enabled'],
                function_schema=row['function_schema'],
                function_name=row['function_name'],
                definition=row['definition']
            )
            yield trigger, None

import asyncio
from collections.abc import AsyncGenerator

from dbmd.ora.exporter.exporter import Exporter
from dbmd.ora.exporter.serializers import MDBaseModel

from dbmd.ora.exporter.triggers import sql
from .serializer import TriggerDetails


class TriggersExporter(Exporter):

    def __init__(self, schema: str = None, subdir: str = 'triggers'):
        super().__init__(schema, subdir)


    async def get_triggers(self):

        def query_f():
            conn = self.pool.acquire()
            self.connections.append(conn)

            return sql.get_triggers(conn, self.schema, self.name)

        return await asyncio.to_thread(query_f)


    async def get_triggers_details(self):

        def query_f():
            conn = self.pool.acquire()
            self.connections.append(conn)

            return sql.get_triggers_definitions(conn, self.schema, self.name)

        return await asyncio.to_thread(query_f)


    async def gather_data(self) -> AsyncGenerator[tuple[MDBaseModel, str | None]]:

        try:

            triggers = await self.get_triggers()
            triggers_definitions = {f'{db_schema}_{trigger_name}': (signature, definition)
                                    for db_schema, trigger_name, signature, definition
                                    in await self.get_triggers_details()}

            for (db_schema, trigger_name, table_name,
                 trigger_type, triggering_event, status, dependencies) in triggers:

                signature, definition = triggers_definitions.get(f'{db_schema}_{trigger_name}')

                signature = self.read_clob_json(signature) or []
                definition = self.read_clob_json(definition) or []

                signature = ''.join(signature)
                definition = ''.join(definition)
                if definition:
                    definition += '/\n'

                trigger = TriggerDetails(db_schema=db_schema,
                                         name=trigger_name,
                                         status=status,
                                         trigger_type=trigger_type,
                                         event=triggering_event,
                                         table_name=table_name,
                                         dependencies=self.convert_dependencies(dependencies),
                                         signature=signature)

                yield trigger, definition

        finally:
            self.cleanup()

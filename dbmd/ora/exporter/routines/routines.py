import asyncio
from collections.abc import AsyncGenerator

from dbmd.ora.exporter.exporter import Exporter
from dbmd.ora.exporter.serializers import MDBaseModel

from dbmd.ora.exporter.routines import sql
from .serializer import Function, Procedure


class RoutinesExporter(Exporter):

    def __init__(self, schema: str = None, subdir: str = 'routines'):
        super().__init__(schema, subdir)


    async def get_routines(self):

        def query_f():
            conn = self.pool.acquire()
            self.connections.append(conn)

            return sql.get_routines(conn, self.schema, self.name)

        return await asyncio.to_thread(query_f)


    async def gather_data(self) -> AsyncGenerator[tuple[MDBaseModel, str | None]]:
        try:

            routines = await self.get_routines()

            for (routine_name, routine_type, dependencies, params,
                 return_type, signature, definition) in routines:

                params = self.convert_parameters(params)
                dependencies = self.convert_dependencies(dependencies)
                signature = self.read_clob_json(signature) or []
                signature = ''.join(signature)

                definition = self.read_clob_json(definition) or []
                definition = ''.join(definition) + '\n/\n' if definition else None

                common_params = dict(db_schema=self.schema, name=routine_name, parameters=params,
                                     dependencies=dependencies, signature=signature)

                if routine_type == 'FUNCTION':
                    routine = Function(
                        **common_params,
                        return_type=return_type
                    )
                elif routine_type == 'PROCEDURE':
                    routine = Procedure(**common_params)
                else:
                    continue

                yield routine, definition

        finally:
            self.cleanup()

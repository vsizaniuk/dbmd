from collections.abc import AsyncGenerator

from dbmd.serializers import MDBaseModel
from dbmd.pg.exporter.exporter import Exporter
from dbmd.pg.exporter.sql import connect
from dbmd.pg.exporter.routines import sql
from .serializer import Function, Procedure


class RoutinesExporter(Exporter):

    def __init__(self, schema: str = None, subdir: str = 'routines'):
        super().__init__(schema, subdir)

    async def gather_data(self) -> AsyncGenerator[tuple[MDBaseModel, str | None]]:
        pool = await connect()
        async with pool.acquire() as conn:
            routines = await sql.get_routines(conn, self.schema, self.name)

        for row in routines:
            params = self.convert_parameters(row['parameters'])
            deps   = self.convert_dependencies(row['dependencies'])

            common = dict(
                db_schema=self.schema,
                name=row['name'],
                signature=row['signature'],
                parameters=params,
                dependencies=deps
            )

            if row['routine_type'] == 'FUNCTION':
                routine = Function(**common, return_type=row['return_type'])
            elif row['routine_type'] == 'PROCEDURE':
                routine = Procedure(**common)
            else:
                continue

            yield routine, row['definition']

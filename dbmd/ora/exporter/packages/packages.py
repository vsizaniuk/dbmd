import asyncio
from typing import AsyncGenerator

from dbmd.ora.exporter.exporter import Exporter
from dbmd.ora.exporter.serializers import MDBaseModel, ObjectTypes

from dbmd.ora.exporter.packages import sql
from .serializer import PackagePublicRoutine, Package


class PackagesExporter(Exporter):

    def __init__(self, schema: str = None, subdir: str = 'packages'):
        super().__init__(schema, subdir)


    async def get_packages(self):

        def query_f():
            conn = self.pool.acquire()
            self.connections.append(conn)

            return sql.get_packages(conn)

        return await asyncio.to_thread(query_f)


    async def get_packages_definitions(self):

        def query_f():
            conn = self.pool.acquire()
            self.connections.append(conn)

            return sql.get_packages_definitions(conn)

        return await asyncio.to_thread(query_f)

    def convert_public_routine(self, routines):

        routines = self.read_clob_json(routines) or dict()
        res = []

        for routine_name, definition in routines.items():
            routine_name, overload_num = routine_name.split(sep='~')

            routine_type = ObjectTypes[definition['type']]
            params = self.convert_parameters(definition['parameters'])

            res.append(PackagePublicRoutine(name=routine_name,
                                            type=routine_type,
                                            overload=int(overload_num or 0),
                                            parameters=params,
                                            return_type=definition['return_type']))

        return res



    async def gather_data(self) -> AsyncGenerator[tuple[MDBaseModel, str | None]]:

        try:

            packages = await self.get_packages()
            definitions = {f'{name}~{o_type}': definition for name, o_type, definition in await self.get_packages_definitions()}

            for (package_name, has_body, dependencies, public_routines) in packages:

                dependencies = self.read_clob_json(dependencies) or dict()

                spec_deps = self.convert_dependencies(dependencies.get('PACKAGE'))
                body_deps = self.convert_dependencies(dependencies.get('PACKAGE BODY'))
                public_routines = self.convert_public_routine(public_routines)

                package = Package(db_schema=self.schema,
                                  name=package_name,
                                  spec_dependencies=spec_deps,
                                  body_dependencies=body_deps,
                                  has_body=bool(has_body),
                                  public_routines=public_routines)

                spec_definition = self.read_clob_json(definitions.get(f'{package_name}~PACKAGE')) or []
                body_definition = self.read_clob_json(definitions.get(f'{package_name}~PACKAGE BODY')) or []

                if spec_definition:
                    definition = ''.join(spec_definition) + '\n/\n' + ''.join(body_definition)
                else:
                    definition = None

                yield package, definition

        finally:
            self.cleanup()

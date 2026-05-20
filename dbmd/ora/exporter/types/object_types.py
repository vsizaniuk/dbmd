import asyncio
from collections.abc import AsyncGenerator

from dbmd.ora.exporter.exporter import Exporter
from dbmd.ora.exporter.serializers import ColumnType, MDBaseModel

from dbmd.ora.exporter.types import sql
from .serializer import OTAttribute, OTMethod, ObjectTypeDetails, CollectionTypeDetails, CollectionTypes, ScalarType


class TypesExporter(Exporter):

    def __init__(self, schema: str = None, subdir: str = 'types'):
        super().__init__(schema, subdir)


    async def get_collection_types(self):

        def query_f():
            conn = self.pool.acquire()
            self.connections.append(conn)

            return sql.get_collection_types(conn, self.schema)

        return await asyncio.to_thread(query_f)

    async def get_scalar_types(self):

        def query_f():
            conn = self.pool.acquire()
            self.connections.append(conn)

            return sql.get_scalar_types(conn, self.schema)

        return await asyncio.to_thread(query_f)

    async def get_object_types(self):

        def query_f():
            conn = self.pool.acquire()
            self.connections.append(conn)

            return sql.get_object_types(conn, self.schema)

        return await asyncio.to_thread(query_f)

    async def get_object_types_definitions(self):

        def query_f():
            conn = self.pool.acquire()
            self.connections.append(conn)

            return sql.get_object_types_definitions(conn, self.schema)

        return await asyncio.to_thread(query_f)

    def convert_ot_attributes(self, attributes):

        attributes = self.read_clob_json(attributes) or []

        res = [OTAttribute(name=attr['name'],
                           datatype=ColumnType(**attr['type']),
                           inherited=bool(attr['inherited']))
               for attr in attributes]

        return res


    def convert_ot_methods(self, methods):

        methods = self.read_clob_json(methods) or []

        res = [OTMethod(name=m['name'],
                        parameters_cnt=m['parameters_cnt'],
                        type=m['type'],
                        is_function=bool(m['is_function']),
                        final=bool(m['is_final']),
                        instantiable=bool(m['is_instantiable']),
                        is_overriding=bool(m['is_overriding']),
                        is_inherited=bool(m['is_inherited']))
               for m in methods]

        return res


    async def gather_data(self) -> AsyncGenerator[tuple[MDBaseModel, str | None]]:
        try:

            collection_types = await self.get_collection_types()
            scalar_types = await self.get_scalar_types()
            object_types = await self.get_object_types()
            definitions = {f'{name}~{o_type}': definition for name, o_type, definition in
                           await self.get_object_types_definitions()}

            for type_name, col_type_type, dependencies, definition in collection_types:

                dependencies = self.convert_dependencies(dependencies)
                definition = self.read_clob_json(definition) or []
                definition = ''.join(definition)

                collection_type = CollectionTypeDetails(db_schema=self.schema,
                                                        collection_type=CollectionTypes[col_type_type],
                                                        name=type_name,
                                                        dependencies=dependencies,
                                                        definition=definition)

                yield collection_type, None

            for type_name, definition in scalar_types:
                definition = self.read_clob_json(definition) or []
                definition = ''.join(definition)

                scalar_type = ScalarType(db_schema=self.schema,
                                         name=type_name,
                                         definition=definition)

                yield scalar_type, None

            for object_type, dependencies, attributes, methods in object_types:
                object_type = self.read_clob_json(object_type) or dict()
                dependencies = self.convert_dependencies(dependencies)
                attributes = self.convert_ot_attributes(attributes)
                methods = self.convert_ot_methods(methods)

                ot_name = object_type['name']

                ot = ObjectTypeDetails(db_schema=self.schema,
                                       name=ot_name,
                                       has_methods=object_type['methods_cnt'] > 0,
                                       attributes=attributes,
                                       methods=methods,
                                       dependencies=dependencies)

                spec_definition = self.read_clob_json(definitions.get(f'{ot_name}~TYPE')) or []
                body_definition = self.read_clob_json(definitions.get(f'{ot_name}~TYPE BODY')) or []

                if spec_definition:
                    definition = ''.join(spec_definition) + '\n/\n' + ''.join(body_definition)
                else:
                    definition = None

                yield ot, definition

        finally:
            self.cleanup()
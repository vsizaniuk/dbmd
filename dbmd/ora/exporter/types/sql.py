from oracledb import Connection

from dbmd.ora.exporter.sql import ExporterSQL


class TypesSQL(ExporterSQL):

    select_collection_types = '''
    with dependencies as
         (select ud.name,
                 json_arrayagg(json_object('type' value lower(ud.referenced_type),
                                           'db_schema' value ud.referenced_owner,
                                           'name' value ud.referenced_name)
                               returning clob) as dependencies
            from all_dependencies ud
            join all_types ut
              on ut.type_name = ud.name
             and ud.owner = ut.owner
           where ut.typecode = 'COLLECTION'
             and ud.referenced_owner != 'SYS'
             and ut.owner = :schema
           group by ud.name)
        select t.type_name, 
               t.collection_type,
               d.dependencies, 
               t.definition
          from (select t.type_name,
                       max(case when lower(s.text) like '%varray%' then 'VARRAY' 
                                when lower(s.text) like '%table%' then 'TABLE' end) as collection_type,
                       json_arrayagg(s.text order by s.line returning clob) as definition
                  from all_types t
                  left join all_source s
                    on t.type_name = s.name
                   and t.owner = s.owner
                   and s.type = 'TYPE'
            
                 where t.typecode = 'COLLECTION'
                   and t.owner = :schema
                 group by t.type_name) t
          left join dependencies d
            on t.type_name = d.name
    '''

    select_scalar_types = '''
    select t.type_name,
           json_arrayagg(s.text order by s.line returning clob) as definition
      from all_types t
      left join all_source s
        on t.type_name = s.name
       and t.owner = s.owner
       and s.type = 'TYPE'
     where t.typecode != 'COLLECTION'
       and t.owner = :schema
       and not exists
     (select 1 from all_type_attrs a where a.type_name = t.type_name and a.owner = t.owner)
     group by t.type_name
    '''

    select_object_types = '''
    with dependencies as
         (select ud.name,
                 json_arrayagg(json_object('type' value lower(ud.referenced_type),
                                           'db_schema' value ud.referenced_owner,
                                           'name' value ud.referenced_name)
                               returning clob) as dependencies
            from all_dependencies ud
            join all_types ut
              on ut.type_name = ud.name
             and ud.owner = ut.owner
           where ut.typecode = 'OBJECT'
             and ud.referenced_owner != 'SYS'
             and ut.owner = :schema
           group by ud.name),
        attribs as
         (select t.type_name,
                 json_arrayagg(json_object('name' value t.attr_name,
                                           'inherited' value t.inherited,
                                           'type' value json_object('name' value t.attr_type_name,
                                                                    'length' value t.length,
                                                                    'precision' value t.precision,
                                                                    'scale' value t.scale)) 
                                order by t.attr_no returning clob) as "attributes"
        
            from all_type_attrs t
           where t.owner = :schema
           group by t.type_name),
        methods as
         (select t.type_name,
                 json_arrayagg(json_object('name' value t.method_name,
                                           'type' value t.method_type,
                                           'parameters_cnt' value t.parameters,
                                           'is_function' value t.results,
                                           'is_final' value t.final,
                                           'is_instantiable' value t.instantiable,
                                           'is_overriding' value t.overriding,
                                           'is_inherited' value t.inherited) order by
                               t.method_no returning clob) as methods
        
            from all_type_methods t
           where t.owner = :schema
           group by t.type_name)
        
        select json_object('super_owner' value t.supertype_owner,
                           'super_name' value t.supertype_name,
                           'name' value t.type_name,
                           'attributes_cnt' value t.attributes,
                           'methods_cnt' value t.methods) as "object_type",
               d.dependencies,
               a."attributes",
               m.methods
        
          from all_types t
          left join attribs a
            on t.type_name = a.type_name
          left join dependencies d
            on t.type_name = d.name
          left join methods m
            on t.type_name = m.type_name
        
         where t.typecode = 'OBJECT'
           and t.owner = :schema
           and exists
         (select 1 from user_type_attrs a where a.type_name = t.type_name)
    '''

    select_object_types_definitions = '''
        select t.name as type_name,
               t.type,
               json_arrayagg(t.text order by t.LINE returning clob) as definition
        
          from all_source t
         where t.type in ('TYPE BODY', 'TYPE')
           and t.owner = :schema
         group by t.name, t.type
        '''

def get_collection_types(conn: Connection, schema: str):

    with conn.cursor() as cur:
        TypesSQL.select_collection_types.execute(cur, {'schema': schema})

        return cur.fetchall()

def get_scalar_types(conn: Connection, schema: str):

    with conn.cursor() as cur:
        TypesSQL.select_scalar_types.execute(cur, {'schema': schema})

        return cur.fetchall()

def get_object_types(conn: Connection, schema: str):

    with conn.cursor() as cur:
        TypesSQL.select_object_types.execute(cur, {'schema': schema})

        return cur.fetchall()

def get_object_types_definitions(conn: Connection, schema: str):

    with conn.cursor() as cur:
        TypesSQL.select_object_types_definitions.execute(cur, {'schema': schema})

        return cur.fetchall()

from oracledb import Connection

from dbmd.ora.exporter.sql import ExporterSQL


class PackagesSQL(ExporterSQL):

    select_packages = '''
    with dependencies as
         (select t.name,
                 json_objectagg(t.object_type value t.dependencies returning clob) as dependencies
            from (select ud.name,
                         p.object_type,
                         json_arrayagg(json_object('type' value lower(ud.referenced_type),
                                                   'db_schema' value ud.referenced_owner,
                                                   'name' value ud.referenced_name)
                                       returning clob) as dependencies
                    from all_dependencies ud
                    join all_objects p
                      on ud.name = p.object_name
                     and ud.type = p.object_type
                     and ud.owner = p.owner
                     and p.object_type in ('PACKAGE BODY', 'PACKAGE')
        
                   where ud.referenced_owner != 'SYS'
                     and p.owner = :schema
                     and (:name is null or p.object_name = :name)
                   group by ud.name, p.object_type) t
        
           group by t.name),
        public_routines as
         (select t.package_name,
                 json_objectagg(t.object_name || '~' || t.overload value
                                json_object('type' value case
                                              when t.return_type is not null then
                                               'FUNCTION'
                                              else
                                               'PROCEDURE'
                                            end,
                                            'parameters' value t.params,
                                            'return_type' value t.return_type
                                            returning clob) returning clob) as routines
            from (select a.package_name,
                         a.object_name,
                         a.overload,
                         json_arrayagg(case
                                         when a.position > 0 then
                                          json_object('name' value a.argument_name,
                                                      'mode' value a.in_out,
                                                      'type' value a.data_type)
                                       end order by a.position returning clob) as params,
                         max(case
                               when a.position = 0 then
                                a.data_type
                             end) as return_type
        
                    from all_arguments a
        
                   where a.package_name is not null
                     and a.owner = :schema
                     and (:name is null or a.package_name = :name)
                   group by a.package_name, a.object_name, a.overload
        
                  ) t
           group by t.package_name)
        
        select t.object_name as package_name,
               case
                 when pb.object_name is not null then
                  1
                 else
                  0
               end as has_body,
               d.dependencies,
               pr.routines as public_routines
        
          from all_objects t
          left join all_objects pb
            on t.object_name = pb.object_name
           and t.owner = pb.owner
           and pb.object_type = 'PACKAGE BODY'
          left join dependencies d
            on t.object_name = d.name
          left join public_routines pr
            on t.object_name = pr.package_name
        
         where t.object_type = 'PACKAGE'
           and t.owner = :schema
           and (:name is null or t.object_name = :name)
    '''

    select_packages_definitions = '''
    select t.name as package_name,
           t.type,
           json_arrayagg(t.text order by t.LINE returning clob) as definition
        
      from all_source t
     where t.type in ('PACKAGE BODY', 'PACKAGE')
       and t.owner = :schema
       and (:name is null or t.name = :name)
       and not exists (
               select 1
                 from all_source s
                where s.owner = t.owner
                  and s.name  = t.name
                  and s.type  = t.type
                  and asciistr(s.text) != s.text
           )
     group by t.name, t.type
    '''


def get_packages(conn: Connection, schema: str, name: str | None = None):

    with conn.cursor() as cur:
        PackagesSQL.select_packages.execute(cur, {'schema': schema, 'name': name})

        return cur.fetchall()


def get_packages_definitions(conn: Connection, schema: str, name: str | None = None):

    with conn.cursor() as cur:
        PackagesSQL.select_packages_definitions.execute(cur, {'schema': schema, 'name': name})

        return cur.fetchall()

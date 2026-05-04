from oracledb import Connection

from dbmd.ora.exporter.sql import ExporterSQL

class RoutinesSQL(ExporterSQL):

    select_routines = '''
    with routine_data as (
        select t.name,
               json_arrayagg(t.signature order by t.line returning clob) as signature,
               json_arrayagg(t.text order by t.line returning clob) as definition
        from (
        select t.name,
               t.line,
               t.text,
               case
                 when t.line < min(case
                                     when regexp_like(t.text, '(is|as)\s', 'i') 
                                          and not regexp_like(t.text, '--.*(is|as)\s') then
                                      t.line
                                   end) over(partition by t.name) then
                  t.text
               end as signature
        
          from all_source t
          join all_procedures up
            on t.name = up.object_name
           and t.owner = up.owner
         where up.object_type in ('PROCEDURE', 'FUNCTION')
           and :schema = all(t.owner, up.owner)) t
         group by t.name
        ), params_data as (
        select a.object_name,
               json_arrayagg(case when a.position > 0 then
                                  json_object('name' value a.argument_name,
                                              'mode' value a.in_out,
                                              'type' value a.data_type) end
                             order by a.position
                                              returning clob) as "parameters",
               max(case when a.position = 0 then a.data_type end) as return_type
          from all_arguments a
          join all_procedures up
            on a.object_name = up.object_name
           and a.owner = up.owner
         where up.object_type in ('PROCEDURE', 'FUNCTION')
           and :schema = all(a.owner, up.owner)
         group by a.object_name
        ), dependencies as (
        select ud.name,
               json_arrayagg(json_object('type' value lower(ud.referenced_type),
                                         'db_schema' value ud.referenced_owner,
                                         'name' value ud.referenced_name) returning clob) as dependencies
          from all_dependencies ud
          join all_procedures up
            on up.object_name = ud.name
         where up.object_type in ('PROCEDURE', 'FUNCTION')
           and ud.referenced_owner != 'SYS'
           and :schema = all(ud.owner, up.owner)
         group by ud.name
        )
        select t.object_name,
               t.object_type,
               ud.dependencies,
               a."parameters",
               a.return_type,
               rd.signature,
               rd.definition
        
          from all_procedures t
          left join dependencies ud
            on t.object_name = ud.name
          left join params_data a
            on t.object_name = a.object_name
          left join routine_data rd
            on t.object_name = rd.name
        
         where t.object_type in ('PROCEDURE', 'FUNCTION')
           and t.owner = :schema
    '''

def get_routines(conn: Connection, schema: str):

    with conn.cursor() as cur:
        RoutinesSQL.select_routines.execute(cur, {'schema': schema})

        return cur.fetchall()

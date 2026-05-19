from oracledb import Connection

from dbmd.ora.exporter.sql import ExporterSQL


class TriggersSQL(ExporterSQL):

    select_triggers = '''
    select tr.owner as db_schema,
           tr.trigger_name,
           tr.table_name,
           tr.trigger_type,
           tr.triggering_event,
           tr.status,
           json_arrayagg(json_object('type' value lower(dep.referenced_type),
                                     'db_schema' value dep.referenced_owner,
                                     'name' value dep.referenced_name) order by dep.referenced_owner,
                         dep.referenced_name returning clob) as dependencies
    
      from all_triggers tr
      left join all_dependencies dep
        on tr.trigger_name = dep.name
       and tr.owner = dep.owner
       and dep.type = 'TRIGGER'
       and dep.referenced_owner != 'SYS'
    
     where :schema = any(tr.owner, tr.table_owner)
     group by tr.owner,
              tr.trigger_name,
              tr.table_name,
              tr.trigger_type,
              tr.triggering_event,
              tr.status
    '''

    select_triggers_definitions = '''
    with definitions as (
         select x.name, 
                json_arrayagg(x.signature order by x.line returning clob) as signature,
                json_arrayagg(x.text order by x.line returning clob) as definition
           from (select t.name,
                        t.line,
                        case
                          when t.line < min(case
                                              when regexp_like(t.TEXT, '(^|[^[:alpha:]])(declare|begin)([^[:alpha:]]|$)', 'i') then
                                               t.line
                                            end) over(partition by t.name) then
                           t.text
                        end as signature,
                        t.text
                   from all_source t
                           
                  where t.type = 'TRIGGER'
                    and t.owner = :schema
                    and not exists (
                            select 1
                              from all_source s
                             where s.owner = t.owner
                               and s.name  = t.name
                               and s.type  = t.type
                               and asciistr(s.text) != s.text
                        )
                  ) x
        group by x.name), 
       trigger_list as (
           select tr.owner, tr.trigger_name
             from all_triggers tr
            where :schema = any(tr.owner, tr.table_owner)
            group by tr.owner, tr.trigger_name
        )
              
    select t.owner, 
           t.trigger_name,
           case when d.signature is null then 
             (
                select json_arrayagg(x.signature order by x.line returning clob) as signature 
                  from (select i.name,
                               i.line,
                               case
                                 when i.LINE < min(case
                                                     when regexp_like(i.TEXT, '(^|[^[:alpha:]])(declare|begin)([^[:alpha:]]|$)', 'i') then
                                                      i.LINE
                                                   end) over(partition by i.name) then
                                  i.TEXT
                               end as signature
                          from all_source i
                         where i.type = 'TRIGGER' 
                           and i.owner = t.owner 
                           and i.name = t.trigger_name
                  ) x
             ) else d.signature end as signature,
          case when d.definition is null then 
             (
                select json_arrayagg(x.definition order by x.line returning clob) as definition 
                  from (select i.name,
                               i.line,
                               case
                                 when i.LINE < min(case
                                                     when regexp_like(i.TEXT, '(^|[^[:alpha:]])(declare|begin)([^[:alpha:]]|$)', 'i') then
                                                      i.LINE
                                                   end) over(partition by i.name) then
                                  i.TEXT
                               end as definition
                          from all_source i
                         where i.type = 'TRIGGER' 
                           and i.owner = t.owner 
                           and i.name = t.trigger_name
                  ) x
             ) else d.definition end as definition
           
      from trigger_list t
      left join definitions d
        on t.trigger_name = d.name 
       and t.owner = :schema
    '''


def get_triggers(conn: Connection, schema: str):

    with conn.cursor() as cur:
        TriggersSQL.select_triggers.execute(cur, {'schema': schema})

        return cur.fetchall()


def get_triggers_definitions(conn: Connection, schema: str):

    with conn.cursor() as cur:
        TriggersSQL.select_triggers_definitions.execute(cur, {'schema': schema})

        return cur.fetchall()

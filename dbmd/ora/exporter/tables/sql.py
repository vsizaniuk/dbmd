from oracledb import Connection

from dbmd.ora.exporter.sql import ExporterSQL


class TablesSQL(ExporterSQL):

    select_tables = '''
    with
      function long_to_varchar(p_schema varchar2, p_table varchar2, p_column varchar2) return varchar2 is
        l_val varchar2(4000);
        l_long_val long;
      begin
        select data_default
          into l_long_val
          from all_tab_columns
         where table_name = p_table
           and column_name = p_column
           and owner = p_schema;
               
        l_val := substr(l_long_val, 1, 4000);
        return l_val;
      exception
        when no_data_found then
          return null;
      end;
          
    select t.table_name,
           tc.comments as "description",
           col."columns",
           t.num_rows as row_count
        
      from all_tables t
      left join all_tab_comments tc 
        on t.table_name = tc.table_name
       and t.owner = tc.owner 
      left join lateral (select json_arrayagg(json_object('name' value c.column_name,
                                                          'type' value json_object('name' value c.data_type,
                                                                                   'length' value c.data_length,
                                                                                   'precision' value c.data_precision,
                                                                                   'scale' value c.data_scale),
                                                          'nullable' value c.nullable,
                                                          'default' value long_to_varchar(c.owner, c.table_name,c.column_name), 
                                                          'description' value cc.comments) returning clob) as "columns"
                           from all_tab_columns c
                           join all_col_comments cc
                             on c.table_name = cc.table_name
                            and c.column_name = cc.column_name
                            and c.owner = cc.owner 
                          where t.table_name = c.table_name
                            and t.owner = cc.owner) col
        on 1 = 1
      
      where t.owner = :schema
         
     order by t.table_name
    '''

    select_table_constraints = '''
    select t.table_name,
           json_arrayagg (
               json_object(
                  'schema' value t.owner,
                  'constraint_type' value t.constraint_type,
                  'constraint_name' value t.constraint_name,
                  'delete_rule' value t.delete_rule,
                  'constrained_columns' value t.constrained_columns,
                  'ref_constraint' value t.ref_constraint
               ) returning clob) as "constraints"
      from (
    select cons.owner,
           cons.table_name,
           cons.constraint_type,
           cons.constraint_name,
           cons.delete_rule,
           json_arrayagg(cons_c.column_name order by cons_c.position) 
               as constrained_columns,
           case when cons.constraint_type = 'R' then 
           json_object(
             'schema'  value cons.r_owner,
             'table'   value ref_cons.table_name,
             'columns' value json_arrayagg(ref_c.column_name order by ref_c.position)
           ) end as ref_constraint
        
    from all_constraints cons
        
    join all_cons_columns cons_c
      on cons.constraint_name = cons_c.constraint_name
     and cons.owner = cons_c.owner
        
    left join all_constraints ref_cons
      on cons.r_owner = ref_cons.owner
     and cons.r_constraint_name = ref_cons.constraint_name
        
    left join all_cons_columns ref_c
      on ref_cons.constraint_name = ref_c.constraint_name
     and ref_cons.owner = ref_c.owner
     and ref_c.position = cons_c.position
        
    where cons.constraint_type in ('U', 'R', 'P')
      and cons.owner = :schema
        
    group by cons.owner,
             cons.table_name,
             cons.constraint_type,
             cons.constraint_name,
             cons.delete_rule,
             cons.r_owner,
             ref_cons.table_name) t
        
    group by t.table_name
    '''

    select_table_triggers = '''
    select tr.table_name,
           json_arrayagg(
             json_object(
             'db_schema' value tr.owner,
             'name' value tr.trigger_name,
             'type' value tr.trigger_type,
             'event' value tr.triggering_event,
             'status' value tr.status
             )) as "triggers"
      from all_triggers tr
     where tr.table_owner = :schema
       and tr.base_object_type = 'TABLE'
    group by tr.table_name
    order by tr.table_name
    '''

    select_table_indexes = '''
    with
      function long_to_varchar(p_schema varchar2, p_index varchar2, p_table in varchar2) return varchar2 is
        l_val varchar2(4000);
      begin
            
        for rec in (
        select t.column_expression
          from all_ind_expressions t
         where t.table_name = p_table
           and t.index_name = p_index
           and t.index_owner = p_schema
         order by t.column_position) loop
           if l_val is null then 
             l_val := substr(rec.column_expression, 1, 4000);
           else 
             l_val := l_val || ':' || substr(rec.column_expression, 1, 4000);
           end if;
        end loop;
            
        return l_val;
      end;
        
    select table_name,
           json_arrayagg("index" returning clob) as "indexes"
      from (
    select i.table_name,
           json_object(
           'db_schema' value i.owner,
           'name' value i.index_name,
           'type' value i.index_type,
           'columns' value json_arrayagg(ic.column_name order by ic.column_position),
           'expression' value long_to_varchar(i.owner, i.index_name, i.table_name)
           ) as "index"
               
      from all_indexes i
      join all_ind_columns ic 
        on i.index_name = ic.index_name
       and i.table_name = ic.table_name
       and i.owner = ic.index_owner
          
     where i.index_type != 'LOB'
       and i.table_owner = :schema
     group by i.owner,
           i.table_name,
           i.index_name,
           i.index_type
     order by i.table_name) t
    group by table_name
    '''


def get_tables(conn: Connection, schema: str):

    with conn.cursor() as cur:
        TablesSQL.select_tables.execute(cur, {'schema': schema})

        return cur.fetchall()


def get_table_constraints(conn: Connection, schema: str):

    with conn.cursor() as cur:
        TablesSQL.select_table_constraints.execute(cur, {'schema': schema})

        return cur.fetchall()


def get_table_triggers(conn: Connection, schema: str):

    with conn.cursor() as cur:
        TablesSQL.select_table_triggers.execute(cur, {'schema': schema})

        return cur.fetchall()


def get_table_indexes(conn: Connection, schema: str):

    with conn.cursor() as cur:
        TablesSQL.select_table_indexes.execute(cur, {'schema': schema})

        return cur.fetchall()

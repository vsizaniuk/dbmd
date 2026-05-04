from oracledb import Connection

from dbmd.ora.exporter.sql import ExporterSQL


class ViewsSQL(ExporterSQL):

    select_views = '''
    with function long_to_clob(p_schema varchar2, p_view varchar2) return clob is
        l_val clob;
        l_long_val long;
      begin
        select t.TEXT
          into l_long_val
          from all_views t
         where t.VIEW_NAME = p_view
           and t.owner = p_schema;
    
        l_val := to_clob(l_long_val);
    
        return l_val;
    
        exception
          when no_data_found then
            return null;
      end;
    
    select uv.VIEW_NAME,
           uvc.COMMENTS,
           case
             when uv.TEXT_LENGTH <= 4000 then
               to_clob(uv.TEXT_VC)
             else
               long_to_clob(uv.owner, uv.VIEW_NAME)
           end as view_sql,
           col."columns",
           dep.dependencies
      from all_views uv
      left join all_tab_comments uvc
        on uv.VIEW_NAME = uvc.TABLE_NAME
       and uvc.TABLE_TYPE = 'VIEW'
       and uv.owner = uvc.owner
      left join (select json_arrayagg(json_object('name' value c.COLUMN_NAME,
                                                  'type' value json_object('name' value c.DATA_TYPE,
                                                                           'length' value c.DATA_LENGTH,
                                                                           'precision' value c.DATA_PRECISION,
                                                                           'scale' value c.DATA_SCALE),
                                                  'description' value cc.COMMENTS) returning clob) as "columns", v.view_name
                   from all_tab_columns c
                   join all_col_comments cc
                     on c.TABLE_NAME = cc.TABLE_NAME
                    and c.COLUMN_NAME = cc.COLUMN_NAME
                    and c.owner = cc.owner
                   join all_views v
                     on c.OWNER = v.owner 
                    and c.TABLE_NAME = v.VIEW_NAME
    
                  where v.owner = :schema
                  group by v.view_name
                  ) col
        on col.view_name = uv.view_name 
      left join (select json_arrayagg(json_object('type' value lower(ud.REFERENCED_TYPE),
                                                  'db_schema' value ud.REFERENCED_OWNER,
                                                  'name' value ud.REFERENCED_NAME) returning clob) as dependencies, v.view_name
                  from all_dependencies ud
                  join all_views v
                    on ud.owner = v.owner 
                   and ud.name = v.view_name 
                 where v.owner = :schema
                 group by v.view_name) dep
       on dep.view_name = uv.view_name
    where uv.owner = :schema
    '''

def get_views(conn: Connection, schema: str):

    with conn.cursor() as cur:
        ViewsSQL.select_views.execute(cur, {'schema': schema})

        return cur.fetchall()

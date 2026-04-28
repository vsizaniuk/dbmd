from oracledb import Connection

from dbmd.ora.exporter.sql import ExporterSQL


class ViewsSQL(ExporterSQL):

    select_views = '''
    with function long_to_clob(p_view varchar2) return clob is
        l_val clob;
        l_long_val long;
      begin
        select t.TEXT
          into l_long_val
          from user_views t
         where t.VIEW_NAME = p_view;
    
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
               long_to_clob(uv.VIEW_NAME)
           end as view_sql,
           col."columns",
           dep.dependencies
      from user_views uv
      left join user_tab_comments uvc
        on uv.VIEW_NAME = uvc.TABLE_NAME
       and uvc.TABLE_TYPE = 'VIEW'
      left join lateral (select json_arrayagg(json_object('name' value c.COLUMN_NAME,
                                                          'type' value json_object('name' value c.DATA_TYPE,
                                                                                   'length' value c.DATA_LENGTH,
                                                                                   'precision' value c.DATA_PRECISION,
                                                                                   'scale' value c.DATA_SCALE),
                                                          'description' value cc.COMMENTS) returning clob) as "columns"
                           from user_tab_columns c
                           join user_col_comments cc
                             on c.TABLE_NAME = cc.TABLE_NAME
                            and c.COLUMN_NAME = cc.COLUMN_NAME
    
                          where uv.VIEW_NAME = c.TABLE_NAME) col
        on 1=1
      left join lateral (select json_arrayagg(json_object('type' value lower(ud.REFERENCED_TYPE),
                                                          'db_schema' value ud.REFERENCED_OWNER,
                                                          'name' value ud.REFERENCED_NAME) returning clob) as dependencies
                          from user_dependencies ud
                         where uv.VIEW_NAME = ud.name) dep
       on 1=1
    '''

def get_views(conn: Connection):

    with conn.cursor() as cur:
        ViewsSQL.select_views.execute(cur)

        return cur.fetchall()

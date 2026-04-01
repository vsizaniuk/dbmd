'''
with triggers_list as
 (select tr.OWNER, tr.TRIGGER_NAME, tr.TABLE_OWNER, tr.TABLE_NAME
    from all_triggers tr
   where 'REVREC_DEV' = any(tr.OWNER, tr.TABLE_OWNER)),

dependencies as
 (select ud.OWNER,
         ud.name,
         json_arrayagg(json_object('type' value lower(ud.REFERENCED_TYPE),
                                   'schema' value ud.REFERENCED_OWNER,
                                   'name' value ud.REFERENCED_NAME)
                       order by ud.REFERENCED_OWNER, ud.referenced_name
                       returning clob ) as dependencies
    from all_dependencies ud
    join triggers_list tr
      on ud.OWNER = tr.OWNER
     and ud.name = tr.TRIGGER_NAME

   where ud.TYPE = 'TRIGGER'
   group by ud.OWNER, ud.name),

trigger_columns as
 (select t.TRIGGER_OWNER,
         t.TRIGGER_NAME,
         json_arrayagg(t.COLUMN_NAME order by t.COLUMN_NAME) as "columns"
    from all_trigger_cols t
    join triggers_list tr
      on t.TRIGGER_OWNER = tr.OWNER
     and t.TRIGGER_NAME = tr.TRIGGER_NAME
   where t.COLUMN_LIST = 'YES'
   group by t.TRIGGER_OWNER, t.TRIGGER_NAME)

select tr.TRIGGER_NAME,
       tr.TABLE_NAME,
       dep.dependencies,
       cols."columns"

  from triggers_list tr
  left join dependencies dep
    on tr.TRIGGER_NAME = dep.name
   and tr.OWNER = dep.owner
  left join trigger_columns cols
    on tr.TRIGGER_NAME = cols.TRIGGER_NAME
   and tr.OWNER = cols.TRIGGER_OWNER;
'''
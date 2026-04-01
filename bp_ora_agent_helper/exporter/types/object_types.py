'''
-- collection
with dependencies as
 (select ud.name,
         json_arrayagg(json_object('type' value lower(ud.REFERENCED_TYPE),
                                   'schema' value ud.REFERENCED_OWNER,
                                   'name' value ud.REFERENCED_NAME)
                       returning clob) as dependencies
    from user_dependencies ud
    join user_types ut
      on ut.TYPE_NAME = ud.name
   where ut.typecode = 'COLLECTION'
     and ud.REFERENCED_OWNER != 'SYS'
   group by ud.name)
select t.TYPE_NAME, d.dependencies, t.definition
  from (select t.TYPE_NAME,
               json_arrayagg(s.TEXT order by s.LINE returning clob) as definition
          from user_types t
          left join user_source s
            on t.TYPE_NAME = s.NAME
           and s.TYPE = 'TYPE'

         where t.typecode = 'COLLECTION'
         group by t.TYPE_NAME) t
  left join dependencies d
    on t.TYPE_NAME = d.name;

-- scalar
select t.TYPE_NAME,
       json_arrayagg(s.TEXT order by s.LINE returning clob) as definition
  from user_types t
  left join user_source s
    on t.TYPE_NAME = s.NAME
   and s.TYPE = 'TYPE'
 where t.typecode != 'COLLECTION'
   and not exists
 (select 1 from user_type_attrs a where a.type_name = t.type_name)
 group by t.TYPE_NAME;

-- object types
with dependencies as
 (select ud.name,
         json_arrayagg(json_object('type' value lower(ud.REFERENCED_TYPE),
                                   'schema' value ud.REFERENCED_OWNER,
                                   'name' value ud.REFERENCED_NAME)
                       returning clob) as dependencies
    from user_dependencies ud
    join user_types ut
      on ut.TYPE_NAME = ud.name
   where ut.typecode = 'OBJECT'
     and ud.REFERENCED_OWNER != 'SYS'
   group by ud.name),
attribs as
 (select t.TYPE_NAME,
         json_arrayagg(json_object('name' value t.ATTR_NAME,
                                   'inherited' value t.INHERITED,
                                   'type' value
                                   json_object('name' value t.ATTR_TYPE_NAME,
                                               'length' value t.length,
                                               'precision' value t.PRECISION,
                                               'scale' value t.scale)) order by
                       t.ATTR_NO returning clob) as "attributes"

    from user_type_attrs t
   group by t.TYPE_NAME),
methods as
 (select t.TYPE_NAME,
         json_arrayagg(json_object('name' value t.METHOD_NAME,
                                   'type' value t.METHOD_TYPE,
                                   'parameters_cnt' value t.PARAMETERS,
                                   'is_function' value t.results,
                                   'is_final' value t.final,
                                   'is_instantiable' value t.INSTANTIABLE,
                                   'is_overriding' value t.OVERRIDING,
                                   'is_inherited' value t.OVERRIDING) order by
                       t.METHOD_NO returning clob) as methods

    from user_type_methods t
   group by t.TYPE_NAME)

select json_object('super_owner' value t.SUPERTYPE_OWNER,
                   'super_name' value t.SUPERTYPE_NAME,
                   'name' value t.TYPE_NAME,
                   'attributes_cnt' value t.attributes,
                   'methods_cnt' value t.methods) as "object_type",
       d.dependencies,
       a."attributes",
       m.methods

  from user_types t
  left join attribs a
    on t.TYPE_NAME = a.TYPE_NAME
  left join dependencies d
    on t.TYPE_NAME = d.name
  left join methods m
    on t.TYPE_NAME = m.TYPE_NAME

 where t.typecode = 'OBJECT'
   and exists
 (select 1 from user_type_attrs a where a.type_name = t.type_name);
'''
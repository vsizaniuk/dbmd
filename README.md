# dbmd

A CLI tool that exports database schema objects into structured Markdown files — designed to give LLMs accurate, navigable context about your database without dumping raw DDL into the prompt.

Each object is exported as a self-contained `.md` file with structured tags (`[TYPE:...]`, `[SCHEMA:...]`, `[NAME:...]`, etc.) that make it easy to parse, reference, and load selectively. SQL definitions are written to separate `.sql` files and referenced by path, so they can be loaded on demand.

## Supported databases

| Database | Status |
|----------|--------|
| Oracle   | ✅ Supported |
| PostgreSQL | ✅ Supported |
| MSSQL    | 🔜 Planned |

## Exported object types

### Oracle

| Type | Description |
|------|-------------|
| Tables | Columns, constraints, indexes, triggers, row counts, partition info |
| Views | Columns, dependencies, SQL definition |
| Packages | Public routines, spec/body dependencies, SQL definition |
| Routines | Standalone functions and procedures with signatures |
| Triggers | Event, timing, table reference, SQL definition |
| Types | Object types, collection types, scalar types |

### PostgreSQL

| Type | Description |
|------|-------------|
| Tables | Columns, constraints, indexes, triggers, row counts, partition info |
| Views | Columns, dependencies, SQL definition |
| Routines | Functions and procedures with signatures, parameters, dependencies |
| Triggers | Event, timing, table reference, function reference, SQL definition |
| Types | Composite types, enum types, domain types |

## Output structure

```
mddb/
└── <schema>/
    ├── tables/
    │   └── my_table.md
    ├── views/
    │   └── my_view.md
    ├── packages/          # Oracle only
    │   ├── my_package.md
    │   └── definitions/
    │       └── my_package.sql
    ├── routines/
    │   ├── my_function.md
    │   └── definitions/
    │       └── my_function.sql
    ├── triggers/
    │   └── my_trigger.md
    └── types/
        └── my_type.md
```

## Installation

Requires Python 3.11+.

```bash
pip install .
```

## Configuration

Create a `.env` file in the working directory. All variables are required unless marked optional.

### Oracle

Two connection modes are supported.

**Thick mode** (requires Oracle Instant Client — use for production/TNS-based connections):

```env
# Path to the Oracle Instant Client libraries directory.
# Download from: https://www.oracle.com/database/technologies/instant-client.html
ORA_INSTA_CLIENT_PATH=C:\oracle\instantclient_19_28

# Oracle credentials
# Supports proxy authentication: ORA_USER=actual_user[proxy_schema]
ORA_USER=my_user
ORA_PASSWORD=my_password

# Path to the directory containing tnsnames.ora
ORA_TNS_PATH=C:\oracle\tns_admin
# TNS alias as defined in tnsnames.ora
ORA_DSN=MY_DB_ALIAS

# Schema to export
ORA_SCHEMA=MY_SCHEMA

# Connection pool
ORA_MIN_CONN_CNT=4
ORA_MAX_CONN_CNT=10
```

**Thin mode** (no Instant Client required — use for local/Docker connections):

```env
# Omit ORA_INSTA_CLIENT_PATH and ORA_TNS_PATH entirely.
# ORA_DSN must be a direct connect string: host:port/service_name
ORA_USER=my_user
ORA_PASSWORD=my_password
ORA_DSN=localhost:1521/FREEPDB1

ORA_SCHEMA=MY_SCHEMA
ORA_MIN_CONN_CNT=4
ORA_MAX_CONN_CNT=10
```

### PostgreSQL

```env
PG_HOST=localhost
PG_PORT=5432
PG_USER=my_user
PG_PASSWORD=my_password
PG_DBNAME=my_database

# Schema to export
PG_SCHEMA=my_schema

# Connection pool
PG_MIN_CONN_CNT=4
PG_MAX_CONN_CNT=10
```

### Logging (optional, both databases)

```env
MDDB_LOG_LEVEL=INFO   # DEBUG, INFO, WARNING, ERROR (default: INFO)
MDDB_WRITE_LOG_FILE=0 # Set to 1 to write logs to a timestamped file
```

## Usage

```bash
# Export all object types
dbmd export all

# Export a specific object type
dbmd export tables
dbmd export views
dbmd export routines
dbmd export triggers
dbmd export types
dbmd export packages   # Oracle only

# Export a single named object
dbmd export tables --name MY_TABLE
dbmd export views --name MY_VIEW
dbmd export routines --name MY_FUNC
dbmd export packages --name MY_PKG
dbmd export triggers --name MY_TRIGGER
dbmd export types --name MY_TYPE

# Select database type (default: oracle)
dbmd --db postgres export all
dbmd --db oracle export all

# Override schema at runtime
dbmd --db postgres --schema other_schema export all
```

## Example output

**Partitioned table (Oracle):**
```markdown
# Table: SALES
[TYPE:TABLE]
[SCHEMA:MY_SCHEMA]

## Partitioning
- Strategy: RANGE
- Key: (SALE_DATE)
- Partitions: 4
- Subpartition strategy: HASH
- Subpartition key: (CUSTOMER_ID)
- Subpartitions per partition: 2

## Columns
- ID: NUMBER not null
- CUSTOMER_ID: NUMBER not null
- AMOUNT: NUMBER(12, 2) not null
- SALE_DATE: DATE not null
```

**Table (PostgreSQL):**
```markdown
# Table: orders
[TYPE:TABLE]
[SCHEMA:my_schema]

Customer orders

## Statistics
- Rows count: 0

## Columns
- id: integer default nextval('my_schema.orders_id_seq'::regclass) not null
- customer_id: integer not null
- status: my_schema.order_status default 'pending'::my_schema.order_status not null
- total_amount: numeric(12,2)
- created_at: timestamp without time zone default now()

## Primary key
- orders_pk: (id)

## Foreign keys
- orders_customer_fk: (customer_id) -> customers (id) [RESTRICT]

## Indexes
- orders_pending_idx: (created_at) btree
  `CREATE INDEX orders_pending_idx ON my_schema.orders USING btree (created_at) WHERE (status = 'pending'::my_schema.order_status)`
```

**Package (Oracle):**
```markdown
# Package: BILLING_ADMIN
[TYPE:PACKAGE]
[SCHEMA:MY_SCHEMA]

[PACKAGE:BILLING_ADMIN]
## General
- Has body: YES

## Public routines
### Function: GET_INVOICE_TOTAL
[ROUTINE:GET_INVOICE_TOTAL]

- Parameters:
  - P_INVOICE_ID IN NUMBER
- Returns: NUMBER

## Definition
[DEFINITION]
./mddb/MY_SCHEMA/packages/definitions/BILLING_ADMIN.sql
```

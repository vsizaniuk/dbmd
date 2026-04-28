# dbmd

A CLI tool that exports database schema objects into structured Markdown files — designed to give LLMs accurate, navigable context about your database without dumping raw DDL into the prompt.

Each object is exported as a self-contained `.md` file with structured tags (`[TYPE:...]`, `[SCHEMA:...]`, `[NAME:...]`, etc.) that make it easy to parse, reference, and load selectively. SQL definitions are written to separate `.sql` files and referenced by path, so they can be loaded on demand.

## Supported databases

| Database | Status |
|----------|--------|
| Oracle   | ✅ Supported |
| PostgreSQL | 🔜 Planned |
| MSSQL    | 🔜 Planned |

## Exported object types

| Type | Description |
|------|-------------|
| Tables | Columns, constraints, indexes, triggers, row counts |
| Views | Columns, dependencies, SQL definition |
| Packages | Public routines, spec/body dependencies, SQL definition |
| Routines | Standalone functions and procedures with signatures |
| Triggers | Event, timing, table reference, SQL definition |
| Types | Object types, collection types, scalar types |

## Output structure

```
mddb/
└── <SCHEMA>/
    ├── tables/
    │   ├── MY_TABLE.md
    │   └── ...
    ├── views/
    ├── packages/
    │   ├── MY_PACKAGE.md
    │   └── definitions/
    │       └── MY_PACKAGE.sql
    ├── routines/
    │   ├── MY_FUNCTION.md
    │   └── definitions/
    ├── triggers/
    ├── types/
    └── views/
```

## Installation

Requires Python 3.11+.

```bash
pip install .
```

## Configuration

Create a `.env` file in the working directory. All variables are required unless marked optional.

```env
# Oracle Instant Client
# Path to the Oracle Instant Client libraries directory.
# Download from: https://www.oracle.com/database/technologies/instant-client.html
ORA_INSTA_CLIENT_PATH=C:\oracle\instantclient_19_28

# Oracle credentials
# Supports proxy authentication: ORA_USER=actual_user[proxy_schema]
ORA_USER=my_user
ORA_PASSWORD=my_password

# TNS configuration
# Path to the directory containing tnsnames.ora (TNS admin directory)
ORA_TNS_PATH=C:\oracle\tns_admin
# TNS alias as defined in tnsnames.ora
ORA_DSN=MY_DB_ALIAS

# Schema to export
ORA_SCHEMA=MY_SCHEMA

# Connection pool
ORA_MIN_CONN_CNT=4   # Minimum number of connections kept open
ORA_MAX_CONN_CNT=10  # Maximum number of connections in the pool

# Logging (optional)
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
dbmd export packages
dbmd export routines
dbmd export triggers
dbmd export types

# Override schema at runtime
dbmd --schema OTHER_SCHEMA export all

# Specify database type (for future multi-db support)
dbmd --db oracle export all
```

## Example output

**Table:**
```markdown
# Table: INVOICE
[TYPE:TABLE]
[SCHEMA:MY_SCHEMA]

## Statistics
- Rows count: 1482301

## Columns
- INVOICE_ID: NUMBER not null
- ACCOUNT_ID: NUMBER not null
- AMOUNT: NUMBER(32, 6) not null
- STATUS: VARCHAR2(64) not null
- CREATED: TIMESTAMP(6) WITH TIME ZONE not null

## Primary key
- INVOICE$INVOICE_ID$PK: (INVOICE_ID)

## Foreign keys
- INVOICE$ACCOUNT_ID$FK: (ACCOUNT_ID) -> ACCOUNT (ACCOUNT_ID) [None]
```

**Package:**
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

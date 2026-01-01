# API Documentation Template

## Endpoint: POST /sync-definitions

### Description
Create a new sync definition that maps a Postgres table to a SharePoint list.

### Authentication
Requires syncbridge.write scope.

### Request Parameters
| Name | Type | Required | Description |
| --- | --- | --- | --- |
| name | string | yes | Human-friendly name |
| source_schema | string | yes | Postgres schema |
| source_table | string | yes | Postgres table |
| sync_mode | string | yes | ONE_WAY_PUSH or TWO_WAY |

### Response
- 201: Created with the sync definition payload
- 400: Validation error

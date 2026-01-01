# Configuration Guide

## Connection profiles
- Postgres: host, database, user, SSL settings
- SharePoint: tenant, site path, and Graph app credentials

## Sync definitions
- Source table and primary key
- Sync mode (push, pull, or two-way)
- Conflict policy
- Schedule or manual runs

## Sharding rules
- Define rule order and default targets
- Example: status == Active -> Projects_Active

## Field mappings
- Map source columns to SharePoint columns
- Apply transformation rules (date formats, type casting)

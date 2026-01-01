# CLI Reference

The CLI is a thin wrapper around control plane APIs for administrative tasks.

## syncbridge

**Usage:**
`syncbridge <command> [flags]`

### Commands
- `connections list`
- `connections verify --id <connection_id>`
- `sync-definitions list`
- `provision --sync-def-id <id>`
- `run --sync-def-id <id> --mode push|pull`
- `status --run-id <id>`

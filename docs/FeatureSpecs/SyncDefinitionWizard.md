# Feature Spec: Sync Definition Wizard

## Goal
- Reduce time-to-first-sync by turning the current manual, multi-screen setup into one guided workflow.

## Scope
- Source selection
- Target selection or provisioning
- Mapping suggestions
- Schedule/CDC setup
- Review and dry-run

## Acceptance Criteria
- User can create a draft wizard session
- User can select a source table and target list
- System suggests field mappings
- Required validation errors are shown inline
- User can review a summary before activation
- User can save draft and resume later
- User can run a dry-run validation before final save

## API Changes
- Wizard draft CRUD
- Mapping suggestion endpoint
- Dry-run validation endpoint

## Data Changes
- `sync_definition_drafts`
- optional `mapping_suggestions_audit`

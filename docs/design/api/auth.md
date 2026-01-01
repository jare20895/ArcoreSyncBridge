# Authentication and Authorization

## Overview
The control plane API uses Azure AD JWT validation. The UI uses OIDC with PKCE, while workers use app-only tokens for Microsoft Graph access.

## Roles and scopes
- syncbridge.read: Read-only access to definitions and run history
- syncbridge.write: Create and update sync definitions
- syncbridge.admin: Manage connections, secrets, and policies

## Token requirements
- Audience must match the API app registration
- Tokens must include required scopes
- Tokens must be renewed before expiry

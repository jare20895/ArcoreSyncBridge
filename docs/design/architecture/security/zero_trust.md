# Zero Trust Architecture

Arcore SyncBridge follows zero trust principles: verify explicitly, use least privilege, and assume breach.

## Core practices
- All users authenticate via Azure AD (OIDC).
- API validates JWT tokens and scopes on every request.
- Workers use app-only tokens with restricted Graph scopes.
- Secrets are encrypted at rest and rotated on schedule.

```mermaid
graph LR
    User((Operator)) -->|OIDC| AAD[Azure AD]
    User --> UI[Web UI]
    UI -->|JWT| API[Control Plane API]
    API --> Meta[(Meta-Store)]
    API --> Queue[(Redis Queue)]
    Queue --> Worker[Sync Worker]
    Worker -->|App-only token| Graph[Microsoft Graph]
    Graph --> SP[SharePoint Lists]
```

# Release and Rollback Guide

## Release Process

1.  **Prepare:** Ensure all changes are merged to `main` and CI passed.
2.  **Run Release Script:**
    ```bash
    ./scripts/release.sh patch  # or minor/major
    ```
    This will:
    - Bump version in `VERSION` and `package.json`.
    - Create a git tag `vX.Y.Z`.
    - Build local Docker images tagged with the version.
3.  **Push:**
    ```bash
    git push origin main --tags
    # Push docker images to registry (if configured)
    docker push myregistry/arcoresyncbridge-backend:vX.Y.Z
    ```

## Rollback Plan

If a deployment fails or critical bugs are found:

### Database Rollback
If schema migrations were applied and need reversing:
1.  Identify the target revision (e.g., previous tag).
2.  Run Alembic downgrade:
    ```bash
    docker exec arcoresyncbridge-backend-1 alembic downgrade <revision_id>
    # Or downgrade by one step
    docker exec arcoresyncbridge-backend-1 alembic downgrade -1
    ```
3.  **Critical:** If data loss occurred, perform [Disaster Recovery Restore](./disaster_recovery.md).

### Application Rollback
To revert the running application to the previous version:

1.  **Identify Previous Version:** Check `git tag` or your container registry.
2.  **Update Deployment:**
    - If using Docker Compose:
      Update `.env` or `docker-compose.yml` to point to the previous image tag (e.g., `v1.0.0` instead of `v1.0.1`).
      ```bash
      docker-compose up -d
      ```
    - If using Kubernetes/Helm:
      ```bash
      helm rollback arcore-syncbridge <revision>
      ```

### Verification
1.  Check logs for startup errors: `docker-compose logs -f backend`.
2.  Verify Health Endpoint: `curl http://localhost:8055/health`.
3.  Check Admin UI for functionality.

# Port Availability (2026-01-09)

Note: Docker daemon is not accessible in this environment (`permission denied` on `docker ps`). Port usage is based on `ss -tuln` output; some high-numbered ports (3000/8000 series, Redis/Postgres/Minio ranges) are heavily occupied by other stacks.

## Phase 0 (ArcoreDataControl) Assigned Host Ports
- Backend API: **8400 -> 8000/tcp** (docker-compose.dev)
- Postgres: **5540 -> 5432/tcp**
- Redis: **7379 -> 6379/tcp**
- Minio: **9100 -> 9000/tcp**, **9101 -> 9001/tcp**
- (Frontend planned) Reserve **3400 -> 3000/tcp** for future UI

## ArcoreSyncBridge Assigned Host Ports
- Backend API: **8401 -> 8401/tcp** (docker-compose.yml)
- Postgres: **5465 -> 5432/tcp**
- Redis: **6384 -> 6379/tcp**
- Frontend UI: **3005 -> 3000/tcp**

## ArcoreLLMProxy Assigned Ports
- Backend API: **8402 -> 8000/tcp** (remapped from 8000)
- Postgres: **5560 -> 5432/tcp**
- Frontend UI: **3401 -> 3000/tcp** (reserved for future admin console)

## Reserved Ports for Upcoming Projects
| Project   | Frontend (host->container) | Backend (host->container) | Database (host->container) |
| :---      | :---                       | :---                      | :---                       |
| Project1  | 3410 -> 3000               | 8410 -> 8000              | 5551 -> 5432               |
| Project2  | 3411 -> 3000               | 8411 -> 8000              | 5552 -> 5432               |
| Project3  | 3412 -> 3000               | 8412 -> 8000              | 5553 -> 5432               |
| Project4  | 3413 -> 3000               | 8413 -> 8000              | 5554 -> 5432               |
| Project5  | 3414 -> 3000               | 8414 -> 8000              | 5555 -> 5432               |
| Project6  | 3415 -> 3000               | 8415 -> 8000              | 5556 -> 5432               |

## Observed Busy Ranges
- Postgres: 5432, 5433, 5452–5470
- Redis: 6379, 6380–6392
- Web/UI: 3000–3200, 5173
- APIs: 8000–8055, 8200, 8501–8502
- Misc: 9000–9003 (Minio), 14250/14268/16686 (Jaeger), 4317/4318 (OTel), 2024 (Langgraph)

## Recommendations
- Avoid assigning new services on the above busy ranges; prefer unused high ports (e.g., 3400–3499 for frontend, 8400–8499 for APIs, 5540–5550 for local Postgres).
- Keep the Phase 0 stack on the reserved ports above to prevent collisions with existing containers.

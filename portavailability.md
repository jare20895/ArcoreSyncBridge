# Port Availability (2025-12-31 09:06:37)
## Assigned Port (arcore-website)
- 3090->3000/tcp (selected from available host ports not listed below)

## Reserved Ports (SSO stack)
| Service | Ports | Notes |
| --- | --- | --- |
| identity/zitadel | 18083->8080/tcp | Zitadel console |
| identity/zitadel | 15437->5432/tcp | Zitadel Postgres |
| sso-onboarding | 3080->3000/tcp | SSO onboarding UI |
| sso-onboarding | 15439->5432/tcp | Onboarding Postgres |
## Docker Containers (all)
| Container | Status | Ports |
| --- | --- | --- |
| arcore-nexus-backend | Up 27 minutes (unhealthy) | - |
| ai-orch-frontend | Up 32 minutes | 0.0.0.0:3200->3000/tcp, [::]:3200->3000/tcp |
| ai-orch-streamlit | Up 32 minutes | 0.0.0.0:8501->8501/tcp, [::]:8501->8501/tcp |
| ai-orch-api | Up 32 minutes | 0.0.0.0:8200->8000/tcp, [::]:8200->8000/tcp |
| ai-orch-worker-http | Up 32 minutes | 0.0.0.0:5200->5000/tcp, [::]:5200->5000/tcp |
| ai-orch-langgraph-server | Up 32 minutes | 0.0.0.0:2024->2024/tcp, [::]:2024->2024/tcp |
| litellm-mock | Up 32 minutes | - |
| ai-orch-langflow | Up 32 minutes | 0.0.0.0:8502->7860/tcp, [::]:8502->7860/tcp |
| ai-orch-jaeger | Up 32 minutes | 0.0.0.0:4317-4318->4317-4318/tcp, [::]:4317-4318->4317-4318/tcp, 0.0.0.0:14250->14250/tcp, [::]:14250->14250/tcp, 0.0.0.0:14268->14268/tcp, [::]:14268->14268/tcp, 0.0.0.0:16686->16686/tcp, [::]:16686->16686/tcp, 0.0.0.0:6831-6832->6831-6832/udp, [::]:6831-6832->6831-6832/udp |
| arcore_scope_frontend | Up 33 minutes | 0.0.0.0:5173->5173/tcp, [::]:5173->5173/tcp |
| arcore_scope_api | Up 33 minutes | 0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp |
| arcore_scope_db | Up 33 minutes (healthy) | 0.0.0.0:5457->5432/tcp, [::]:5457->5432/tcp |
| arcorenarrator-postgres | Up 37 minutes (healthy) | 0.0.0.0:5464->5432/tcp, [::]:5464->5432/tcp |
| arcorenarrator-redis | Up 37 minutes (healthy) | 0.0.0.0:6391->6379/tcp, [::]:6391->6379/tcp |
| arcorenarrator-minio | Up 37 minutes (healthy) | 0.0.0.0:9002->9000/tcp, [::]:9002->9000/tcp, 0.0.0.0:9003->9001/tcp, [::]:9003->9001/tcp |
| arcore_insignia_db | Up 48 minutes (healthy) | 0.0.0.0:5433->5432/tcp, [::]:5433->5432/tcp |
| arcore-studio | Up 52 minutes | 0.0.0.0:9229->9229/tcp, [::]:9229->9229/tcp, 0.0.0.0:3011->3000/tcp, [::]:3011->3000/tcp |
| arcore-service | Restarting (1) 42 seconds ago | - |
| arcore-postgres | Up 52 minutes (healthy) | 0.0.0.0:5470->5432/tcp, [::]:5470->5432/tcp |
| arcore-redis | Up 52 minutes (healthy) | 0.0.0.0:6390->6379/tcp, [::]:6390->6379/tcp |
| arcoreerp_db | Up 54 minutes (healthy) | 0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp |
| arcoreerp_redis | Up 54 minutes (healthy) | 0.0.0.0:6379->6379/tcp, [::]:6379->6379/tcp |
| arcoreblueprint_studio_dev | Up About an hour | 0.0.0.0:3010->3000/tcp, [::]:3010->3000/tcp |
| arcoreblueprint_pgadmin_dev | Up About an hour | 0.0.0.0:5051->80/tcp, [::]:5051->80/tcp |
| arcoreblueprint_db_dev | Up About an hour (healthy) | 0.0.0.0:5463->5432/tcp, [::]:5463->5432/tcp |
| arcoreblueprint_redis_dev | Up About an hour (healthy) | 0.0.0.0:6383->6379/tcp, [::]:6383->6379/tcp |
| arecore_frontend | Up About an hour | 0.0.0.0:3001->3001/tcp, [::]:3001->3001/tcp |
| arecore_portal | Up About an hour | 0.0.0.0:3002->3001/tcp, [::]:3002->3001/tcp |
| arecore_backend | Up About an hour | 0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp |
| arecore_db | Up About an hour (healthy) | 0.0.0.0:5458->5432/tcp, [::]:5458->5432/tcp |

## Docker Compose Ports (project)
| Compose File | Service | Ports |
| --- | --- | --- |
| AcademicOperationsCenter/docker-compose.yml | aoc-dashboard | 13005->3000/tcp |
| AcademicOperationsCenter/docker-compose.yml | aoc-dev | 13005->3000/tcp |
| AcademicOperationsCenter/docker-compose.yml | minio | 19000->9000/tcp, 19001->9001/tcp |
| AcademicOperationsCenter/docker-compose.yml | postgres | 15432->5432/tcp |
| AcademicOperationsCenter/docker-compose.yml | redis | 16379->6379/tcp |
| ArcorParkour/docker-compose.yml | backend | ${BACKEND_PORT:-8100}->8000/tcp |
| ArcorParkour/docker-compose.yml | db | ${DATABASE_PORT:-5436}->5432/tcp |
| ArcorParkour/docker-compose.yml | frontend | ${FRONTEND_PORT:-3100}->3000/tcp |
| ArcorParkour/docker-compose.yml | redis | ${REDIS_PORT:-6381}->6379/tcp |
| ArcoreArsenal/docker-compose.dev.yml | adminer | 8080->8080/tcp |
| ArcoreArsenal/docker-compose.dev.yml | redis-commander | 8081->8081/tcp |
| ArcoreArsenal/docker-compose.yml | backend | 8000->8000/tcp |
| ArcoreArsenal/docker-compose.yml | flower | 5555->5555/tcp |
| ArcoreArsenal/docker-compose.yml | frontend | 80->80/tcp |
| ArcoreArsenal/docker-compose.yml | postgres | 5432->5432/tcp |
| ArcoreArsenal/docker-compose.yml | redis | 6379->6379/tcp |
| ArcoreBlueprint/docker-compose.dev.yml | pgadmin | ${PGADMIN_PORT:-5051}->80/tcp |
| ArcoreBlueprint/docker-compose.dev.yml | postgres | ${POSTGRES_PORT:-5463}->5432/tcp |
| ArcoreBlueprint/docker-compose.dev.yml | redis | ${REDIS_PORT:-6383}->6379/tcp |
| ArcoreBlueprint/docker-compose.dev.yml | studio-dev | ${STUDIO_PORT:-3010}->3000/tcp |
| ArcoreBlueprint/docker-compose.yml | pgadmin | ${PGADMIN_PORT:-5051}->80/tcp |
| ArcoreBlueprint/docker-compose.yml | postgres | ${POSTGRES_PORT:-5463}->5432/tcp |
| ArcoreBlueprint/docker-compose.yml | redis | ${REDIS_PORT:-6383}->6379/tcp |
| ArcoreBlueprint/docker-compose.yml | studio | ${STUDIO_PORT:-3010}->3000/tcp |
| ArcoreCodex/docker-compose.prod.yml | frontend | 80->80/tcp |
| ArcoreCodex/docker-compose.yml | backend | 8002->8002/tcp |
| ArcoreCodex/docker-compose.yml | db | 5432->5432/tcp |
| ArcoreCodex/docker-compose.yml | frontend | 3002->3000/tcp |
| ArcoreERP/docker-compose.yml | db | 5432->5432/tcp |
| ArcoreERP/docker-compose.yml | redis | 6379->6379/tcp |
| ArcoreEstate/docker-compose.yml | backend | 8000->8000/tcp |
| ArcoreEstate/docker-compose.yml | frontend | 5173->5173/tcp |
| ArcoreEstate/docker-compose.yml | postgres | 5432->5432/tcp |
| ArcoreFiscal/docker-compose.prod.yml | frontend | ${FRONTEND_PORT:-5173}->80/tcp |
| ArcoreFiscal/docker-compose.yml | backend | ${BACKEND_PORT:-8006}->8000/tcp |
| ArcoreFiscal/docker-compose.yml | db | ${POSTGRES_PORT:-5452}->5432/tcp |
| ArcoreFiscal/docker-compose.yml | frontend | ${FRONTEND_PORT:-5173}->5173/tcp |
| ArcoreFiscal/docker-compose.yml | nginx | ${NGINX_PORT:-80}->80/tcp, ${NGINX_SSL_PORT:-443}->443/tcp |
| ArcoreFiscal/docker-compose.yml | redis | ${REDIS_PORT:-6386}->6379/tcp |
| ArcoreFoundry/docker-compose.prod.yml | nginx | 80->80/tcp, 443->443/tcp |
| ArcoreFoundry/docker-compose.yml | postgres | 5470->5432/tcp |
| ArcoreFoundry/docker-compose.yml | redis | 6390->6379/tcp |
| ArcoreFoundry/docker-compose.yml | service | 3012->3001/tcp, 9230->9230/tcp |
| ArcoreFoundry/docker-compose.yml | studio | 3011->3000/tcp, 9229->9229/tcp |
| ArcoreGenesis/docker-compose.yml | genesis-api | 8000->8000/tcp |
| ArcoreGenesis/docker-compose.yml | genesis-web | 3000->3000/tcp |
| ArcoreGenesis/docker-compose.yml | postgres | 5432->5432/tcp |
| ArcoreInsignia/docker-compose.yml | api | 3001->3001/tcp |
| ArcoreInsignia/docker-compose.yml | db | 5433->5432/tcp |
| ArcoreInsignia/docker-compose.yml | pgadmin | 5051->80/tcp |
| ArcoreInsignia/docker-compose.yml | web | 3003->3000/tcp |
| ArcoreLedger/docker-compose.yml | backend | 8007->8000/tcp |
| ArcoreLedger/docker-compose.yml | db | 5456->5432/tcp |
| ArcoreLedger/docker-compose.yml | frontend | 5174->5173/tcp |
| ArcoreMaestro/docker-compose.yml | api | 8200->8000/tcp |
| ArcoreMaestro/docker-compose.yml | frontend | 3200->3000/tcp |
| ArcoreMaestro/docker-compose.yml | jaeger | 16686->16686/tcp, 4318->4318/tcp, 4317->4317/tcp, 14268->14268/tcp, 14250->14250/tcp, 6831->6831/udp, 6832->6832/udp |
| ArcoreMaestro/docker-compose.yml | langflow | 8502->7860/tcp |
| ArcoreMaestro/docker-compose.yml | langgraph-server | 2024->2024/tcp |
| ArcoreMaestro/docker-compose.yml | streamlit | 8501->8501/tcp |
| ArcoreMaestro/docker-compose.yml | worker-http | 5200->5000/tcp |
| ArcoreNarrator/docker-compose.yml | minio | 9002->9000/tcp, 9003->9001/tcp |
| ArcoreNarrator/docker-compose.yml | postgres | 5464->5432/tcp |
| ArcoreNarrator/docker-compose.yml | redis | 6391->6379/tcp |
| ArcoreNexus/docker-compose.yml | frontend | 5173->80/tcp |
| ArcoreScope/docker-compose.yml | api | 8000->8000/tcp |
| ArcoreScope/docker-compose.yml | db | 5457->5432/tcp |
| ArcoreScope/docker-compose.yml | frontend | 5173->5173/tcp |
| ArcoreSentinel/docker-compose.develop.yaml | sentinel-dev | 8080->8080/tcp |
| ArcoreSentinel/docker-compose.yaml | sentinel | 8080->8080/tcp |
| ArcoreVector/docker-compose.yml | backend | 8000->8000/tcp |
| ArcoreVector/docker-compose.yml | frontend | 5173->5173/tcp |
| ArcoreVector/docker-compose.yml | postgres | 5432->5432/tcp |
| ArcoreWebsite/website/docker-compose.yaml | arcore-website | 8090->8090/tcp |
| Arecore/docker-compose.yaml | backend | 3000->3000/tcp |
| Arecore/docker-compose.yaml | frontend | 3001->3001/tcp |
| Arecore/docker-compose.yaml | portal | 3002->3001/tcp |
| Arecore/docker-compose.yaml | postgres | 5458->5432/tcp |
| ArecoreConduit/docker-compose.yaml | backend | 8001->8000/tcp |
| ArecoreConduit/docker-compose.yaml | frontend | 3003->3003/tcp |
| ArecoreConduit/docker-compose.yaml | infisical | 8081->8080/tcp |
| ArecoreConduit/docker-compose.yaml | postgres | 5433->5432/tcp |
| ArecoreConduit/docker-compose.yaml | redis | 6382->6379/tcp |
| ArecoreConduit/docker-compose.yaml | scrapper | 8082->8080/tcp |
| CareerForge/docker-compose.yml | frontend | 3009->3000/tcp |
| CareerForge/docker-compose.yml | pgadmin | 5050->80/tcp |
| CareerForge/docker-compose.yml | postgres | 5460->5432/tcp |
| Chapterize/docker-compose.yml | backend | 8050->8000/tcp |
| Chapterize/docker-compose.yml | daphne | 8051->8001/tcp |
| Chapterize/docker-compose.yml | db | 5455->5432/tcp |
| Chapterize/docker-compose.yml | frontend | 3001->5173/tcp |
| Chapterize/docker-compose.yml | redis | 6379->6379/tcp |
| CyberSecurityConsulting/docker-compose.dev.yml | backend | 8002->8000/tcp |
| CyberSecurityConsulting/docker-compose.dev.yml | db | 5435->5432/tcp |
| CyberSecurityConsulting/docker-compose.dev.yml | frontend | 3004->3000/tcp |
| CyberSecurityConsulting/docker-compose.yml | backend | 8002->8000/tcp |
| CyberSecurityConsulting/docker-compose.yml | db | 5435->5432/tcp |
| CyberSecurityConsulting/docker-compose.yml | frontend | 3004->80/tcp |
| SNOWTools/docker-compose.yml | db | 5434->5432/tcp |
| SNOWTools/docker-compose.yml | redis | 6380->6379/tcp |
| SNOWTools/docker-compose.yml | web | 8888->8000/tcp |
| ServiceCatalog/ServiceCatalog/service-catalog-management/docker/docker-compose.yaml | admin | 8010->8001/tcp |
| ServiceCatalog/ServiceCatalog/service-catalog-management/docker/docker-compose.yaml | api | 8011->8000/tcp |
| ServiceCatalog/ServiceCatalog/service-catalog-management/docker/docker-compose.yaml | db | 5442->5432/tcp |
| ServiceCatalog/ServiceCatalog/service-catalog-management/docker/docker-compose.yaml | frontend | 3000->80/tcp |
| local-llm-server/docker-compose-build.yml | llm-server | 8002->8000/tcp |
| local-llm-server/docker-compose.yml | llm-frontend | 4173->3000/tcp |
| local-llm-server/docker-compose.yml | llm-frontend-dev | 4174->3000/tcp |
| local-llm-server/docker-compose.yml | llm-server | 8001->8000/tcp |
| arcore-website/docker-compose.yml | arcore-website | 3090->3000/tcp |
| ArcoreSyncBridge/docker-compose.yml | backend | 8055->8000/tcp |
| ArcoreSyncBridge/docker-compose.yml | frontend | 3005->3000/tcp |
| ArcoreSyncBridge/docker-compose.yml | db | 5465->5432/tcp |
| ArcoreSyncBridge/docker-compose.yml | redis | 6384->6379/tcp |

## TCP Ports in Use (host)
```
State  Recv-Q Send-Q  Local Address:Port  Peer Address:PortProcess                       
LISTEN 0      1000   10.255.255.254:53         0.0.0.0:*                                 
LISTEN 0      511         127.0.0.1:37283      0.0.0.0:*    users:(("node",pid=26,fd=21))
LISTEN 0      4096                *:14268            *:*                                 
LISTEN 0      4096                *:14250            *:*                                 
LISTEN 0      4096                *:8200             *:*                                 
LISTEN 0      4096                *:8501             *:*                                 
LISTEN 0      4096                *:8502             *:*                                 
LISTEN 0      4096                *:9003             *:*                                 
LISTEN 0      4096                *:9002             *:*                                 
LISTEN 0      4096                *:9229             *:*                                 
LISTEN 0      4096                *:4317             *:*                                 
LISTEN 0      4096                *:4318             *:*                                 
LISTEN 0      4096                *:5051             *:*                                 
LISTEN 0      4096                *:5173             *:*                                 
LISTEN 0      4096                *:5200             *:*                                 
LISTEN 0      4096                *:5433             *:*                                 
LISTEN 0      4096                *:5432             *:*                                 
LISTEN 0      4096                *:5457             *:*                                 
LISTEN 0      4096                *:5458             *:*                                 
LISTEN 0      4096                *:5463             *:*                                 
LISTEN 0      4096                *:5464             *:*                                 
LISTEN 0      4096                *:5470             *:*                                 
LISTEN 0      4096                *:6391             *:*                                 
LISTEN 0      4096                *:6390             *:*                                 
LISTEN 0      4096                *:6379             *:*                                 
LISTEN 0      4096                *:6383             *:*                                 
LISTEN 0      4096                *:8000             *:*                                 
LISTEN 0      4096                *:16686            *:*                                 
LISTEN 0      4096                *:2024             *:*                                 
LISTEN 0      4096                *:3001             *:*                                 
LISTEN 0      4096                *:3000             *:*                                 
LISTEN 0      4096                *:3002             *:*                                 
LISTEN 0      4096                *:3011             *:*                                 
LISTEN 0      4096                *:3010             *:*                                 
LISTEN 0      4096                *:3200             *:*
```

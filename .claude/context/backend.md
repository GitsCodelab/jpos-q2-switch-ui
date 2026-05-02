# Backend Context

Architecture:
- Service/repository pattern
- FastAPI REST APIs
- PostgreSQL persistence

Important Directories:
- /backend/api
- /backend/services
- /backend/repositories
- /backend/models

Rules:
- Keep controllers thin
- Business logic in services
- DB access only via repositories
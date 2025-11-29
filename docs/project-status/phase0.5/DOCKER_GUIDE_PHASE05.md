# DreamSeed Phase 0.5 - Docker Quick Start Guide

## 🚀 Quick Start

```bash
# 1. Copy environment file
cp .env.docker .env

# 2. Make scripts executable
chmod +x backend/docker-entrypoint.sh scripts/init-db.sh

# 3. Start all services
docker-compose -f docker-compose.phase0.5.yml up -d

# 4. View logs
docker-compose -f docker-compose.phase0.5.yml logs -f backend

# 5. Check health
curl http://localhost:8001/health
```

## 📦 Services

### Core Services (Always Running)
- **PostgreSQL** (port 5433) - Main database
- **Redis** (port 6380) - CAT engine state cache
- **Backend** (port 8001) - FastAPI application

### Optional Services
- **pgAdmin** (port 5051) - Database admin UI
  ```bash
  docker-compose -f docker-compose.phase0.5.yml --profile admin up -d
  ```

## 🔍 Service Details

### PostgreSQL
- **Image:** postgres:15-alpine
- **Port:** 5433 → 5432 (mapped to avoid conflict)
- **Health Check:** `pg_isready`
- **Volumes:** `postgres_phase05_data`
- **Credentials:**
  - Database: `dreamseed_dev`
  - User: `postgres`
  - Password: `DreamSeedAi0908`

### Redis
- **Image:** redis:7-alpine
- **Port:** 6380 → 6379 (mapped to avoid conflict)
- **Health Check:** `redis-cli ping`
- **Volumes:** `redis_phase05_data`
- **Persistence:** AOF enabled

### Backend
- **Build:** Custom Dockerfile
- **Port:** 8001 → 8000
- **Health Check:** `GET /health`
- **Auto-seeding:** Set `AUTO_SEED_DATA=true` in `.env`
- **Hot Reload:** Enabled in development mode

## 🔧 Configuration

### Environment Variables (.env)

```bash
# PostgreSQL
POSTGRES_DB=dreamseed_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=DreamSeedAi0908
POSTGRES_PORT=5433

# Redis
REDIS_PORT=6380

# Backend
BACKEND_PORT=8001
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
DEBUG=true
AUTO_SEED_DATA=true

# pgAdmin (optional)
PGADMIN_PORT=5051
PGADMIN_EMAIL=admin@dreamseed.ai
PGADMIN_PASSWORD=admin
```

## 📊 Health Checks

```bash
# Check all service health
docker-compose -f docker-compose.phase0.5.yml ps

# Check PostgreSQL
docker exec dreamseed_postgres_phase05 pg_isready -U postgres -d dreamseed_dev

# Check Redis
docker exec dreamseed_redis_phase05 redis-cli ping

# Check Backend
curl http://localhost:8001/health
```

## 🧪 Testing

### Run E2E Tests
```bash
# Inside backend container
docker exec -it dreamseed_backend_phase05 pytest tests/test_adaptive_exam_e2e.py -v

# Or from host
export DATABASE_URL="postgresql+psycopg://postgres:DreamSeedAi0908@localhost:5433/dreamseed_test"
export REDIS_URL="redis://localhost:6380/0"
cd backend && pytest tests/test_adaptive_exam_e2e.py -v
```

### Test CAT API
```bash
# Start exam
curl -X POST http://localhost:8001/api/adaptive/start \
  -H "Content-Type: application/json" \
  -d '{"exam_type": "placement"}'

# Get next item
curl http://localhost:8001/api/adaptive/next?exam_session_id=1

# Submit answer
curl -X POST http://localhost:8001/api/adaptive/answer \
  -H "Content-Type: application/json" \
  -d '{
    "exam_session_id": 1,
    "item_id": 1,
    "correct": true,
    "selected_choice": 1,
    "response_time_ms": 15000
  }'
```

## 🗄️ Database Access

### psql (Command Line)
```bash
# Connect to main database
docker exec -it dreamseed_postgres_phase05 psql -U postgres -d dreamseed_dev

# Or from host
psql postgresql://postgres:DreamSeedAi0908@localhost:5433/dreamseed_dev
```

### pgAdmin (Web UI)
```bash
# Start pgAdmin
docker-compose -f docker-compose.phase0.5.yml --profile admin up -d pgadmin

# Open browser
open http://localhost:5051

# Credentials
Email: admin@dreamseed.ai
Password: admin

# Add server connection
Host: postgres
Port: 5432
Database: dreamseed_dev
Username: postgres
Password: DreamSeedAi0908
```

## 🔄 Common Commands

### Start/Stop
```bash
# Start all services
docker-compose -f docker-compose.phase0.5.yml up -d

# Start with rebuild
docker-compose -f docker-compose.phase0.5.yml up -d --build

# Stop all services
docker-compose -f docker-compose.phase0.5.yml down

# Stop and remove volumes
docker-compose -f docker-compose.phase0.5.yml down -v
```

### Logs
```bash
# All services
docker-compose -f docker-compose.phase0.5.yml logs -f

# Specific service
docker-compose -f docker-compose.phase0.5.yml logs -f backend
docker-compose -f docker-compose.phase0.5.yml logs -f postgres
docker-compose -f docker-compose.phase0.5.yml logs -f redis
```

### Shell Access
```bash
# Backend shell
docker exec -it dreamseed_backend_phase05 /bin/bash

# PostgreSQL shell
docker exec -it dreamseed_postgres_phase05 /bin/sh

# Redis shell
docker exec -it dreamseed_redis_phase05 /bin/sh
```

## 🧹 Cleanup

### Remove Containers Only
```bash
docker-compose -f docker-compose.phase0.5.yml down
```

### Remove Containers and Volumes
```bash
docker-compose -f docker-compose.phase0.5.yml down -v
```

### Full Cleanup (Nuclear Option)
```bash
# Stop and remove everything
docker-compose -f docker-compose.phase0.5.yml down -v --rmi all

# Remove dangling volumes
docker volume prune -f

# Remove dangling images
docker image prune -f
```

## 🐛 Troubleshooting

### Port Conflicts
If ports 5433, 6380, or 8001 are already in use:
```bash
# Edit .env
POSTGRES_PORT=5434
REDIS_PORT=6381
BACKEND_PORT=8002
```

### Database Connection Errors
```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.phase0.5.yml ps postgres

# Check logs
docker-compose -f docker-compose.phase0.5.yml logs postgres

# Restart service
docker-compose -f docker-compose.phase0.5.yml restart postgres
```

### Backend Won't Start
```bash
# Check dependencies
docker-compose -f docker-compose.phase0.5.yml ps

# Rebuild backend
docker-compose -f docker-compose.phase0.5.yml build --no-cache backend
docker-compose -f docker-compose.phase0.5.yml up -d backend

# Check logs
docker-compose -f docker-compose.phase0.5.yml logs backend
```

### Auto-Seed Not Working
```bash
# Manual seed inside container
docker exec -it dreamseed_backend_phase05 python3 ../scripts/seed_cat_items.py

# Or from host
cd /path/to/dreamseed_monorepo
export DATABASE_URL="postgresql+psycopg://postgres:DreamSeedAi0908@localhost:5433/dreamseed_dev"
python3 scripts/seed_cat_items.py
```

## 📈 Monitoring

### Resource Usage
```bash
# Check CPU/Memory
docker stats dreamseed_backend_phase05 dreamseed_postgres_phase05 dreamseed_redis_phase05

# Disk usage
docker system df
```

### API Metrics
```bash
# Health endpoint
curl http://localhost:8001/health

# API docs
open http://localhost:8001/docs
```

## 🎯 Next Steps

After Docker setup is complete:

1. ✅ Verify all services healthy
2. ✅ Check seed data loaded
3. ✅ Run E2E tests
4. ✅ Test CAT API endpoints
5. ✅ Performance testing
6. ✅ Complete Phase 0.5!

---

**Need Help?**
- Check logs: `docker-compose -f docker-compose.phase0.5.yml logs -f`
- Restart services: `docker-compose -f docker-compose.phase0.5.yml restart`
- Full reset: `docker-compose -f docker-compose.phase0.5.yml down -v && docker-compose -f docker-compose.phase0.5.yml up -d`

# Backend — Healthcare Data Operations Platform

## Setup

### 1. Environment
```bash
cp ../.env.example .env
# Edit .env — set DATABASE_URL and a strong JWT_SECRET_KEY
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Start PostgreSQL
Using Docker (recommended):
```bash
docker-compose up postgres -d
```

### 4. Run migrations
```bash
python -m alembic upgrade head
```

### 5. Seed development users
```bash
python seed.py
```

Development credentials (LOCAL ONLY — change before any production deployment):
| Email | Password | Role |
|---|---|---|
| admin@example.com | Admin1234! | ADMIN |
| worker@example.com | Worker1234! | WORKER |

### 6. Start the API
```bash
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## Switching to AWS RDS
Only change `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql://username:password@<RDS_ENDPOINT>:5432/healthcare_db
```
No code changes required.

## Running Tests
```bash
python -m pytest tests/ -v
```
Tests use an in-memory SQLite database — no PostgreSQL required.

## API Endpoints
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /auth/login | Public | Login, returns JWT |
| GET | /auth/me | JWT | Current user info |
| POST | /auth/logout | Public | Clears client token |
| GET | /admin/dashboard | ADMIN | Admin-only |
| GET | /worker/dashboard | WORKER | Worker-only |

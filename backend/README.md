# FastAPI Backend

This contains the backend services of the Healthcare Data Operations Platform.

## Run Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Initialize database:
   ```bash
   alembic upgrade head
   python -m app.database  # to verify base connection
   ```
3. Run dev server:
   ```bash
   uvicorn app.main:app --reload
   ```

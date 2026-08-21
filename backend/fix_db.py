from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text('ALTER TABLE audit_logs ALTER COLUMN "timestamp" DROP NOT NULL;'))
        conn.execute(text('ALTER TABLE audit_logs ALTER COLUMN "timestamp" SET DEFAULT NOW();'))
        conn.commit()
        print("Updated timestamp column successfully.")
    except Exception as e:
        print("Error:", e)


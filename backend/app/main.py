from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, protected, anomalies
from app.routers import auth, protected, admin, anomalies, ml, datasets

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Backend API for Healthcare Data Operations Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(protected.router)
app.include_router(anomalies.router)
app.include_router(admin.router)
app.include_router(anomalies.router)
app.include_router(ml.router)
app.include_router(datasets.router)   # GET/POST /anomalies + WS /anomalies/ws


@app.get("/")
def read_root():
    return {"message": "Healthcare Data Operations Platform API"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "env": settings.ENV}

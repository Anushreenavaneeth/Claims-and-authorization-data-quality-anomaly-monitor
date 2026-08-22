from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, protected, admin, anomalies, ml, datasets, dashboard, pipeline, reviews, actions
from app.database import init_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="Healthcare Data Quality & Anomaly Monitoring Platform API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    init_db()

# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(protected.router)
app.include_router(admin.router)
app.include_router(anomalies.router)
app.include_router(ml.router)
app.include_router(datasets.router)
app.include_router(dashboard.router)   # GET /api/dashboard/*, /api/anomalies/integrated, etc.
app.include_router(pipeline.router)    # POST /api/process, GET /api/process/status
app.include_router(reviews.router)     # POST/GET/PATCH /reviews
app.include_router(actions.router)     # POST/GET/PATCH /actions


@app.get("/")
def read_root():
    return {"message": "Healthcare Data Operations Platform API v2"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "env": settings.ENV, "version": "2.0.0"}

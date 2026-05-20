from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config.config_loader import get_app_settings
from src.api.routes import mis_routes, master_routes, circular_routes, achievement_routes, campaign_routes, communication_routes, content_routes

app_settings = get_app_settings()

app = FastAPI(
    title=app_settings.app_title + " API",
    description=app_settings.app_description,
    version="1.0.0"
)

# Configure CORS for Next.js frontend (localhost:3000) and future deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(mis_routes.router,          prefix="/api/mis",          tags=["MIS"])
app.include_router(master_routes.router,       prefix="/api/master",       tags=["Master Data"])
app.include_router(circular_routes.router,     prefix="/api/circulars",    tags=["Circulars"])
app.include_router(achievement_routes.router,  prefix="/api/achievements", tags=["Achievements"])
app.include_router(campaign_routes.router,        prefix="/api/campaigns",       tags=["Campaigns"])
app.include_router(communication_routes.router,  prefix="/api/communications",  tags=["Communications"])
app.include_router(content_routes.router,      prefix="/api/content",      tags=["Static Content"])


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "environment": app_settings.environment}

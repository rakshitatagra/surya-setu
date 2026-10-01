from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="SURYA-SETU API",
    description="Rooftop photo -> installable solar capacity -> rupees. "
                 "See README.md and docs/ROADMAP.md for the full pipeline.",
    version="0.1.0",
)

app.include_router(router)

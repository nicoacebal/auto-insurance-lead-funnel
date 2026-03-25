"""Entrypoint del backend API productivo."""

from fastapi import FastAPI

from backend.api.cotizaciones import router as cotizaciones_router
from backend.api.quotes import router as quotes_router
from backend.api.vehicles import router as vehicles_router

app = FastAPI(
    title="Auto Insurance Lead Funnel API",
    version="1.0.0",
    description="API del cotizador automotor con selector profesional de vehiculos.",
)

app.include_router(vehicles_router)
app.include_router(quotes_router)
app.include_router(cotizaciones_router)


@app.get("/salud", tags=["Sistema"])
def salud() -> dict[str, str]:
    return {"estado": "ok"}

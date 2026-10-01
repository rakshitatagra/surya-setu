from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.pipeline.orchestrator import run_assessment
from app.schemas import AssessmentRequest, AssessmentResponse

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/assess", response_model=AssessmentResponse)
def assess(request: AssessmentRequest) -> AssessmentResponse:
    try:
        report = run_assessment(
            latitude=request.latitude,
            longitude=request.longitude,
            monthly_units=request.monthly_units,
            state=request.state,
            roof_image_path=request.roof_image_path,
            obstacle_image_path=request.obstacle_image_path,
            tilt_deg=request.tilt_deg,
            panel_wattage_w=request.panel_wattage_w,
            # NOTE: override kept here (not in production) so the API works
            # out of the box without live internet access to NASA POWER.
            # Remove this override once Stage 5 is validated against real
            # fetched irradiance data - see docs/ROADMAP.md.
            annual_generation_kwh_override=3050,
        )
    except Exception as exc:  # noqa: BLE001 - surfaced to the client deliberately
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AssessmentResponse(report=report)

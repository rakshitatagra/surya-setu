from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AssessmentRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    monthly_units: float = Field(..., gt=0, description="Household's current monthly electricity consumption, in units/kWh")
    state: Optional[str] = Field(None, description="State code for tariff/subsidy lookup, e.g. 'DL'")
    roof_image_path: Optional[str] = Field(None, description="Path to the nadir/satellite roof photo")
    obstacle_image_path: Optional[str] = Field(None, description="Path to the homeowner's oblique terrace photo")
    tilt_deg: float = Field(20, description="Assumed/measured panel tilt angle")
    panel_wattage_w: float = Field(400, description="Wattage per panel used to size the system")


class AssessmentResponse(BaseModel):
    report: dict

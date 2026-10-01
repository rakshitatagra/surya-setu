"""
Stage 5 - Yield simulation.

Two parts:
1. fetch_nasa_power_hourly() - pulls real hourly GHI/DNI/DHI for a
   lat/lon from NASA POWER's free public API. Requires outbound internet
   access at run time (not available inside this sandbox - the function
   is written correctly against NASA POWER's documented API but hasn't
   been live-tested here; run it yourself once you have network access
   and sanity-check a few values against a known-sunny day).
2. estimate_annual_yield() - the actual physics: Perez transposition
   (pvlib) to convert horizontal irradiance onto your tilted, oriented
   panel array, then a simplified PVWatts-style DC power calculation
   with soiling/inverter/degradation derates.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
import pvlib
import requests

NASA_POWER_HOURLY_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"


def fetch_nasa_power_hourly(latitude: float, longitude: float,
                             start_date: str, end_date: str) -> pd.DataFrame:
    """
    start_date / end_date: "YYYYMMDD" strings.
    Returns a DataFrame indexed by UTC datetime with columns ghi, dni, dhi
    (all W/m^2).
    """
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DNI,ALLSKY_SFC_SW_DIFF",
        "community": "RE",
        "longitude": longitude,
        "latitude": latitude,
        "start": start_date,
        "end": end_date,
        "format": "JSON",
    }
    response = requests.get(NASA_POWER_HOURLY_URL, params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()

    param_data = payload["properties"]["parameter"]
    ghi_raw = param_data["ALLSKY_SFC_SW_DWN"]
    dni_raw = param_data["ALLSKY_SFC_SW_DNI"]
    dhi_raw = param_data["ALLSKY_SFC_SW_DIFF"]

    index = pd.to_datetime(list(ghi_raw.keys()), format="%Y%m%d%H", utc=True)
    df = pd.DataFrame(
        {
            "ghi": list(ghi_raw.values()),
            "dni": list(dni_raw.values()),
            "dhi": list(dhi_raw.values()),
        },
        index=index,
    ).sort_index()

    # NASA POWER uses -999 as a missing-data sentinel.
    df = df.replace(-999, 0).clip(lower=0)
    return df


def compute_poa_irradiance(times: pd.DatetimeIndex, latitude: float, longitude: float,
                            tilt_deg: float, surface_azimuth_deg: float,
                            ghi: pd.Series, dni: pd.Series, dhi: pd.Series) -> pd.Series:
    """
    The Perez transposition step named in Stage 5 of the poster: converts
    horizontal-plane irradiance (as reported by NASA POWER) into the
    plane-of-array irradiance actually striking a panel at this specific
    tilt and orientation.
    """
    solpos = pvlib.solarposition.get_solarposition(times, latitude, longitude)
    dni_extra = pvlib.irradiance.get_extra_radiation(times)
    airmass = pvlib.atmosphere.get_relative_airmass(solpos["apparent_zenith"])

    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=tilt_deg,
        surface_azimuth=surface_azimuth_deg,
        solar_zenith=solpos["apparent_zenith"],
        solar_azimuth=solpos["azimuth"],
        dni=dni,
        ghi=ghi,
        dhi=dhi,
        dni_extra=dni_extra,
        airmass=airmass,
        model="perez",
    )
    return poa["poa_global"].clip(lower=0)


def estimate_annual_yield(
    latitude: float,
    longitude: float,
    system_capacity_kw: float,
    tilt_deg: float,
    surface_azimuth_deg: float = 180,  # 180 = south-facing, standard for N. hemisphere
    soiling_derate: float = 0.97,
    inverter_derate: float = 0.96,
    degradation_rate: float = 0.005,
    system_age_years: int = 0,
    year: Optional[int] = None,
) -> dict:
    """
    Fetches a full year of hourly irradiance and returns estimated annual
    generation in kWh, net of soiling/inverter/degradation derates.

    Requires internet access (NASA POWER API) - see module docstring.
    """
    if year is None:
        year = pd.Timestamp.now().year - 1  # use last full calendar year by default

    start = f"{year}0101"
    end = f"{year}1231"

    irradiance = fetch_nasa_power_hourly(latitude, longitude, start, end)

    poa_global = compute_poa_irradiance(
        irradiance.index, latitude, longitude, tilt_deg, surface_azimuth_deg,
        irradiance["ghi"], irradiance["dni"], irradiance["dhi"],
    )

    degradation_factor = (1 - degradation_rate) ** system_age_years
    # Simplified PVWatts-style DC power: POA irradiance relative to the
    # 1000 W/m^2 STC reference, scaled by rated capacity and derates.
    dc_power_kw = (
        (poa_global / 1000.0)
        * system_capacity_kw
        * soiling_derate
        * inverter_derate
        * degradation_factor
    )

    annual_kwh = float(dc_power_kw.sum())  # hourly data -> sum of kW = kWh

    return {
        "year_used": year,
        "annual_generation_kwh": round(annual_kwh, 1),
        "avg_daily_kwh": round(annual_kwh / 365, 2),
    }

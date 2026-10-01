# SURYA-SETU

**One rooftop photo → installable solar capacity → rupees.**

SURYA-SETU turns a rooftop photo and a pin on a map into a plain-language
feasibility report: how many solar panels actually fit after accounting
for obstructions and shadows, what the system costs after the PM Surya
Ghar subsidy, and how many years until it pays back — using a
slab-aware billing model that correctly reflects how Indian electricity
tariffs actually work.

Built against the ~52 lakh Indian households still needed to hit the
government's 1-crore-household rooftop solar target by March 2027, where
survey evidence shows most willing households never start because nobody
can tell them, simply and for free, whether their specific roof works.

Full context, references, and the research this project is built on:
see `docs/ROADMAP.md`.

## What's actually working right now vs. what's a stub

This is an honest, in-progress build — here's exactly where it stands:

| Stage | What it does | Status |
|---|---|---|
| 1. Roof segmentation | Outline the roof from a nadir photo | **Stub** — returns a mock polygon; real model (SAM2) is Phase 5 |
| 2. Obstacle detection | Find & label mumty, tank, dish, vents | **Stub** — returns mock obstacles; real model (YOLOv8-seg, fine-tuned) is Phase 6 |
| 3. Shadow geometry | Sun position + shadow casting | **Working** — real `pvlib` sun-position math + `shapely` shadow polygons |
| 4. Panel layout | Fit panels into the shade-free area | **Working** — greedy grid packer with setback/walkway constraints |
| 5. Yield simulation | Annual generation estimate | **Working**, needs internet — real NASA POWER fetch + `pvlib` Perez transposition. Not live-tested in this repo's dev environment (network-restricted); verify against a known location once you have internet access. |
| 6. Financial engine | Slab-aware savings, subsidy, payback, LCOE | **Working & tested** — reproduces the project's own worked example (₹13,200/year saving on a 500-unit household with 200 units of solar) exactly |
| 7. Report generation | Assemble the final report | **Working** (v1) — P10/P90 range is currently a placeholder ±15% band, not yet a real Monte Carlo simulation |

Stages 1 and 2 use **mock mode** by default so the whole pipeline runs
end-to-end today, even before the CV models are trained. This is
deliberate: the geometry, packing, yield, and financial stages can be
built, tested, and validated completely independently of the two hardest
(AI) stages — see `docs/ROADMAP.md` for why this build order was chosen.

## Quickstart

```bash
git clone <your-repo-url>
cd surya-setu
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the test suite
pytest -v

# Run the full pipeline directly, no server needed
python -c "
from app.pipeline.orchestrator import run_assessment
import json
report = run_assessment(
    latitude=28.6139, longitude=77.2090,
    monthly_units=500, state='DL',
    annual_generation_kwh_override=3050,  # skip the live NASA POWER call
)
print(json.dumps(report, indent=2))
"

# Or run it as an API
uvicorn app.main:app --reload
# then POST to http://localhost:8000/assess, or see /docs for the
# interactive Swagger UI FastAPI generates automatically
```

## Architecture

```
Client → API gateway (FastAPI) → [orchestrator] → 7-stage pipeline → Report
                                        │
                    ┌───────────────────┼───────────────────┐
              Data layer                                External data
        (Postgres+PostGIS, S3 — Phase 8)          (NASA POWER, DISCOM tariffs)
```

Each pipeline stage lives in its own module under `app/services/`, kept
deliberately independent of the others — same input/output contract
whether it's called synchronously (as it is now, for a working v1) or
later as an async Celery task chain (Phase 8), which is the natural next
step once Stage 2's human-confirmation step needs to pause the pipeline
for real user input in a live frontend.

```
app/
├── config.py              # constants: panel size, derates, cost assumptions
├── schemas.py              # Pydantic request/response models
├── data/
│   ├── tariff_slabs.json   # ⚠ illustrative sample DISCOM slabs — replace with real data
│   └── subsidy_rules.json  # PM Surya Ghar subsidy tiers
├── services/
│   ├── roof_segmentation.py    # Stage 1 (stub)
│   ├── obstacle_detection.py   # Stage 2 (stub)
│   ├── solar_geometry.py       # Stage 3 (working)
│   ├── panel_layout.py         # Stage 4 (working)
│   ├── yield_simulation.py     # Stage 5 (working, needs internet)
│   ├── financial_engine.py     # Stage 6 (working, tested)
│   └── report_generator.py     # Stage 7 (working)
├── pipeline/
│   └── orchestrator.py     # wires all 7 stages together
├── api/
│   └── routes.py           # POST /assess, GET /health
└── main.py                 # FastAPI app
```

## A worked example, verified by the test suite

Run `pytest tests/test_financial_engine.py -v` and you'll see
`test_savings_reproduces_poster_worked_example` pass — this reproduces,
in code, the project's own headline claim: a Delhi household on 500
units/month, with solar generating 200 units/month, saves **₹13,200/year**
under correct slab-aware billing versus only **₹10,300/year** under the
naive "generation × average rate" method most simple calculators use —
a ~28% difference that comes purely from how progressive slab billing
actually works, not from any optimistic assumption. See
`app/services/financial_engine.py` for the full logic and comments.

## Known limitations (stated honestly, not hidden)

- Stages 1 and 2 are not yet backed by real models — see the status table above.
- Stage 3's shadow casting approximates each obstacle's shadow as a convex
  hull rather than a full 3D silhouette projection — a reasonable
  approximation for roughly box-shaped rooftop obstacles, documented as
  a v2 upgrade in the code.
- Stage 4's panel packing is a greedy grid heuristic, not the
  closer-to-optimal OR-Tools CP-SAT solve described in the roadmap.
- Stage 5's NASA POWER fetch hasn't been live-tested in this development
  environment due to network restrictions — the code is written correctly
  against NASA POWER's documented API, but test it yourself against a
  known location before trusting it.
- The illustrative tariff slabs and system-cost-per-kW figure in
  `app/data/` and `app/config.py` are **placeholders for development and
  testing** — replace them with real, current DISCOM tariff data and real
  vendor pricing before using this for any actual financial decision.

## Roadmap

See `docs/ROADMAP.md` for the full phase-by-phase build plan, including
what's next (CVAT/Label Studio dataset labeling, fine-tuning YOLOv8-seg,
the Celery async pipeline migration, and the 20–30 rooftop pilot
validation against a professional surveyor).

## License

MIT — see `LICENSE`.

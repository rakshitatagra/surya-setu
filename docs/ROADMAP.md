# Build Roadmap

The full reasoning behind this phase order, and what to learn at each
step, is worth keeping alongside the code so the "why this order" isn't
lost. Condensed version below; expand any phase into its own issue/board
as you go.

**Why this order:** the non-AI stages (3, 4, 5, 6) are pure geometry and
arithmetic — fast to build, fast to test, and they validate the
project's actual differentiator (slab-aware billing) before any time is
spent on the two genuinely hard AI stages. Stages 1 and 2 run in mock
mode until their own phases below are done, so the pipeline is always
runnable end-to-end.

## Phase 0 — Foundations
Python intermediate, git/GitHub, REST API basics, refreshed trig — done
implicitly by working through Phases 1–3 below.

## Phase 1 — Financial engine ✅ done
`app/services/financial_engine.py` + `tests/test_financial_engine.py`.
Learn: Indian DISCOM slab tariffs (read one real tariff order), the
PM Surya Ghar subsidy guidelines (read the actual MNRE doc), `pytest`.

## Phase 2 — Solar geometry engine ✅ done
`app/services/solar_geometry.py` + `tests/test_solar_geometry.py`.
Learn: sun-position astronomy basics, `pvlib`'s solar position module,
`shapely`'s polygon operations (union/intersection/difference).

## Phase 3 — Panel layout ✅ done
`app/services/panel_layout.py` + `tests/test_panel_layout.py`.
Learn: 2D bin-packing as a CS problem; next upgrade is Google OR-Tools'
CP-SAT solver for a closer-to-optimal packing (work through OR-Tools'
official CP-SAT primer when you get here) plus row pitch derived from
`solar_geometry`'s worst-case sun elevation.

## Phase 4 — CV fundamentals (learn before building)
CNNs conceptually (CS231n lecture material), semantic vs. instance
segmentation, transfer learning, PyTorch basics, IoU/precision/recall.

## Phase 5 — Stage 1: real roof segmentation
Replace `app/services/roof_segmentation.py`'s mock with Meta's SAM2,
zero-shot with a bounding-box/point prompt, run against a real nadir
tile fetched from a satellite tile provider (Google Maps Static API or
Mapbox) by lat/lon. Validate IoU against a handful of hand-labeled roofs.

## Phase 6 — Data labeling + Stage 2: real obstacle detection
Label 100–300+ real Indian rooftop photos in CVAT or Label Studio
(taxonomy: mumty, water tank, satellite dish, vents, parapet). Fine-tune
YOLOv8-seg (via the `ultralytics` package) on that dataset. Build the
three-tap confirm/reject/relabel UI — every correction becomes new
training data for the next fine-tuning round.

## Phase 7 — Stage 3b: height estimation
Add monocular height estimation (Depth Anything V2 or MiDaS, pretrained,
no fine-tuning needed initially) to feed real obstacle heights into the
already-working `solar_geometry.cast_shadow()`, calibrated against a
known reference object (parapet, doorway) in frame.

## Phase 8 — Async pipeline migration
Move `app/pipeline/orchestrator.py` from a synchronous function call to
a Celery task chain (Celery + Redis), with an explicit pause point after
Stage 2 for the human-confirmation step. Add PostgreSQL + PostGIS for
persisting jobs and roof geometries; Docker Compose for local dev.

## Phase 9 — Frontend
Next.js + Tailwind. Photo/pin capture, the tap-to-confirm obstacle UI
(HTML canvas overlay on the uploaded photo), and the report view.

## Phase 10 — Deployment & validation
Deploy `docker-compose` to a single cloud VM. Run the 20–30 rooftop
pilot against a professional surveyor's measurements. Upgrade Stage 7's
placeholder ±15% band to a real Monte Carlo simulation sampling height,
irradiance, and tariff uncertainty for genuine P10/P50/P90 output.

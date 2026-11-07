"""Quick Day 17 feature check for interview prep."""
import sys, os
sys.path.insert(0, r"d:\Projects\cargopulse-ai\backend")
os.environ["PYTHONIOENCODING"] = "utf-8"

PASS = "[OK]  "
FAIL = "[FAIL]"
results = []

def chk(label, ok, detail=""):
    sym = PASS if ok else FAIL
    results.append(ok)
    suffix = f" — {detail}" if detail else ""
    print(f"  {sym} {label}{suffix}")

print("\n========= Day 17 — Quick Feature Check =========\n")

# ── 1. Imports ────────────────────────────────────────────────────────────────
print("1. IMPORTS")
try:
    from app.ai.decision_engine.optimizer import rank_options, ObjectiveWeights, _ALWAYS_UNAVAILABLE
    chk("optimizer.py imports OK", True)
except Exception as e:
    chk("optimizer.py imports OK", False, str(e)[:80]); sys.exit(1)

try:
    from app.services.dependency_graph_service import (
        _delay_severity, DELAY_THRESHOLD_HIGH, DELAY_THRESHOLD_MEDIUM,
        DELAY_THRESHOLD_LOW, _build_impact_summary
    )
    chk("dependency_graph_service.py imports OK", True)
except Exception as e:
    chk("dependency_graph_service.py imports OK", False, str(e)[:80]); sys.exit(1)

try:
    from app.api.optimizer import WeightsRequest
    from app.api.dependency_graph import router as dep_router
    from app.models.dependency_graph import DependencyGraph
    from app.ai.decision_engine.recommender import CANDIDATE_SHIPPING_MODES
    chk("API routers + DB model + recommender import OK", True)
except Exception as e:
    chk("API routers + DB model + recommender import OK", False, str(e)[:80])

# ── 2. Router registration ────────────────────────────────────────────────────
print("\n2. FASTAPI ROUTER REGISTRATION")
try:
    from app.main import app

    # FastAPI stores included routers as _IncludedRouter (a dataclass) with an
    # `original_router` attribute containing the actual APIRouter and its routes.
    all_paths = []
    for r in app.routes:
        orig = getattr(r, "original_router", None)
        if orig:
            for sub in getattr(orig, "routes", []):
                p = getattr(sub, "path", "")
                if p:
                    all_paths.append(p)
        else:
            p = getattr(r, "path", "")
            if p:
                all_paths.append(p)

    chk("/optimizer route registered",        any("/optimizer" in p for p in all_paths))
    chk("/dependency-graph route registered", any("/dependency-graph" in p for p in all_paths))
except Exception as e:
    chk("app.main import", False, str(e)[:80])

# ── 3. Optimizer — scoring ─────────────────────────────────────────────────────
print("\n3. OPTIMIZER SCORING")
OPTS = [
    {"shipping_mode": "Same Day",       "delay_probability": 0.3563, "eta_days": 3.15},
    {"shipping_mode": "First Class",    "delay_probability": 0.4977, "eta_days": 3.84},
    {"shipping_mode": "Second Class",   "delay_probability": 0.3517, "eta_days": 4.22},
    {"shipping_mode": "Standard Class", "delay_probability": 0.3518, "eta_days": 4.12},
]
ranked = rank_options(OPTS, ObjectiveWeights(w_delay=0.7, w_eta=0.3))
chk("4 shipping modes scored", len(ranked) == 4)
chk("composite_scores in [0,1]", all(0 <= o.composite_score <= 1 for o in ranked))
chk("sorted descending by composite_score",
    all(ranked[i].composite_score >= ranked[i+1].composite_score for i in range(len(ranked)-1)))
chk("cost_score always None (not fabricated)", all(o.cost_score is None for o in ranked))
chk("impact_score always None (not fabricated)", all(o.impact_score is None for o in ranked))
chk("'cost' never in available_objectives", all("cost" not in o.available_objectives for o in ranked))
top = ranked[0].shipping_mode
chk(f"#1 ranked: {top}", True)

# ── 4. Pareto ─────────────────────────────────────────────────────────────────
print("\n4. PARETO-OPTIMAL")
pareto = [o.shipping_mode for o in ranked if o.is_pareto_optimal]
chk("At least one Pareto-optimal option", len(pareto) >= 1, f"pareto={pareto}")
chk("Same Day is Pareto-optimal (best on both metrics)", "Same Day" in pareto)
# clear domination test
dominated = rank_options([
    {"shipping_mode": "A", "delay_probability": 0.2, "eta_days": 2.0},
    {"shipping_mode": "B", "delay_probability": 0.5, "eta_days": 5.0},
])
by = {o.shipping_mode: o for o in dominated}
chk("A dominates B → A Pareto-optimal", by["A"].is_pareto_optimal)
chk("A dominates B → B NOT Pareto-optimal", not by["B"].is_pareto_optimal)

# ── 5. Weight validation ───────────────────────────────────────────────────────
print("\n5. WEIGHT VALIDATION")
try:
    ObjectiveWeights(w_delay=-1, w_eta=1)
    chk("Negative weight rejected", False)
except ValueError:
    chk("Negative weight rejected", True)
try:
    ObjectiveWeights(w_delay=0, w_eta=0)
    chk("All-zero weights rejected", False)
except ValueError:
    chk("All-zero weights rejected", True)

w = ObjectiveWeights(w_delay=70, w_eta=30)
eff = w.effective_weights(frozenset(["delay", "eta"]))
chk("Weights normalised to sum 1.0", abs(sum(eff.values()) - 1.0) < 1e-9,
    f"delay={eff['delay']:.2f} eta={eff['eta']:.2f}")

# ── 6. API schema validation ──────────────────────────────────────────────────
print("\n6. API SCHEMA (WeightsRequest)")
from pydantic import ValidationError
try:
    WeightsRequest(w_delay=-1, w_eta=1)
    chk("Negative weight → ValidationError", False)
except (ValidationError, ValueError):
    chk("Negative weight → ValidationError", True)
try:
    WeightsRequest(w_delay=0, w_eta=0, w_cost=0, w_impact=0)
    chk("All-zero → ValidationError", False)
except (ValidationError, ValueError):
    chk("All-zero → ValidationError", True)
w_ok = WeightsRequest(w_delay=0.7, w_eta=0.3)
chk("Valid weights accepted", w_ok.w_delay == 0.7)

# ── 7. Dependency graph service logic ─────────────────────────────────────────
print("\n7. DEPENDENCY GRAPH — SEVERITY THRESHOLDS")
chk("0.80 → HIGH",   _delay_severity(0.80) == "HIGH")
chk("0.70 → HIGH",   _delay_severity(0.70) == "HIGH")
chk("0.69 → MEDIUM", _delay_severity(0.69) == "MEDIUM")
chk("0.50 → MEDIUM", _delay_severity(0.50) == "MEDIUM")
chk("0.49 → LOW",    _delay_severity(0.49) == "LOW")
chk("0.30 → LOW",    _delay_severity(0.30) == "LOW")
chk("0.29 → NONE",   _delay_severity(0.29) == "NONE")

# ── 8. Impact summary ─────────────────────────────────────────────────────────
print("\n8. DEPENDENCY GRAPH — IMPACT SUMMARY")
nodes = [
    {"label": "Route A",   "impact_status": "IMPACTED",     "data_source": "database"},
    {"label": "Order B",   "impact_status": "IMPACTED",     "data_source": "database"},
    {"label": "Unknown X", "impact_status": "unavailable",  "data_source": "missing"},
]
delay_info = {"delay_probability": 0.80, "severity": "HIGH", "model_available": True, "error": None}
summary = _build_impact_summary(delay_info, nodes)
chk("cost_impact always None", summary["cost_impact"] is None)
chk("cost_impact_note present", bool(summary.get("cost_impact_note")))
chk("impacted_downstream_count = 2", summary["impacted_downstream_count"] == 2)
chk("unavailable_count = 1", summary["unavailable_count"] == 1)
chk("Missing node in unavailable_labels", "Unknown X" in summary["unavailable_labels"])

# ── 9. Existing recommender regression ────────────────────────────────────────
print("\n9. EXISTING RECOMMENDER (REGRESSION)")
chk("CANDIDATE_SHIPPING_MODES non-empty", len(CANDIDATE_SHIPPING_MODES) >= 2,
    str(CANDIDATE_SHIPPING_MODES))
chk("DependencyGraph table name", DependencyGraph.__tablename__ == "dependency_graph")

# ── 10. Frontend files ────────────────────────────────────────────────────────
print("\n10. FRONTEND FILES")
import os
frontend = r"d:\Projects\cargopulse-ai\frontend\src"
files = {
    "Optimizer.tsx":       os.path.join(frontend, "pages", "Optimizer.tsx"),
    "DependencyGraph.tsx": os.path.join(frontend, "pages", "DependencyGraph.tsx"),
    "optimizerService.ts": os.path.join(frontend, "services", "optimizerService.ts"),
    "AppRoutes.tsx":       os.path.join(frontend, "routes", "AppRoutes.tsx"),
    "MainLayout.tsx":      os.path.join(frontend, "layouts", "MainLayout.tsx"),
}
for name, path in files.items():
    exists = os.path.isfile(path)
    chk(f"{name} exists", exists)

# Check routes wired
with open(files["AppRoutes.tsx"]) as f:
    routes_src = f.read()
chk("/optimizer route in AppRoutes.tsx", '"/optimizer"' in routes_src)
chk("/dependency-graph route in AppRoutes.tsx", '"/dependency-graph"' in routes_src)

# Check nav wired
with open(files["MainLayout.tsx"]) as f:
    nav_src = f.read()
chk("Optimizer in MainLayout nav", "Optimizer" in nav_src)
chk("Dep. Graph in MainLayout nav", "Dep. Graph" in nav_src)
chk("AI Decision Engine section in nav", "AI Decision Engine" in nav_src)

# ── Summary ───────────────────────────────────────────────────────────────────
passed = sum(results)
failed = len(results) - passed
print(f"\n{'='*49}")
print(f"  TOTAL: {passed} passed, {failed} failed out of {len(results)} checks")
if failed == 0:
    print("  ✓ All Day 17 features verified — ready to present!")
else:
    print("  ✗ Some checks failed — see above")
    sys.exit(1)

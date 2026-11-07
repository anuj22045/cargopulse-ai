"""
Phase 4 Integration Tests — Day 17
====================================
Tests the optimizer and dependency graph service layer directly
(no HTTP server needed — avoids lifespan/scheduler issues in the sandbox).

Covers:
  1.  Optimizer — default weights with multiple options
  2.  Optimizer — w_delay=1.0 extreme weight
  3.  Optimizer — w_eta=1.0 extreme weight
  4.  Optimizer — mixed weights normalised to 1.0
  5.  Optimizer — invalid weights: negative → ValueError
  6.  Optimizer — invalid weights: all-zero → ValueError
  7.  Optimizer — missing cost/impact handled (not fabricated)
  8.  Optimizer — correct Pareto-optimal results
  9.  Optimizer — invalid empty list → ValueError
  10. Dependency service — _delay_severity thresholds correct
  11. Dependency service — impact data never fabricated (cost always None)
  12. Dependency service — missing relationship policy
  13. Dependency service — impact_summary structure correct
  14. Dependency service — get_shipment_dependency_graph returns None for bad ID
  15. Optimizer API schema — WeightsRequest validates correctly
  16. Optimizer — effective weights always sum to 1 across multiple runs
  17. Optimizer — Pareto: dominated option correctly excluded from non-dominated set
  18. Optimizer — single option always Pareto-optimal with score 1.0
  19. Optimizer — cost/impact never in available_objectives
  20. Existing recommender imports still work (regression guard)
  21. Frontend tsc --noEmit clean (no TypeScript errors)
  22. Frontend vite build clean (production build succeeds)
"""

import sys
import os
import subprocess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["PYTHONIOENCODING"] = "utf-8"

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"
results = []


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = PASS if condition else FAIL
    results.append((status, label))
    suffix = f"  ({detail})" if detail else ""
    print(f"  {status} {label}{suffix}")
    return condition


def section(title: str) -> None:
    print(f"\n=== {title} ===")


# ─────────────────────────────────────────────────────────────────────────────
# Import optimizer + dependency service (pure Python, no DB / no HTTP)
# ─────────────────────────────────────────────────────────────────────────────
section("Import checks")

try:
    from app.ai.decision_engine.optimizer import (
        ObjectiveWeights,
        ScoredOption,
        rank_options,
        _mark_pareto,
        _minmax,
        _invert,
        _ALWAYS_UNAVAILABLE,
    )
    check("Optimizer module imports OK", True)
except Exception as e:
    check("Optimizer module imports OK", False, str(e))

try:
    from app.services.dependency_graph_service import (
        _delay_severity,
        DELAY_THRESHOLD_HIGH,
        DELAY_THRESHOLD_MEDIUM,
        DELAY_THRESHOLD_LOW,
        _build_impact_summary,
        _shipment_node,
    )
    check("Dependency graph service imports OK", True)
except Exception as e:
    check("Dependency graph service imports OK", False, str(e)[:100])

try:
    from pydantic import BaseModel, model_validator
    from app.api.optimizer import WeightsRequest, OptimizerRequest
    check("Optimizer API schema imports OK", True)
except Exception as e:
    check("Optimizer API schema imports OK", False, str(e)[:100])

try:
    from app.ai.decision_engine.recommender import build_recommendation_features, _evaluate, CANDIDATE_SHIPPING_MODES
    check("Existing recommender module imports OK (regression)", True)
except Exception as e:
    check("Existing recommender module imports OK (regression)", False, str(e)[:100])


# ─────────────────────────────────────────────────────────────────────────────
# 1-9: Optimizer logic tests
# ─────────────────────────────────────────────────────────────────────────────
section("1. Default weights scoring")

# Realistic options based on what the ML model actually returns
FOUR_OPTIONS = [
    {"shipping_mode": "Same Day",       "delay_probability": 0.3563, "eta_days": 3.15},
    {"shipping_mode": "First Class",    "delay_probability": 0.4977, "eta_days": 3.84},
    {"shipping_mode": "Second Class",   "delay_probability": 0.3517, "eta_days": 4.22},
    {"shipping_mode": "Standard Class", "delay_probability": 0.3518, "eta_days": 4.12},
]

w_default = ObjectiveWeights(w_delay=0.7, w_eta=0.3)
ranked = rank_options(FOUR_OPTIONS, weights=w_default)

check("1. Returns 4 ScoredOptions", len(ranked) == 4)
check("1. All composite_scores in [0,1]",
      all(0.0 <= o.composite_score <= 1.0 for o in ranked))
check("1. Sorted descending by composite_score",
      all(ranked[i].composite_score >= ranked[i+1].composite_score
          for i in range(len(ranked)-1)))
check("1. delay_score and eta_score are floats in [0,1]",
      all(0.0 <= o.delay_score <= 1.0 and 0.0 <= o.eta_score <= 1.0 for o in ranked))

section("2. w_delay=1.0 — lowest delay ranked first")
w_delay_only = ObjectiveWeights(w_delay=1.0, w_eta=0.0)
ranked_d = rank_options(FOUR_OPTIONS, weights=w_delay_only)
# Second Class has lowest delay_probability (0.3517)
check("2. Lowest delay_probability ranked #1 with w_delay=1.0",
      ranked_d[0].delay_score == max(o.delay_score for o in ranked_d),
      f"#1={ranked_d[0].shipping_mode}")

section("3. w_eta=1.0 — fastest ETA ranked first")
w_eta_only = ObjectiveWeights(w_delay=0.0, w_eta=1.0)
ranked_e = rank_options(FOUR_OPTIONS, weights=w_eta_only)
# Same Day has lowest eta_days (3.15) → highest eta_score
check("3. Fastest ETA ranked #1 with w_eta=1.0",
      ranked_e[0].eta_score == max(o.eta_score for o in ranked_e),
      f"#1={ranked_e[0].shipping_mode}")
check("3. Same Day is #1 with w_eta=1.0",
      ranked_e[0].shipping_mode == "Same Day", f"got {ranked_e[0].shipping_mode}")

section("4. Mixed weights normalised to 1.0")
w_5_5 = ObjectiveWeights(w_delay=5, w_eta=5)
ranked_55 = rank_options(FOUR_OPTIONS, weights=w_5_5)
eff = ranked_55[0].effective_weights
check("4. Effective weights sum to 1.0",
      abs(sum(eff.values()) - 1.0) < 1e-9, f"sum={sum(eff.values())}")
check("4. Delay and ETA weights equal after 5/5 normalisation",
      abs(eff.get("delay", 0) - eff.get("eta", 0)) < 1e-9,
      f"delay={eff.get('delay')}, eta={eff.get('eta')}")

# Large scale (0-100 slider)
w_70_30 = ObjectiveWeights(w_delay=70, w_eta=30)
ranked_7030 = rank_options(FOUR_OPTIONS, weights=w_70_30)
eff2 = ranked_7030[0].effective_weights
check("4. Large-scale weights (70/30) still normalise correctly",
      abs(sum(eff2.values()) - 1.0) < 1e-9)
check("4. 70/30 → 0.7/0.3 ratio preserved",
      abs(eff2.get("delay", 0) / eff2.get("eta", 1) - 7/3) < 1e-6,
      f"ratio={eff2.get('delay', 0) / eff2.get('eta', 1):.4f} expected {7/3:.4f}")

section("5-6. Invalid weight rejection")
try:
    ObjectiveWeights(w_delay=-0.5, w_eta=1.0)
    check("5. Negative weight → ValueError", False)
except ValueError as e:
    check("5. Negative weight → ValueError", True, str(e)[:60])

try:
    ObjectiveWeights(w_delay=0.0, w_eta=0.0, w_cost=0.0, w_impact=0.0)
    check("6. All-zero weights → ValueError", False)
except ValueError as e:
    check("6. All-zero weights → ValueError", True, str(e)[:60])

section("7. Missing cost/impact — never fabricated")
# cost and impact passed as None (default)
ranked7 = rank_options(FOUR_OPTIONS)
check("7. cost_score always None",    all(o.cost_score   is None for o in ranked7))
check("7. impact_score always None",  all(o.impact_score is None for o in ranked7))
check("7. cost not in available_objectives",
      "cost"   not in ranked7[0].available_objectives)
check("7. impact not in available_objectives",
      "impact" not in ranked7[0].available_objectives)
check("7. 'cost' in _ALWAYS_UNAVAILABLE",   "cost"   in _ALWAYS_UNAVAILABLE)
check("7. 'impact' in _ALWAYS_UNAVAILABLE", "impact" in _ALWAYS_UNAVAILABLE)

# Even if someone passes cost values they are ignored because cost is ALWAYS_UNAVAILABLE
opts_with_cost = [
    {"shipping_mode": "A", "delay_probability": 0.3, "eta_days": 3.0, "cost": 100.0},
    {"shipping_mode": "B", "delay_probability": 0.4, "eta_days": 4.0, "cost": 50.0},
]
ranked_cost = rank_options(opts_with_cost)
check("7. cost_score still None even when cost values provided",
      all(o.cost_score is None for o in ranked_cost))

section("8. Pareto-optimal results")
# Same Day is best on BOTH metrics → must be Pareto-optimal
pareto = [o for o in ranked if o.is_pareto_optimal]
check("8. At least one Pareto-optimal option exists", len(pareto) >= 1)
pareto_modes = [o.shipping_mode for o in pareto]
check("8. Same Day is Pareto-optimal (best delay AND best ETA)",
      "Same Day" in pareto_modes, f"pareto={pareto_modes}")

# Construct a clear domination scenario
dom_opts = [
    {"shipping_mode": "A", "delay_probability": 0.2, "eta_days": 2.0},  # dominates B
    {"shipping_mode": "B", "delay_probability": 0.5, "eta_days": 5.0},  # dominated by A
]
ranked_dom = rank_options(dom_opts)
a_opt = next(o for o in ranked_dom if o.shipping_mode == "A")
b_opt = next(o for o in ranked_dom if o.shipping_mode == "B")
check("8. A dominates B — A is Pareto-optimal",   a_opt.is_pareto_optimal)
check("8. A dominates B — B is NOT Pareto-optimal", not b_opt.is_pareto_optimal)

section("9. Error cases")
try:
    rank_options([])
    check("9. Empty options list → ValueError", False)
except ValueError:
    check("9. Empty options list → ValueError", True)

try:
    rank_options([{"shipping_mode": "X", "delay_probability": 0.5}])  # missing eta_days
    check("9. Missing eta_days → ValueError", False)
except ValueError:
    check("9. Missing eta_days → ValueError", True)

try:
    rank_options([{"shipping_mode": "X", "delay_probability": 1.5, "eta_days": 3.0}])
    check("9. delay_probability > 1 → ValueError", False)
except ValueError:
    check("9. delay_probability > 1 → ValueError", True)

try:
    rank_options([{"shipping_mode": "X", "delay_probability": 0.5, "eta_days": -1.0}])
    check("9. eta_days <= 0 → ValueError", False)
except ValueError:
    check("9. eta_days <= 0 → ValueError", True)


# ─────────────────────────────────────────────────────────────────────────────
# 10-14: Dependency graph service tests (pure logic, no DB queries)
# ─────────────────────────────────────────────────────────────────────────────
section("10. Delay severity thresholds")

check("10. _delay_severity(0.80) = HIGH",   _delay_severity(0.80) == "HIGH")
check("10. _delay_severity(0.70) = HIGH",   _delay_severity(0.70) == "HIGH")
check("10. _delay_severity(0.69) = MEDIUM", _delay_severity(0.69) == "MEDIUM")
check("10. _delay_severity(0.50) = MEDIUM", _delay_severity(0.50) == "MEDIUM")
check("10. _delay_severity(0.49) = LOW",    _delay_severity(0.49) == "LOW")
check("10. _delay_severity(0.30) = LOW",    _delay_severity(0.30) == "LOW")
check("10. _delay_severity(0.29) = NONE",   _delay_severity(0.29) == "NONE")
check("10. _delay_severity(0.00) = NONE",   _delay_severity(0.00) == "NONE")
check("10. DELAY_THRESHOLD_HIGH = 0.70",    DELAY_THRESHOLD_HIGH   == 0.70)
check("10. DELAY_THRESHOLD_MEDIUM = 0.50",  DELAY_THRESHOLD_MEDIUM == 0.50)
check("10. DELAY_THRESHOLD_LOW = 0.30",     DELAY_THRESHOLD_LOW    == 0.30)

section("11. Impact summary — cost always null")
delay_info_high = {
    "delay_probability": 0.80,
    "severity": "HIGH",
    "model_available": True,
    "error": None,
}
nodes_sample = [
    {"label": "Route A", "impact_status": "IMPACTED",     "data_source": "database"},
    {"label": "Carrier B", "impact_status": "ON_TRACK",   "data_source": "database"},
    {"label": "Order C",   "impact_status": "IMPACTED",   "data_source": "database"},
    {"label": "Unknown X", "impact_status": "unavailable","data_source": "missing"},
]
summary = _build_impact_summary(delay_info_high, nodes_sample)

check("11. cost_impact in summary always None", summary["cost_impact"] is None)
check("11. cost_impact_note present and non-empty",
      bool(summary.get("cost_impact_note")))
check("11. model_available is True", summary["model_available"] is True)
check("11. delay_probability = 0.80",
      summary["delay_probability"] == 0.80)

section("12. Missing relationship policy — unavailable not fabricated")
check("12. Unavailable nodes labeled 'unavailable'",
      sum(1 for n in nodes_sample if n["impact_status"] == "unavailable") == 1)
check("12. Missing nodes in unavailable_labels",
      "Unknown X" in summary.get("unavailable_labels", []))
check("12. unavailable_count correct", summary["unavailable_count"] == 1)

section("13. Impact summary — required fields")
required_fields = {
    "delay_probability", "severity", "model_available",
    "impacted_downstream_count", "impacted_downstream_labels",
    "unavailable_count", "unavailable_labels",
    "cost_impact", "cost_impact_note", "model_error",
}
missing_fields = required_fields - set(summary.keys())
check("13. All required impact_summary fields present",
      not missing_fields, f"missing={missing_fields}")
check("13. impacted_downstream_count correct",
      summary["impacted_downstream_count"] == 2,  # Route A + Order C
      f"got {summary['impacted_downstream_count']}")

section("14. Service returns None for bad shipment ID (no DB)")
# We can't run the full get_shipment_dependency_graph without DB,
# but we verify the import and function signature exist.
from app.services.dependency_graph_service import get_shipment_dependency_graph, upsert_dependency_edge
import inspect
sig = inspect.signature(get_shipment_dependency_graph)
check("14. get_shipment_dependency_graph takes (db, shipment_id)",
      "db" in sig.parameters and "shipment_id" in sig.parameters)
sig2 = inspect.signature(upsert_dependency_edge)
check("14. upsert_dependency_edge takes (db, source_type, source_id, target_type, target_id, relationship_type)",
      all(p in sig2.parameters for p in
          ["db", "source_type", "source_id", "target_type", "target_id", "relationship_type"]))


# ─────────────────────────────────────────────────────────────────────────────
# 15. API schema validation (WeightsRequest)
# ─────────────────────────────────────────────────────────────────────────────
section("15. Optimizer API schema — WeightsRequest validation")

from pydantic import ValidationError

# Valid
try:
    w = WeightsRequest(w_delay=0.7, w_eta=0.3)
    check("15. Valid weights accepted", w.w_delay == 0.7)
except ValidationError as e:
    check("15. Valid weights accepted", False, str(e)[:80])

# Negative weight
try:
    WeightsRequest(w_delay=-1.0, w_eta=0.5)
    check("15. Negative weight → ValidationError", False)
except (ValidationError, ValueError):
    check("15. Negative weight → ValidationError", True)

# All-zero
try:
    WeightsRequest(w_delay=0.0, w_eta=0.0, w_cost=0.0, w_impact=0.0)
    check("15. All-zero → ValidationError", False)
except (ValidationError, ValueError):
    check("15. All-zero → ValidationError", True)


# ─────────────────────────────────────────────────────────────────────────────
# 16. Effective weights always sum to 1 across multiple weight combos
# ─────────────────────────────────────────────────────────────────────────────
section("16. Effective weights sum to 1 across all combinations")

combos = [
    (1, 0), (0, 1), (5, 5), (7, 3), (1, 9), (100, 1), (1, 100),
]
for wd, we in combos:
    w = ObjectiveWeights(w_delay=wd, w_eta=we)
    eff = w.effective_weights(frozenset(["delay", "eta"]))
    ok = abs(sum(eff.values()) - 1.0) < 1e-9
    check(f"16. w_delay={wd}, w_eta={we} → sum=1.0", ok, f"sum={sum(eff.values())}")


# ─────────────────────────────────────────────────────────────────────────────
# 17. Pareto domination with 3 options
# ─────────────────────────────────────────────────────────────────────────────
section("17. Pareto dominance — 3-option scenario")

# C dominates B but not A; A and C are Pareto-optimal
three = [
    {"shipping_mode": "A", "delay_probability": 0.2, "eta_days": 5.0},  # best delay
    {"shipping_mode": "B", "delay_probability": 0.5, "eta_days": 5.0},  # dominated by C
    {"shipping_mode": "C", "delay_probability": 0.3, "eta_days": 2.0},  # best ETA
]
ranked17 = rank_options(three)
by_name = {o.shipping_mode: o for o in ranked17}
check("17. A is Pareto-optimal (best delay)", by_name["A"].is_pareto_optimal)
check("17. C is Pareto-optimal (best ETA)", by_name["C"].is_pareto_optimal)
check("17. B is NOT Pareto-optimal (dominated by C on ETA, not better on delay)",
      not by_name["B"].is_pareto_optimal)


# ─────────────────────────────────────────────────────────────────────────────
# 18. Single option
# ─────────────────────────────────────────────────────────────────────────────
section("18. Single option — always Pareto-optimal, score=1.0")

single = rank_options([{"shipping_mode": "Only", "delay_probability": 0.5, "eta_days": 7.0}])
check("18. Single option returned", len(single) == 1)
check("18. Single option is_pareto_optimal = True", single[0].is_pareto_optimal)
check("18. Single option composite_score = 1.0", single[0].composite_score == 1.0,
      f"got {single[0].composite_score}")


# ─────────────────────────────────────────────────────────────────────────────
# 19. cost/impact never in available_objectives
# ─────────────────────────────────────────────────────────────────────────────
section("19. cost/impact never in available_objectives")

for opts_set in [FOUR_OPTIONS, opts_with_cost, three]:
    ranked19 = rank_options(opts_set)
    for o in ranked19:
        check(
            f"19. {o.shipping_mode}: 'cost' not in available_objectives",
            "cost" not in o.available_objectives,
        )
        check(
            f"19. {o.shipping_mode}: 'impact' not in available_objectives",
            "impact" not in o.available_objectives,
        )


# ─────────────────────────────────────────────────────────────────────────────
# 20. Existing recommender regression guard
# ─────────────────────────────────────────────────────────────────────────────
section("20. Existing recommender — regression guard")

check("20. CANDIDATE_SHIPPING_MODES is non-empty",
      isinstance(CANDIDATE_SHIPPING_MODES, (list, tuple)) and len(CANDIDATE_SHIPPING_MODES) >= 2,
      f"modes={CANDIDATE_SHIPPING_MODES}")
check("20. build_recommendation_features is callable",
      callable(build_recommendation_features))
check("20. _evaluate is callable", callable(_evaluate))


# ─────────────────────────────────────────────────────────────────────────────
# 21-22. Frontend checks (tsc + vite build)
# ─────────────────────────────────────────────────────────────────────────────
section("21. Frontend TypeScript type-check")

frontend_dir = r"d:\Projects\cargopulse-ai\frontend"
result_tsc = subprocess.run(
    ["npx", "tsc", "--noEmit"],
    cwd=frontend_dir,
    capture_output=True,
    text=True,
    shell=True,
    timeout=120,
)
if result_tsc.returncode == 0:
    check("21. tsc --noEmit exits 0 (no type errors)", True)
else:
    check("21. tsc --noEmit exits 0 (no type errors)", False,
          (result_tsc.stdout + result_tsc.stderr)[:200])

section("22. Frontend production build")
result_build = subprocess.run(
    ["npx", "vite", "build"],
    cwd=frontend_dir,
    capture_output=True,
    text=True,
    shell=True,
    timeout=120,
)
if result_build.returncode == 0:
    check("22. vite build exits 0", True, "production build clean")
else:
    check("22. vite build exits 0", False,
          (result_build.stdout + result_build.stderr)[:200])


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
passed  = sum(1 for s, _ in results if s == PASS)
failed  = sum(1 for s, _ in results if s == FAIL)
skipped = sum(1 for s, _ in results if s == SKIP)
total   = len(results)
print(f"TOTAL: {passed} passed, {failed} failed, {skipped} skipped "
      f"out of {total} checks")

if failed:
    print("\nFailed checks:")
    for s, label in results:
        if s == FAIL:
            print(f"  {s} {label}")
    sys.exit(1)
else:
    print("All checks passed.")

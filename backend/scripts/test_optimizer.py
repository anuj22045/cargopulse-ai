"""
Phase 1 Tests — Multi-Objective Optimizer
==========================================
Covers:
  1.  Basic scoring with two available objectives (delay + eta)
  2.  Weight validation — negative weight rejected
  3.  Weight validation — all-zero weight rejected
  4.  Weight validation — only eta weight (delay weight = 0)
  5.  Weight normalisation — arbitrary positive values sum to 1 after norm
  6.  Missing metric (cost, impact) — handled via weight collapse, no error
  7.  Pareto filtering — dominated option correctly flagged
  8.  Pareto filtering — all equal → all Pareto-optimal
  9.  Single option → always Pareto-optimal, composite_score computed
  10. Empty options list raises ValueError
  11. Option missing required key raises ValueError
  12. Option with delay_probability outside [0, 1] raises ValueError
  13. Option with eta_days <= 0 raises ValueError
  14. Best delay option ranked first when w_delay=1.0
  15. Best eta option ranked first when w_eta=1.0
  16. to_dict() returns all expected keys
  17. available_objectives never contains 'cost' or 'impact'
  18. cost_score and impact_score are always None
  19. Real model output integration (no ML load — uses literal values from probe)
  20. ObjectiveWeights.effective_weights excludes always-unavailable objectives
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.ai.decision_engine.optimizer import (
    ObjectiveWeights,
    ScoredOption,
    rank_options,
    _mark_pareto,
    _minmax,
    _invert,
    _ALWAYS_UNAVAILABLE,
)

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = PASS if condition else FAIL
    results.append((status, label))
    suffix = f"  ({detail})" if detail else ""
    print(f"  {status} {label}{suffix}")
    return condition


def section(title: str) -> None:
    print(f"\n=== {title} ===")


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_opt(mode, delay_prob, eta_days, cost=None, impact=None):
    return {
        "shipping_mode": mode,
        "delay_probability": delay_prob,
        "eta_days": eta_days,
        "cost": cost,
        "impact": impact,
    }


THREE_OPTIONS = [
    make_opt("Same Day",       0.3563, 3.15),
    make_opt("First Class",    0.4977, 3.84),
    make_opt("Second Class",   0.3517, 4.22),
]

# ── Section 1: Basic scoring ───────────────────────────────────────────────────
section("1. Basic scoring — two objectives")

ranked = rank_options(THREE_OPTIONS)
check("Returns list of ScoredOption",
      all(isinstance(o, ScoredOption) for o in ranked))
check("All options present", len(ranked) == 3)
check("delay_score is float in [0, 1]",
      all(0.0 <= o.delay_score <= 1.0 for o in ranked))
check("eta_score is float in [0, 1]",
      all(0.0 <= o.eta_score <= 1.0 for o in ranked))
check("composite_score is float in [0, 1]",
      all(0.0 <= o.composite_score <= 1.0 for o in ranked))
check("Sorted descending by composite_score",
      all(ranked[i].composite_score >= ranked[i+1].composite_score
          for i in range(len(ranked)-1)))

# ── Section 2 & 3: Weight validation ──────────────────────────────────────────
section("2-3. Weight validation")

try:
    ObjectiveWeights(w_delay=-0.1, w_eta=0.5)
    check("Negative weight rejected", False)
except ValueError as e:
    check("Negative weight rejected", True, str(e)[:60])

try:
    ObjectiveWeights(w_delay=0.0, w_eta=0.0, w_cost=0.0, w_impact=0.0)
    check("All-zero weights rejected", False)
except ValueError as e:
    check("All-zero weights rejected", True, str(e)[:60])

# ── Section 4: Only eta weight ─────────────────────────────────────────────────
section("4. Only eta weight active")

w_eta_only = ObjectiveWeights(w_delay=0.0, w_eta=1.0)
ranked_eta = rank_options(THREE_OPTIONS, weights=w_eta_only)
# Best eta = lowest eta_days = Same Day (3.15)
check("Best ETA mode ranked first with w_eta=1.0",
      ranked_eta[0].shipping_mode == "Same Day",
      f"got {ranked_eta[0].shipping_mode!r}")

# ── Section 5: Weight normalisation ────────────────────────────────────────────
section("5. Weight normalisation")

w_big = ObjectiveWeights(w_delay=70.0, w_eta=30.0)
eff = w_big.effective_weights(frozenset(["delay", "eta"]))
total = sum(eff.values())
check("Effective weights sum to 1.0", abs(total - 1.0) < 1e-9,
      f"sum={total}")
check("Ratio preserved after normalisation",
      abs(eff["delay"] / eff["eta"] - 70/30) < 1e-6,
      f"ratio={eff['delay']}/{eff['eta']}")

# ── Section 6: Missing cost/impact ─────────────────────────────────────────────
section("6. Missing cost/impact — no error, weight collapsed")

# Even if caller passes w_cost=0.5, it should be zeroed out
w_with_cost = ObjectiveWeights(w_delay=0.5, w_eta=0.3, w_cost=0.2)
ranked_nc = rank_options(THREE_OPTIONS, weights=w_with_cost)
check("No error when cost/impact unavailable", len(ranked_nc) == 3)
check("cost_score is always None",
      all(o.cost_score is None for o in ranked_nc))
check("impact_score is always None",
      all(o.impact_score is None for o in ranked_nc))
check("'cost' not in available_objectives",
      all("cost" not in o.available_objectives for o in ranked_nc))
check("effective weights still sum to 1.0",
      all(abs(sum(o.effective_weights.values()) - 1.0) < 1e-6
          for o in ranked_nc))

# ── Section 7: Pareto — dominated option ───────────────────────────────────────
section("7. Pareto — dominated option correctly flagged")

# A dominates B on both objectives
dominated_set = [
    ScoredOption("A", delay_probability=0.2, eta_days=2.0,
                 delay_score=1.0, eta_score=1.0, composite_score=1.0,
                 available_objectives=["delay", "eta"]),
    ScoredOption("B", delay_probability=0.5, eta_days=5.0,
                 delay_score=0.0, eta_score=0.0, composite_score=0.0,
                 available_objectives=["delay", "eta"]),
]
_mark_pareto(dominated_set)
check("A is Pareto-optimal", dominated_set[0].is_pareto_optimal)
check("B is dominated (not Pareto-optimal)", not dominated_set[1].is_pareto_optimal)

# ── Section 8: Pareto — all equal ─────────────────────────────────────────────
section("8. Pareto - all equal -> all optimal")

equal_set = [
    ScoredOption("X", delay_probability=0.4, eta_days=4.0,
                 delay_score=0.5, eta_score=0.5, composite_score=0.5),
    ScoredOption("Y", delay_probability=0.4, eta_days=4.0,
                 delay_score=0.5, eta_score=0.5, composite_score=0.5),
]
_mark_pareto(equal_set)
check("X is Pareto-optimal (tie → not dominated)",
      equal_set[0].is_pareto_optimal)
check("Y is Pareto-optimal (tie → not dominated)",
      equal_set[1].is_pareto_optimal)

# ── Section 9: Single option ───────────────────────────────────────────────────
section("9. Single option")

single = rank_options([make_opt("Same Day", 0.35, 3.0)])
check("Single option is Pareto-optimal", single[0].is_pareto_optimal)
check("Single option composite_score is 1.0",
      single[0].composite_score == 1.0,
      f"got {single[0].composite_score}")

# ── Section 10–13: Error cases ────────────────────────────────────────────────
section("10-13. Error cases")

try:
    rank_options([])
    check("Empty list raises ValueError", False)
except ValueError:
    check("Empty list raises ValueError", True)

try:
    rank_options([{"shipping_mode": "X", "eta_days": 3.0}])  # missing delay_probability
    check("Missing required key raises ValueError", False)
except ValueError:
    check("Missing required key raises ValueError", True)

try:
    rank_options([make_opt("X", 1.5, 3.0)])  # delay_prob > 1
    check("delay_probability > 1 raises ValueError", False)
except ValueError:
    check("delay_probability > 1 raises ValueError", True)

try:
    rank_options([make_opt("X", 0.5, -1.0)])  # eta_days <= 0
    check("eta_days <= 0 raises ValueError", False)
except ValueError:
    check("eta_days <= 0 raises ValueError", True)

# ── Section 14-15: Weight extremes ────────────────────────────────────────────
section("14-15. Weight extremes")

w_delay_only = ObjectiveWeights(w_delay=1.0, w_eta=0.0)
ranked_d = rank_options(THREE_OPTIONS, weights=w_delay_only)
# Best delay = lowest delay_probability = Second Class (0.3517)
check("Best delay mode ranked first with w_delay=1.0",
      ranked_d[0].shipping_mode == "Second Class",
      f"got {ranked_d[0].shipping_mode!r}")

w_eta_only2 = ObjectiveWeights(w_delay=0.0, w_eta=1.0)
ranked_e = rank_options(THREE_OPTIONS, weights=w_eta_only2)
check("Best ETA mode ranked first with w_eta=1.0",
      ranked_e[0].shipping_mode == "Same Day",
      f"got {ranked_e[0].shipping_mode!r}")

# ── Section 16: to_dict() ─────────────────────────────────────────────────────
section("16. to_dict() completeness")

d = ranked[0].to_dict()
EXPECTED_KEYS = {
    "shipping_mode", "delay_probability", "eta_days",
    "cost", "impact", "delay_score", "eta_score",
    "cost_score", "impact_score", "composite_score",
    "effective_weights", "available_objectives", "is_pareto_optimal",
}
missing_keys = EXPECTED_KEYS - set(d.keys())
check("to_dict() has all expected keys", not missing_keys,
      f"missing: {missing_keys}")

# ── Section 17-18: Always None / always excluded ──────────────────────────────
section("17-18. Cost/impact always absent")

check("'cost' in _ALWAYS_UNAVAILABLE", "cost" in _ALWAYS_UNAVAILABLE)
check("'impact' in _ALWAYS_UNAVAILABLE", "impact" in _ALWAYS_UNAVAILABLE)

for o in ranked:
    check(f"{o.shipping_mode}: cost_score is None", o.cost_score is None)
    check(f"{o.shipping_mode}: impact_score is None", o.impact_score is None)

# ── Section 19: Real model values integration ─────────────────────────────────
section("19. Real model output values (from probe run)")

# Values from the probe executed above
real_opts = [
    make_opt("Same Day",       0.3563, 3.15),
    make_opt("First Class",    0.4977, 3.84),
    make_opt("Second Class",   0.3517, 4.22),
    make_opt("Standard Class", 0.3518, 4.12),
]
w_default = ObjectiveWeights(w_delay=0.7, w_eta=0.3)
real_ranked = rank_options(real_opts, weights=w_default)

check("All 4 modes scored", len(real_ranked) == 4)
check("Composite scores in [0, 1]",
      all(0.0 <= o.composite_score <= 1.0 for o in real_ranked))
check("Pareto flags set on all",
      all(isinstance(o.is_pareto_optimal, bool) for o in real_ranked))

pareto_modes = [o.shipping_mode for o in real_ranked if o.is_pareto_optimal]
check("At least one Pareto-optimal mode exists", len(pareto_modes) >= 1,
      f"pareto={pareto_modes}")

# Same Day has lowest delay_prob AND lowest eta_days → must be Pareto-optimal
check("'Same Day' is Pareto-optimal (best on both metrics)",
      "Same Day" in pareto_modes)

print("\n  Ranking:")
for o in real_ranked:
    pareto_mark = " ★" if o.is_pareto_optimal else ""
    print(f"    {o.composite_score:.4f}  {o.shipping_mode:20}"
          f"  delay={o.delay_probability:.4f}  eta={o.eta_days:.2f}d"
          f"  delay_score={o.delay_score:.4f}  eta_score={o.eta_score:.4f}"
          f"{pareto_mark}")

# ── Section 20: effective_weights excludes always-unavailable ─────────────────
section("20. effective_weights excludes always-unavailable objectives")

w_all = ObjectiveWeights(w_delay=0.5, w_eta=0.3, w_cost=0.1, w_impact=0.1)
eff_all = w_all.effective_weights(frozenset(["delay", "eta"]))
check("'cost' excluded from effective_weights", "cost" not in eff_all)
check("'impact' excluded from effective_weights", "impact" not in eff_all)
check("Effective weights sum to 1", abs(sum(eff_all.values()) - 1.0) < 1e-9)

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "="*60)
passed = sum(1 for s, _ in results if s == PASS)
failed = sum(1 for s, _ in results if s == FAIL)
print(f"TOTAL: {passed} passed, {failed} failed out of {len(results)} checks")
if failed:
    print("\nFailed checks:")
    for s, label in results:
        if s == FAIL:
            print(f"  {s} {label}")
    sys.exit(1)
else:
    print("All checks passed.")

"""
Multi-Objective Optimizer — Day 17 Phase 1
===========================================
Scores shipping-mode alternatives using a weighted combination of objectives
derived from the existing ML models (delay predictor + ETA predictor).

Available objectives
--------------------
  delay_score  : derived from delay_probability (lower probability → higher score)
  eta_score    : derived from eta_days          (fewer days → higher score)

Unavailable objectives — missing-data policy
--------------------------------------------
  cost_score   : No shipping-cost model exists in this project. cost is always
                 None. When cost_score is unavailable the caller's w_cost weight
                 is collapsed into zero and the remaining weights are
                 re-normalised so they still sum to 1. This is documented in
                 every scored result via the 'available_objectives' field.

  impact_score : No supply-chain dependency data is populated in the
                 dependency_graph table (0 rows). impact_score is therefore
                 unavailable and handled identically to cost_score.

Scoring
-------
  raw_score = w_delay * delay_score + w_eta * eta_score
              [+ w_cost * cost_score  if cost data available]
              [+ w_impact * impact_score  if impact data available]

  Scores are min-max normalised across the candidate set so that the
  best option on any single metric maps to 1.0 and the worst maps to 0.0.
  Higher raw_score is always better.

Pareto optimality
-----------------
  An option is Pareto-dominated if another option is at least as good on
  every *available* objective and strictly better on at least one.
  Options that are not dominated are Pareto-optimal.

Weight validation
-----------------
  Weights must be non-negative. Weights are normalised to sum to 1 so
  callers may pass any scale (e.g. 0–100 sliders). All-zero weight vectors
  are rejected with ValueError.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ── Constants ─────────────────────────────────────────────────────────────────

SUPPORTED_OBJECTIVES = frozenset(["delay", "eta", "cost", "impact"])

# These objectives are always unavailable in the current project.
_ALWAYS_UNAVAILABLE = frozenset(["cost", "impact"])


# ── Data structures ───────────────────────────────────────────────────────────


@dataclass
class ObjectiveWeights:
    """
    User-supplied weights for each optimisation objective.

    cost and impact default to 0.0 because they are not supported yet.
    Any non-negative values are accepted and normalised internally.
    """
    w_delay: float = 0.7
    w_eta: float = 0.3
    w_cost: float = 0.0
    w_impact: float = 0.0

    def __post_init__(self) -> None:
        for name, val in self._raw_items():
            if val < 0:
                raise ValueError(
                    f"Weight '{name}' must be non-negative, got {val}."
                )
        if sum(v for _, v in self._raw_items()) == 0.0:
            raise ValueError(
                "At least one weight must be > 0."
            )

    def _raw_items(self) -> list[tuple[str, float]]:
        return [
            ("w_delay", self.w_delay),
            ("w_eta", self.w_eta),
            ("w_cost", self.w_cost),
            ("w_impact", self.w_impact),
        ]

    def effective_weights(
        self,
        available: frozenset[str],
    ) -> dict[str, float]:
        """
        Return normalised weights restricted to *available* objectives.

        Objectives in _ALWAYS_UNAVAILABLE or absent from `available`
        have their weight collapsed to 0. The remaining weights are
        re-normalised so they sum to 1.0.
        """
        mapping = {
            "delay": self.w_delay,
            "eta": self.w_eta,
            "cost": self.w_cost,
            "impact": self.w_impact,
        }
        # Zero-out unavailable
        active = {
            k: v for k, v in mapping.items()
            if k in available and k not in _ALWAYS_UNAVAILABLE
        }
        total = sum(active.values())
        if total == 0.0:
            raise ValueError(
                "No available objectives have non-zero weight. "
                "Ensure w_delay and/or w_eta are > 0."
            )
        return {k: v / total for k, v in active.items()}


@dataclass
class ScoredOption:
    """One shipping-mode option with raw metrics and computed scores."""
    shipping_mode: str

    # Raw model outputs (always present)
    delay_probability: float          # [0, 1]
    eta_days: float                   # > 0

    # Always None in the current project — preserved for forward compatibility
    cost: Optional[float] = None
    impact: Optional[float] = None

    # Computed by the optimizer (filled in by rank_options)
    delay_score: Optional[float] = None      # normalised, higher = better
    eta_score: Optional[float] = None        # normalised, higher = better
    cost_score: Optional[float] = None       # always None — no cost model
    impact_score: Optional[float] = None     # always None — no impact data
    composite_score: Optional[float] = None  # weighted sum of available scores

    effective_weights: dict[str, float] = field(default_factory=dict)
    available_objectives: list[str] = field(default_factory=list)
    is_pareto_optimal: bool = False

    def to_dict(self) -> dict:
        return {
            "shipping_mode": self.shipping_mode,
            "delay_probability": self.delay_probability,
            "eta_days": self.eta_days,
            "cost": self.cost,
            "impact": self.impact,
            "delay_score": self.delay_score,
            "eta_score": self.eta_score,
            "cost_score": self.cost_score,
            "impact_score": self.impact_score,
            "composite_score": self.composite_score,
            "effective_weights": self.effective_weights,
            "available_objectives": self.available_objectives,
            "is_pareto_optimal": self.is_pareto_optimal,
        }


# ── Normalization helpers ─────────────────────────────────────────────────────


def _minmax(values: list[float]) -> list[float]:
    """
    Min-max normalise a list to [0, 1].
    All-equal values map to 1.0 (treat them as equally good).
    """
    lo, hi = min(values), max(values)
    if hi == lo:
        return [1.0] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def _invert(values: list[float]) -> list[float]:
    """
    Invert normalised scores so that lower raw value → higher score.
    Applies to delay_probability and eta_days (smaller is better).
    """
    return [1.0 - v for v in values]


# ── Pareto ────────────────────────────────────────────────────────────────────


def _mark_pareto(options: list[ScoredOption]) -> None:
    """
    Mark each option as Pareto-optimal or dominated in-place.

    Uses only *available* per-option objectives (delay_score, eta_score).
    Cost and impact are skipped when None.
    """
    n = len(options)

    def scores(o: ScoredOption) -> list[float]:
        s = []
        if o.delay_score is not None:
            s.append(o.delay_score)
        if o.eta_score is not None:
            s.append(o.eta_score)
        # cost_score / impact_score omitted (always None currently)
        return s

    for i in range(n):
        si = scores(options[i])
        dominated = False
        for j in range(n):
            if i == j:
                continue
            sj = scores(options[j])
            if len(sj) != len(si):
                continue
            # j dominates i if j >= i on all and j > i on at least one
            all_ge = all(sj[k] >= si[k] for k in range(len(si)))
            any_gt = any(sj[k] > si[k] for k in range(len(si)))
            if all_ge and any_gt:
                dominated = True
                break
        options[i].is_pareto_optimal = not dominated


# ── Main API ──────────────────────────────────────────────────────────────────


def rank_options(
    options: list[dict],
    weights: ObjectiveWeights | None = None,
) -> list[ScoredOption]:
    """
    Score and rank shipping-mode alternatives.

    Parameters
    ----------
    options:
        Each dict must contain:
          - shipping_mode  (str)
          - delay_probability (float, [0, 1])
          - eta_days          (float, > 0)
        Optional keys (ignored if absent or None):
          - cost   (float | None)
          - impact (float | None)

    weights:
        ObjectiveWeights instance. Defaults to w_delay=0.7, w_eta=0.3.

    Returns
    -------
    List of ScoredOption, sorted by composite_score descending.
    Pareto-optimal flag is set on each option.

    Raises
    ------
    ValueError  — empty options list, invalid option structure, invalid weights.
    """
    if not options:
        raise ValueError("options must be a non-empty list.")

    if weights is None:
        weights = ObjectiveWeights()

    # ── Validate and wrap options ─────────────────────────────────────────
    scored: list[ScoredOption] = []
    for i, opt in enumerate(options):
        for key in ("shipping_mode", "delay_probability", "eta_days"):
            if key not in opt:
                raise ValueError(
                    f"Option at index {i} is missing required key {key!r}."
                )
        dp = float(opt["delay_probability"])
        if not (0.0 <= dp <= 1.0):
            raise ValueError(
                f"Option {i}: delay_probability must be in [0, 1], got {dp}."
            )
        eta = float(opt["eta_days"])
        if eta <= 0:
            raise ValueError(
                f"Option {i}: eta_days must be > 0, got {eta}."
            )
        scored.append(ScoredOption(
            shipping_mode=str(opt["shipping_mode"]),
            delay_probability=dp,
            eta_days=eta,
            cost=opt.get("cost"),       # None — no cost model
            impact=opt.get("impact"),   # None — no impact data
        ))

    # ── Determine available objectives ───────────────────────────────────
    # An objective is "available" if it has real data for all options and
    # is not in _ALWAYS_UNAVAILABLE.
    available: set[str] = {"delay", "eta"}
    # cost / impact: available only when ALL options provide a non-None value
    # and the objective is not permanently unavailable.
    # (Currently always skipped — kept for future extensibility.)
    for obj, attr in [("cost", "cost"), ("impact", "impact")]:
        if obj not in _ALWAYS_UNAVAILABLE and all(
            getattr(s, attr) is not None for s in scored
        ):
            available.add(obj)

    available_frozen = frozenset(available)
    eff_weights = weights.effective_weights(available_frozen)

    # ── Compute per-objective normalised scores ───────────────────────────
    # delay: lower delay_probability → higher score
    # eta: lower eta_days → higher score
    # Single-option edge case: no comparison exists; the one option is
    # trivially the best, so both scores are set to 1.0.
    delay_probs = [s.delay_probability for s in scored]
    eta_days_vals = [s.eta_days for s in scored]

    if len(scored) == 1:
        delay_scores_norm = [1.0]
        eta_scores_norm = [1.0]
    else:
        delay_scores_norm = _invert(_minmax(delay_probs))
        eta_scores_norm = _invert(_minmax(eta_days_vals))


    for i, s in enumerate(scored):
        s.delay_score = round(delay_scores_norm[i], 4)
        s.eta_score = round(eta_scores_norm[i], 4)
        # cost_score and impact_score remain None
        s.effective_weights = {k: round(v, 4) for k, v in eff_weights.items()}
        s.available_objectives = sorted(available)

    # ── Composite score ───────────────────────────────────────────────────
    for s in scored:
        comp = 0.0
        if "delay" in eff_weights:
            comp += eff_weights["delay"] * s.delay_score
        if "eta" in eff_weights:
            comp += eff_weights["eta"] * s.eta_score
        s.composite_score = round(comp, 4)

    # ── Pareto ────────────────────────────────────────────────────────────
    _mark_pareto(scored)

    # ── Sort by composite_score descending ───────────────────────────────
    scored.sort(key=lambda o: o.composite_score, reverse=True)

    return scored

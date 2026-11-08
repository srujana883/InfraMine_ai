"""
InfraMiner AI - Agent 4: Decision (AHP-TOPSIS)

Deterministic multi-criteria decision agent. No LLM calls.

Consumes Agent 2 (sources, routes) and Agent 3 (cost, environment,
resilience) outputs. Performs AHP for criterion weighting and TOPSIS
for alternative ranking.

AHP:
    - Pairwise comparison matrix for 4 criteria
    - Eigenvector approximation (geometric mean method)
    - Consistency Index (CI) and Consistency Ratio (CR)

TOPSIS:
    - Decision matrix from Agent 3 assessments
    - Vector normalization
    - Weighted normalized matrix
    - Ideal (A+) and negative-ideal (A-) solutions
    - Euclidean distances to ideal/negative-ideal
    - Closeness coefficient and ranking

Criteria:
    1. Cost           (cost criterion - lower is better)
    2. Logistics      (cost criterion - lower distance is better)
    3. Environmental  (cost criterion - lower impact is better)
    4. Resilience     (benefit criterion - higher is better)
"""

from __future__ import annotations

import math
from typing import Any

from src.state import InfraMinerState


# ===================================================================
# AHP - Analytic Hierarchy Process
# ===================================================================

# Random Index table for consistency checking (Saaty 1980)
# RI[n] for n = 1..10 criteria
_RI_TABLE = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90,
    5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41,
    9: 1.45, 10: 1.49,
}

# Criterion definitions
CRITERIA = ["cost", "logistics", "environmental", "resilience"]

# Criterion direction: "cost" = lower is better, "benefit" = higher is better
CRITERION_TYPE = {
    "cost": "cost",
    "logistics": "cost",
    "environmental": "cost",
    "resilience": "benefit",
}

# AHP Pairwise Comparison Matrix (Saaty 1-9 scale)
#
# Rationale for this infrastructure project context:
#   - Cost is slightly more important than logistics (2)
#   - Cost is equally/slightly more important than environmental (2)
#   - Resilience is slightly more important than cost (1/2 reciprocal, so cost=1/2 vs resilience)
#   - Resilience is moderately more important than logistics (3)
#   - Environmental is slightly more important than logistics (2)
#   - Resilience is slightly more important than environmental (2)
#
# Matrix (row vs column):
#                Cost  Logistics  Environmental  Resilience
# Cost            1       2           2            1/2
# Logistics      1/2     1           1/2          1/3
# Environmental  1/2     2           1            1/2
# Resilience     2       3           2            1

DEFAULT_PAIRWISE_MATRIX = [
    [1.0,   2.0,  2.0,  0.5],   # Cost
    [0.5,   1.0,  0.5,  1/3],   # Logistics
    [0.5,   2.0,  1.0,  0.5],   # Environmental
    [2.0,   3.0,  2.0,  1.0],   # Resilience
]


def compute_ahp_weights(
    pairwise_matrix: list[list[float]] | None = None,
) -> dict[str, Any]:
    """Compute AHP criterion weights from a pairwise comparison matrix.

    Uses the geometric mean (row product) method for eigenvector
    approximation, which is standard for 4x4 matrices.

    Returns dict with:
        weights: dict[str, float]
        consistency_index: float
        consistency_ratio: float
        is_consistent: bool
        pairwise_matrix: list[list[float]]
        lambda_max: float
    """
    matrix = pairwise_matrix or DEFAULT_PAIRWISE_MATRIX
    n = len(matrix)

    # 1. Geometric mean of each row
    geo_means: list[float] = []
    for row in matrix:
        product = 1.0
        for val in row:
            product *= val
        geo_means.append(product ** (1.0 / n))

    # 2. Normalize to get weights
    total = sum(geo_means)
    raw_weights = [g / total for g in geo_means]

    # 3. Calculate lambda_max for consistency check
    # Multiply matrix by weight vector, then divide each element by weight
    col_sums = [
        sum(matrix[i][j] for i in range(n))
        for j in range(n)
    ]
    lambda_max = sum(
        col_sums[j] * raw_weights[j]
        for j in range(n)
    )
    # More accurate: Aw / w method
    aw: list[float] = []
    for i in range(n):
        aw_i = sum(matrix[i][j] * raw_weights[j] for j in range(n))
        aw.append(aw_i)
    lambda_max = sum(aw[i] / raw_weights[i] for i in range(n)) / n

    # 4. Consistency Index
    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0

    # 5. Consistency Ratio
    ri = _RI_TABLE.get(n, 1.49)
    cr = ci / ri if ri > 0 else 0.0

    weights = {CRITERIA[i]: round(raw_weights[i], 4) for i in range(n)}

    return {
        "weights": weights,
        "lambda_max": round(lambda_max, 4),
        "consistency_index": round(ci, 4),
        "consistency_ratio": round(cr, 4),
        "is_consistent": cr < 0.10,
        "pairwise_matrix": matrix,
        "criteria": CRITERIA[:],
        "criterion_types": dict(CRITERION_TYPE),
    }


# ===================================================================
# Decision Matrix Construction
# ===================================================================

def build_decision_matrix(
    sources: list[dict],
    routes: list[dict],
    cost_estimates: list[dict],
    environmental_assessments: list[dict],
    resilience_assessments: list[dict],
) -> tuple[list[dict], list[list[float]]]:
    """Build the decision matrix from Agent 2 and Agent 3 outputs.

    Each row = one source alternative.
    Columns = [cost, logistics (distance), environmental, resilience]

    Returns:
        alternatives: list of dicts with source metadata
        matrix: list of [cost, logistics, env, resilience] rows
    """
    # Index Agent 3 outputs by source_id
    cost_by_id = {c["source_id"]: c for c in cost_estimates}
    env_by_id = {e["source_id"]: e for e in environmental_assessments}
    res_by_id = {r["source_id"]: r for r in resilience_assessments}
    route_by_id = {r["source_id"]: r for r in routes}

    # Calculate neutral defaults for partially missing values
    known_costs = [
        c["total_cost"] for c in cost_estimates
        if c.get("total_cost") is not None and c["total_cost"] > 0
    ]
    avg_known_cost = (sum(known_costs) / len(known_costs)) if known_costs else 0.0

    known_dists = [
        r["distance_km"] for r in routes
        if r.get("distance_km") is not None and r["distance_km"] > 0
    ]
    avg_known_dist = (sum(known_dists) / len(known_dists)) if known_dists else 100.0

    alternatives: list[dict] = []
    matrix: list[list[float]] = []
    seen_keys: set[tuple[str, str]] = set()

    for source in sources:
        sid = str(source.get("source_id", "")).strip()
        mat_name = str(source.get("material_name", "unknown")).strip()
        sname = str(source.get("source_name", "")).strip()
        key = (sid, mat_name) if sid else (sname, mat_name)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        cost_est = cost_by_id.get(sid, {})
        env_est = env_by_id.get(sid, {})
        res_est = res_by_id.get(sid, {})
        route = route_by_id.get(sid, {})

        # Extract criteria values (use safe defaults for missing data)
        total_cost = cost_est.get("total_cost")
        distance_km = route.get("distance_km")
        env_score = env_est.get("combined_impact_score")
        resilience = res_est.get("resilience_score")

        # Skip alternatives with all-missing data
        if total_cost is None and distance_km is None:
            alternatives.append({
                "source_id": sid,
                "source_name": source.get("source_name", "unknown"),
                "material_name": source.get("material_name", "unknown"),
                "excluded": True,
                "exclusion_reason": "Insufficient data for decision matrix",
            })
            continue

        # Use neutral defaults for partially missing values
        cost_val = total_cost if total_cost is not None else avg_known_cost
        dist_val = distance_km if distance_km is not None else avg_known_dist
        env_val = env_score if env_score is not None else 0.5
        res_val = resilience if resilience is not None else 0.5

        is_provisional = not (
            total_cost is not None and distance_km is not None and env_score is not None and resilience is not None
        )

        alternatives.append({
            "source_id": sid,
            "source_name": source.get("source_name", "unknown"),
            "material_name": source.get("material_name", "unknown"),
            "source_type": source.get("source_type", "unknown"),
            "excluded": False,
            "raw_cost": cost_val,
            "raw_logistics": dist_val,
            "raw_environmental": env_val,
            "raw_resilience": res_val,
            "cost_available": total_cost is not None,
            "distance_available": distance_km is not None,
            "environmental_available": env_score is not None,
            "resilience_available": resilience is not None,
            "actual_cost": total_cost,
            "actual_distance_km": distance_km,
            "actual_environmental_score": env_score,
            "actual_resilience_score": resilience,
            "cost_status": "documented/calculated" if total_cost is not None else "unavailable (neutral average applied for TOPSIS)",
            "distance_status": "documented" if distance_km is not None else "unavailable (neutral average applied for TOPSIS)",
            "environmental_status": "documented" if env_score is not None else "unavailable (neutral 0.5 applied for TOPSIS)",
            "resilience_status": "calculated" if resilience is not None else "unavailable (neutral 0.5 applied for TOPSIS)",
            "is_provisional": is_provisional,
            "recommendation_status": "provisional_indicative" if is_provisional else "verified_recommendation",
        })
        matrix.append([cost_val, dist_val, env_val, res_val])

    return alternatives, matrix


# ===================================================================
# TOPSIS Implementation
# ===================================================================

def normalize_matrix(matrix: list[list[float]]) -> list[list[float]]:
    """Vector normalization: x_ij / sqrt(sum(x_ij^2)) for each column."""
    if not matrix:
        return []

    n_rows = len(matrix)
    n_cols = len(matrix[0])

    # Column norms
    col_norms = []
    for j in range(n_cols):
        ss = sum(matrix[i][j] ** 2 for i in range(n_rows))
        col_norms.append(math.sqrt(ss) if ss > 0 else 1.0)

    # Normalize
    normalized = []
    for i in range(n_rows):
        row = [matrix[i][j] / col_norms[j] for j in range(n_cols)]
        normalized.append(row)

    return normalized


def apply_weights(
    normalized: list[list[float]], weights: dict[str, float]
) -> list[list[float]]:
    """Multiply normalized matrix by criterion weights."""
    if not normalized:
        return []
    w = [weights.get(c, 0.25) for c in CRITERIA]
    weighted = []
    for row in normalized:
        weighted.append([row[j] * w[j] for j in range(len(row))])
    return weighted


def find_ideal_solutions(
    weighted: list[list[float]],
) -> tuple[list[float], list[float]]:
    """Find ideal (A+) and negative-ideal (A-) solutions.

    For cost criteria (lower is better): A+ = min, A- = max
    For benefit criteria (higher is better): A+ = max, A- = min
    """
    if not weighted:
        return [], []

    n_cols = len(weighted[0])
    ideal: list[float] = []
    neg_ideal: list[float] = []

    for j in range(n_cols):
        col_vals = [weighted[i][j] for i in range(len(weighted))]
        criterion = CRITERIA[j]
        ctype = CRITERION_TYPE[criterion]

        if ctype == "benefit":
            ideal.append(max(col_vals))
            neg_ideal.append(min(col_vals))
        else:  # cost criterion
            ideal.append(min(col_vals))
            neg_ideal.append(max(col_vals))

    return ideal, neg_ideal


def calculate_distances(
    weighted: list[list[float]],
    ideal: list[float],
    neg_ideal: list[float],
) -> tuple[list[float], list[float]]:
    """Calculate Euclidean distances to ideal and negative-ideal."""
    d_plus: list[float] = []
    d_minus: list[float] = []

    for row in weighted:
        dp = math.sqrt(sum((row[j] - ideal[j]) ** 2 for j in range(len(row))))
        dm = math.sqrt(sum((row[j] - neg_ideal[j]) ** 2 for j in range(len(row))))
        d_plus.append(dp)
        d_minus.append(dm)

    return d_plus, d_minus


def calculate_closeness(
    d_plus: list[float], d_minus: list[float]
) -> list[float]:
    """Calculate TOPSIS closeness coefficient: C_i = d_minus / (d_plus + d_minus)."""
    closeness: list[float] = []
    for dp, dm in zip(d_plus, d_minus):
        total = dp + dm
        if total > 0:
            closeness.append(round(dm / total, 4))
        else:
            closeness.append(0.5)  # equal distance = neutral
    return closeness


def rank_alternatives(
    alternatives: list[dict],
    closeness: list[float],
) -> list[dict]:
    """Rank alternatives by closeness coefficient (higher = better)."""
    # Only rank non-excluded alternatives
    ranked_indices = sorted(
        range(len(closeness)),
        key=lambda i: closeness[i],
        reverse=True,
    )

    ranked: list[dict] = []
    for rank, idx in enumerate(ranked_indices, start=1):
        alt = alternatives[idx].copy()
        alt["closeness_coefficient"] = closeness[idx]
        alt["rank"] = rank
        alt["is_viable"] = closeness[idx] >= 0.30
        ranked.append(alt)

    return ranked


def identify_fallbacks(
    ranked: list[dict],
    resilience_assessments: list[dict],
) -> list[dict]:
    """Identify fallback alternatives from the ranking.

    The primary recommendation is rank 1.
    Fallbacks are alternatives with:
      - rank >= 2
      - genuinely distinct physical source
      - viability evaluation
    """
    if not ranked:
        return []

    res_by_id = {r["source_id"]: r for r in resilience_assessments}
    primary = ranked[0] if ranked else None
    primary_material = primary.get("material_name", "") if primary else ""
    primary_sid = primary.get("source_id") if primary else None

    fallbacks: list[dict] = []
    seen_fb_sids: set[str] = set()
    if primary_sid:
        seen_fb_sids.add(primary_sid)

    for alt in ranked[1:]:
        sid = alt.get("source_id")
        if sid and sid in seen_fb_sids:
            continue
        if sid:
            seen_fb_sids.add(sid)

        res = res_by_id.get(sid, {})
        c_score = alt.get("closeness_coefficient", 0.0)

        # Feasibility reasoning
        reasons: list[str] = []
        if c_score >= 0.3:
            reasons.append("Viable TOPSIS score")
        if res.get("resilience_score", 0) >= 0.5:
            reasons.append("Adequate resilience")
        if alt.get("material_name") == primary_material:
            reasons.append("Same material as primary - direct substitute")

        fb = {
            "source_id": sid,
            "source_name": alt.get("source_name"),
            "material_name": alt.get("material_name"),
            "rank": alt.get("rank"),
            "closeness_coefficient": c_score,
            "resilience_score": res.get("resilience_score"),
            "alternative_count": res.get("alternative_count", 0),
            "fallback_feasible": res.get("fallback_feasible", False),
            "feasibility_reasons": reasons,
            "is_viable_fallback": len(reasons) >= 2,
        }
        fallbacks.append(fb)

    return fallbacks


def build_final_sourcing_plan(
    ranked: list[dict],
    resilience_assessments: list[dict],
) -> list[dict]:
    """Construct material-specific final sourcing plans with primary and fallback sources.

    Groups ranked alternatives by material, assigning the top-ranked viable alternative
    as the primary source and subsequent viable alternatives as fallbacks.
    If no alternative meets the viability threshold (closeness_coefficient >= 0.3),
    reports 'No viable source identified'.
    """
    if not ranked:
        return []

    res_by_id = {r["source_id"]: r for r in resilience_assessments}

    by_material: dict[str, list[dict]] = {}
    for alt in ranked:
        mat = alt.get("material_name", "Unknown")
        by_material.setdefault(mat, []).append(alt)

    plan: list[dict] = []
    for mat, alts in by_material.items():
        # Deduplicate alternatives by physical source_id within this material
        seen_sids: set[str] = set()
        unique_alts: list[dict] = []
        for alt in alts:
            sid = alt.get("source_id")
            if sid not in seen_sids:
                seen_sids.add(sid)
                unique_alts.append(alt)

        # Viable alternatives have closeness_coefficient >= 0.30
        viable_alts = [a for a in unique_alts if a.get("closeness_coefficient", 0.0) >= 0.30]
        non_viable_alts = [a for a in unique_alts if a.get("closeness_coefficient", 0.0) < 0.30]

        if not viable_alts:
            # All available sources for this material are non-viable
            sample_non_viable = unique_alts[0] if unique_alts else {}
            explanation = (
                f"No viable source identified for {mat}. Candidate source '{sample_non_viable.get('source_name', 'Unknown')}' "
                f"(TOPSIS closeness coefficient: {sample_non_viable.get('closeness_coefficient', 0.0):.4f}) failed multi-criteria viability threshold (< 0.30). "
                f"Sourcing requires identifying additional alternative sources or re-evaluating project logistics and cost constraints."
            )
            plan.append({
                "material_name": mat,
                "recommendation_status": "no_viable_source",
                "is_provisional": True,
                "has_viable_source": False,
                "primary_source": {
                    "source_id": sample_non_viable.get("source_id", "none"),
                    "source_name": "No viable source identified",
                    "source_type": sample_non_viable.get("source_type"),
                    "closeness_coefficient": sample_non_viable.get("closeness_coefficient", 0.0),
                    "resilience_score": None,
                    "is_viable": False,
                },
                "fallback_sources": [],
                "fallback_feasible": False,
                "sourcing_strategy": explanation,
                "non_viable_candidates": [
                    {
                        "source_id": a.get("source_id"),
                        "source_name": a.get("source_name"),
                        "closeness_coefficient": a.get("closeness_coefficient"),
                        "rejection_reason": f"TOPSIS score {a.get('closeness_coefficient', 0.0):.4f} is below viability threshold (0.30)",
                    }
                    for a in non_viable_alts
                ],
            })
            continue

        # At least one viable alternative exists
        primary = viable_alts[0]
        primary_res = res_by_id.get(primary["source_id"], {})

        fallback_entries: list[dict] = []
        for fb in viable_alts[1:]:
            fb_res = res_by_id.get(fb["source_id"], {})
            fallback_entries.append({
                "source_id": fb["source_id"],
                "source_name": fb["source_name"],
                "rank_overall": fb["rank"],
                "closeness_coefficient": fb["closeness_coefficient"],
                "resilience_score": fb_res.get("resilience_score"),
                "is_viable": True,
                "feasibility_notes": (
                    f"Direct substitute with resilience score {fb_res.get('resilience_score', 'N/A')}. "
                    f"Provides supply redundancy if primary source experiences disruption."
                ),
            })

        has_viable_fb = len(fallback_entries) > 0
        is_provisional = primary.get("is_provisional", False)
        plan_status = "provisional_indicative" if is_provisional else "verified_recommendation"

        explanation = (
            f"Primary source '{primary['source_name']}' recommended for {mat} based on "
            f"TOPSIS closeness coefficient {primary['closeness_coefficient']:.4f} and "
            f"resilience score {primary_res.get('resilience_score', 'N/A')}. "
        )
        if is_provisional:
            explanation += (
                "[NOTICE: Sourcing evaluation is PROVISIONAL / INDICATIVE. Some criteria "
                "such as numerical environmental scores or commercial unit prices are not published "
                "in project documents; neutral mathematical assumptions were used for TOPSIS calculation. "
                "Field verification and formal bidding are required before contract commitment.] "
            )
        if fallback_entries:
            explanation += (
                f"{len(fallback_entries)} fallback alternative(s) identified. "
                f"Top fallback '{fallback_entries[0]['source_name']}' ensures operational continuity."
            )
        else:
            explanation += (
                "Single-source dependency warning: No alternative viable source identified. "
                "Recommend qualifying additional suppliers to reduce supply risk."
            )

        plan.append({
            "material_name": mat,
            "recommendation_status": plan_status,
            "is_provisional": is_provisional,
            "has_viable_source": True,
            "primary_source": {
                "source_id": primary["source_id"],
                "source_name": primary["source_name"],
                "source_type": primary.get("source_type"),
                "closeness_coefficient": primary["closeness_coefficient"],
                "resilience_score": primary_res.get("resilience_score"),
                "raw_cost": primary.get("raw_cost"),
                "raw_logistics_distance_km": primary.get("raw_logistics"),
                "raw_environmental_impact": primary.get("raw_environmental"),
                "cost_status": primary.get("cost_status"),
                "environmental_status": primary.get("environmental_status"),
                "resilience_status": primary.get("resilience_status"),
                "is_viable": True,
            },
            "fallback_sources": fallback_entries,
            "fallback_feasible": has_viable_fb,
            "sourcing_strategy": explanation,
        })

    return plan


def generate_resilience_explanation(
    primary: dict | None,
    fallbacks: list[dict],
    sourcing_plan: list[dict],
    ahp_weights: dict[str, float],
) -> str:
    """Generate comprehensive narrative on resilience considerations and fallback viability."""
    lines = []
    res_wt = ahp_weights.get("resilience", 0.0) * 100
    lines.append(
        f"Resilience is weighted at {res_wt:.1f}% in the multi-criteria decision framework, "
        "reflecting the critical need for supply continuity in large-scale infrastructure projects."
    )
    if primary and primary.get("source_name") != "No viable source identified":
        lines.append(
            f"Primary selection '{primary['source_name']}' ({primary.get('material_name')}) "
            f"achieves the highest overall TOPSIS score ({primary['closeness_coefficient']:.4f}), "
            "optimizing the trade-off across cost, logistics, environmental footprint, and resilience."
        )
    plan_fb_names = []
    seen_fbs = set()
    for sp in sourcing_plan:
        for fb in sp.get("fallback_sources", []):
            name = fb.get("source_name")
            sid = fb.get("source_id") or name
            if sid and sid not in seen_fbs:
                seen_fbs.add(sid)
                if name:
                    plan_fb_names.append(f"'{name}'")

    if not plan_fb_names and fallbacks:
        for f in fallbacks:
            if f.get("is_viable_fallback"):
                name = f.get("source_name")
                sid = f.get("source_id") or name
                if sid and sid not in seen_fbs:
                    seen_fbs.add(sid)
                    if name:
                        plan_fb_names.append(f"'{name}'")

    if plan_fb_names:
        names = ", ".join(plan_fb_names[:3])
        lines.append(
            f"{len(plan_fb_names)} viable fallback alternative(s) were identified across materials ({names}). "
            "These alternatives provide critical operational buffering against supply chain disruptions, "
            "such as seasonal monsoon closures, transport corridor failures, or capacity constraints."
        )
    for p in sourcing_plan:
        if not p.get("fallback_feasible"):
            if not p.get("has_viable_source", True):
                lines.append(
                    f"Notice: Material '{p['material_name']}' has no viable source identified under multi-criteria threshold. Dedicated procurement action required."
                )
            else:
                lines.append(
                    f"Notice: Material '{p['material_name']}' exhibits single-source dependency. "
                    "A proactive risk mitigation strategy is recommended."
                )
    return " ".join(lines)


# ===================================================================
# Full TOPSIS Pipeline
# ===================================================================

def run_topsis(
    alternatives: list[dict],
    matrix: list[list[float]],
    weights: dict[str, float],
) -> dict[str, Any]:
    """Execute the complete TOPSIS procedure.

    Returns dict with all intermediate and final results.
    """
    if not matrix or len(matrix) < 2:
        # Need at least 2 alternatives for TOPSIS
        if len(matrix) == 1:
            return {
                "ranked_alternatives": [{
                    **alternatives[0],
                    "closeness_coefficient": 1.0,
                    "rank": 1,
                }],
                "normalized_matrix": [matrix[0]],
                "weighted_matrix": [matrix[0]],
                "ideal_solution": matrix[0],
                "negative_ideal_solution": matrix[0],
                "d_plus": [0.0],
                "d_minus": [0.0],
                "closeness_coefficients": [1.0],
                "note": "Single alternative - no comparison possible",
            }
        return {
            "ranked_alternatives": [],
            "error": "No alternatives available for TOPSIS",
        }

    # Active (non-excluded) alternatives and their matrix rows
    active_alts = [a for a in alternatives if not a.get("excluded")]

    # 1. Normalize
    normalized = normalize_matrix(matrix)

    # 2. Apply weights
    weighted = apply_weights(normalized, weights)

    # 3. Ideal solutions
    ideal, neg_ideal = find_ideal_solutions(weighted)

    # 4. Distances
    d_plus, d_minus = calculate_distances(weighted, ideal, neg_ideal)

    # 5. Closeness coefficients
    closeness = calculate_closeness(d_plus, d_minus)

    # 6. Ranking
    ranked = rank_alternatives(active_alts, closeness)

    return {
        "ranked_alternatives": ranked,
        "normalized_matrix": normalized,
        "weighted_matrix": weighted,
        "ideal_solution": [round(v, 6) for v in ideal],
        "negative_ideal_solution": [round(v, 6) for v in neg_ideal],
        "d_plus": [round(v, 6) for v in d_plus],
        "d_minus": [round(v, 6) for v in d_minus],
        "closeness_coefficients": closeness,
    }


# ===================================================================
# LangGraph Node - Agent 4: Decision
# ===================================================================

def run_decision(state: InfraMinerState) -> dict:
    """LangGraph node for Agent 4 (Decision / AHP-TOPSIS).

    Consumes:
        - sources, routes (Agent 2)
        - cost_estimates, environmental_assessments,
          resilience_assessments (Agent 3)

    Produces:
        - decision_results (single dict with full AHP-TOPSIS output)
        - messages, current_agent, completed_agents
    """

    sources = state.get("sources", [])
    routes = state.get("routes", [])
    cost_estimates = state.get("cost_estimates", [])
    env_assessments = state.get("environmental_assessments", [])
    res_assessments = state.get("resilience_assessments", [])

    if not sources:
        return {
            "errors": ["Agent 4: No sources in state. Ensure Agent 2 completed."],
            "current_agent": "decision",
        }

    if not cost_estimates and not res_assessments:
        return {
            "errors": ["Agent 4: No assessments in state. Ensure Agent 3 completed."],
            "current_agent": "decision",
        }

    # 1. AHP weights
    ahp_result = compute_ahp_weights()

    # 2. Build decision matrix
    alternatives, matrix = build_decision_matrix(
        sources, routes, cost_estimates, env_assessments, res_assessments
    )

    active_alts = [a for a in alternatives if not a.get("excluded")]
    excluded_alts = [a for a in alternatives if a.get("excluded")]

    if not active_alts:
        return {
            "errors": [
                "Agent 4: No alternatives with sufficient data for ranking."
            ],
            "current_agent": "decision",
        }

    # 3. TOPSIS
    topsis_result = run_topsis(active_alts, matrix, ahp_result["weights"])

    # 4. Identify fallbacks
    ranked = topsis_result.get("ranked_alternatives", [])
    fallbacks = identify_fallbacks(ranked, res_assessments)

    # 5. Primary recommendation
    primary = ranked[0] if ranked else None

    # 6. Final sourcing plan per material
    final_sourcing_plan = build_final_sourcing_plan(ranked, res_assessments)

    # 7. Comprehensive resilience explanation
    resilience_explanation = generate_resilience_explanation(
        primary, fallbacks, final_sourcing_plan, ahp_result["weights"]
    )

    # 8. Build decision_results dict
    decision_results: dict[str, Any] = {
        "methodology": "AHP-TOPSIS",
        "ahp": {
            "pairwise_matrix": ahp_result["pairwise_matrix"],
            "criteria": ahp_result["criteria"],
            "criterion_types": ahp_result["criterion_types"],
            "weights": ahp_result["weights"],
            "lambda_max": ahp_result["lambda_max"],
            "consistency_index": ahp_result["consistency_index"],
            "consistency_ratio": ahp_result["consistency_ratio"],
            "is_consistent": ahp_result["is_consistent"],
        },
        "topsis": {
            "decision_matrix_size": f"{len(matrix)} alternatives x {len(CRITERIA)} criteria",
            "normalized_matrix": topsis_result.get("normalized_matrix"),
            "weighted_matrix": topsis_result.get("weighted_matrix"),
            "ideal_solution": topsis_result.get("ideal_solution"),
            "negative_ideal_solution": topsis_result.get("negative_ideal_solution"),
            "d_plus": topsis_result.get("d_plus"),
            "d_minus": topsis_result.get("d_minus"),
            "closeness_coefficients": topsis_result.get("closeness_coefficients"),
        },
        "ranking": ranked,
        "primary_recommendation": primary,
        "fallback_alternatives": fallbacks,
        "final_sourcing_plan": final_sourcing_plan,
        "resilience_explanation": resilience_explanation,
        "excluded_alternatives": excluded_alts,
        "total_alternatives_evaluated": len(active_alts),
        "total_alternatives_excluded": len(excluded_alts),
        "data_type": "calculated",
        "data_provenance": (
            "Decision computed deterministically using AHP-TOPSIS. "
            "Input data includes demonstration/assumption values from "
            "upstream agents. Results are indicative, not verified."
        ),
    }

    messages_list = [
        f"Agent 4: Evaluated {len(active_alts)} alternative(s) "
        f"using AHP-TOPSIS with {len(CRITERIA)} criteria.",
    ]
    if primary:
        messages_list.append(
            f"Agent 4: Primary recommendation is "
            f"{primary['source_name']} (closeness={primary['closeness_coefficient']})."
        )
    if fallbacks:
        viable = [f for f in fallbacks if f.get("is_viable_fallback")]
        messages_list.append(
            f"Agent 4: Identified {len(viable)} viable fallback(s) "
            f"out of {len(fallbacks)} alternative(s)."
        )

    return {
        "decision_results": decision_results,
        "messages": messages_list,
        "current_agent": "decision",
        "completed_agents": ["decision"],
    }


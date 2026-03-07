"""Customer lens profiles and lightweight post-fusion interpretation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LensConfig:
    id: str
    label: str
    description: str
    signal_multipliers: dict[str, float]
    customer_tag: str
    impact_focus: str
    action_focus: str
    watchlist_focus: str
    recommended_actions: dict[str, str]


LENS_PROFILES: dict[str, LensConfig] = {
    "general": LensConfig(
        id="general",
        label="General",
        description="Balanced interpretation for broad hazard triage.",
        signal_multipliers={},
        customer_tag="General Brief",
        impact_focus="Assess overall hazard posture across the AOI.",
        action_focus="Use this as a general decision-support brief.",
        watchlist_focus="Rank watchlist members by overall risk.",
        recommended_actions={
            "critical": "Escalate immediately and align stakeholders on the highest-impact hazard drivers.",
            "high": "Prepare rapid operational decisions and verify with the strongest corroborating sources.",
            "medium": "Monitor closely and rescan on a tighter cadence before escalating.",
            "low": "Keep on watch and use trend movement to decide whether to escalate later.",
            "none": "No customer escalation required yet; maintain monitoring coverage.",
        },
    ),
    "logistics": LensConfig(
        id="logistics",
        label="Logistics",
        description="Emphasizes supply chain continuity, route access, and corridor disruption.",
        signal_multipliers={
            "sentinel_change": 1.10,
            "gdacs": 1.15,
            "usgs_seismic": 1.20,
            "geo_conflict": 1.10,
        },
        customer_tag="Logistics Exposure",
        impact_focus="Focus on route continuity, chokepoints, port access, and supplier timing risk.",
        action_focus="Translate the result into route, shipment, or supplier continuity decisions.",
        watchlist_focus="Prioritize assets that could disrupt throughput or route reliability.",
        recommended_actions={
            "critical": "Re-route immediately, validate alternate corridors, and alert operations owners now.",
            "high": "Prepare route contingency plans and confirm carrier or supplier exposure.",
            "medium": "Review corridor resilience and stage fallback routing if conditions worsen.",
            "low": "Keep monitoring key nodes and scan again before changing the plan.",
            "none": "No logistics intervention needed yet; retain for route watchkeeping.",
        },
    ),
    "energy": LensConfig(
        id="energy",
        label="Energy",
        description="Emphasizes facility continuity, corridor exposure, and operational resilience.",
        signal_multipliers={
            "sentinel_change": 1.20,
            "gdacs": 1.05,
            "usgs_seismic": 1.10,
            "geo_conflict": 1.20,
        },
        customer_tag="Energy Continuity",
        impact_focus="Focus on facility access, corridor security, and continuity of operations.",
        action_focus="Translate the result into facility resilience and corridor exposure decisions.",
        watchlist_focus="Prioritize sites with continuity, shutdown, or access exposure.",
        recommended_actions={
            "critical": "Escalate to site operators immediately and prepare continuity or shutdown decisions.",
            "high": "Review continuity plans and confirm site access, staffing, and corridor exposure.",
            "medium": "Stage mitigation steps for facilities and dependent corridors if risk persists.",
            "low": "Continue monitoring site conditions and reassess on the next scan cycle.",
            "none": "No immediate energy continuity action required; remain on routine watch.",
        },
    ),
    "insurance": LensConfig(
        id="insurance",
        label="Insurance",
        description="Emphasizes severity, accumulation risk, and insured asset exposure.",
        signal_multipliers={
            "sentinel_change": 1.15,
            "gdacs": 1.20,
            "usgs_seismic": 1.25,
            "geo_conflict": 1.05,
        },
        customer_tag="Insurance Exposure",
        impact_focus="Focus on severity, accumulation potential, and insured asset concentration.",
        action_focus="Translate the result into exposure review and severity monitoring decisions.",
        watchlist_focus="Prioritize locations with the sharpest severity and accumulation movement.",
        recommended_actions={
            "critical": "Escalate to exposure and claims teams immediately and review insured concentration.",
            "high": "Prepare severity assumptions and validate whether exposure accumulation is increasing.",
            "medium": "Track claim-driving indicators and rescan before updating reserve assumptions.",
            "low": "Monitor severity direction and keep the location on the exposure watchlist.",
            "none": "No insurance escalation needed yet; retain as low-severity background monitoring.",
        },
    ),
    "humanitarian": LensConfig(
        id="humanitarian",
        label="Humanitarian",
        description="Emphasizes access constraints, responder safety, and affected-population urgency.",
        signal_multipliers={
            "sentinel_change": 1.05,
            "gdacs": 1.20,
            "usgs_seismic": 1.15,
            "geo_conflict": 1.25,
        },
        customer_tag="Humanitarian Access",
        impact_focus="Focus on responder access, population support urgency, and access constraints.",
        action_focus="Translate the result into access, responder posture, and support prioritization.",
        watchlist_focus="Prioritize locations where access and support urgency are moving fastest.",
        recommended_actions={
            "critical": "Escalate for response planning now and review responder access constraints immediately.",
            "high": "Prepare access and safety planning with local corroboration before deployment.",
            "medium": "Monitor for worsening access constraints and pre-position support if justified.",
            "low": "Maintain watchkeeping and validate whether access conditions are changing materially.",
            "none": "No immediate humanitarian response trigger; continue monitoring the area.",
        },
    ),
    "security": LensConfig(
        id="security",
        label="Security / Defense",
        description="Emphasizes escalation, personnel safety, and operational posture.",
        signal_multipliers={
            "sentinel_change": 1.05,
            "gdacs": 0.95,
            "usgs_seismic": 0.90,
            "geo_conflict": 1.35,
        },
        customer_tag="Security Posture",
        impact_focus="Focus on personnel safety, escalation posture, and facility security exposure.",
        action_focus="Translate the result into posture, protective measures, and escalation readiness.",
        watchlist_focus="Prioritize locations with the strongest escalation and personnel risk pattern.",
        recommended_actions={
            "critical": "Escalate to security leadership immediately and initiate protective posture changes now.",
            "high": "Prepare protective measures and confirm personnel exposure and site posture.",
            "medium": "Tighten watchkeeping and validate whether escalation signals are corroborating further.",
            "low": "Maintain security monitoring and keep the site on the escalation watchlist.",
            "none": "No security escalation required yet; continue intelligence monitoring.",
        },
    ),
}


def resolve_lens(lens_id: str | None) -> LensConfig:
    normalized = str(lens_id or "general").strip().lower()
    return LENS_PROFILES.get(normalized, LENS_PROFILES["general"])


def available_lenses() -> list[dict[str, str]]:
    return [
        {
            "id": config.id,
            "label": config.label,
            "description": config.description,
        }
        for config in LENS_PROFILES.values()
    ]


def score_signals_for_lens(
    signals: list[dict[str, Any]],
    lens: LensConfig,
    fallback_score: float | None,
) -> tuple[float | None, list[dict[str, Any]], dict[str, Any] | None]:
    total_weight = 0.0
    weighted_sum = 0.0
    scored_signals: list[dict[str, Any]] = []
    dominant_signal: dict[str, Any] | None = None
    dominant_value = -1.0

    for signal in signals:
        if not isinstance(signal, dict):
            continue
        score_raw = signal.get("score")
        try:
            score = float(score_raw) if score_raw is not None else 0.0
        except (TypeError, ValueError):
            score = 0.0
        try:
            effective_weight = float(signal.get("effective_weight") or 0.0)
        except (TypeError, ValueError):
            effective_weight = 0.0
        multiplier = float(lens.signal_multipliers.get(str(signal.get("key", "")), 1.0))
        lens_effective_weight = effective_weight * multiplier
        total_weight += lens_effective_weight
        weighted_sum += score * lens_effective_weight
        contribution = score * lens_effective_weight
        scored = {
            "key": signal.get("key"),
            "multiplier": round(multiplier, 4),
            "lens_effective_weight": round(lens_effective_weight, 4),
            "lens_contribution": round(contribution, 4),
        }
        scored_signals.append(scored)
        if contribution > dominant_value:
            dominant_value = contribution
            dominant_signal = signal

    if total_weight <= 0:
        return fallback_score, scored_signals, dominant_signal
    return round(weighted_sum / total_weight, 4), scored_signals, dominant_signal


def lens_recommended_action(lens: LensConfig, threat_level: str) -> str:
    return lens.recommended_actions.get(
        threat_level,
        lens.recommended_actions["none"],
    )

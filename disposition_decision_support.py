#!/usr/bin/env python3
"""
PSI/PORT Disposition Decision Support
Integrates PSI score with bed management logic for optimal patient placement:
floor vs. observation vs. ICU, with safety-net follow-up plans.

Author: Dr. Abu Suraih Sakhri | License: MIT
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class DispositionLevel(Enum):
    HOME = "home"
    OBSERVATION = "observation"
    FLOOR = "floor"
    STEP_DOWN = "step_down"
    ICU = "icu"


@dataclass
class BedAvailability:
    """Current bed availability for disposition planning."""
    icu_beds_available: int = 5
    step_down_beds_available: int = 10
    floor_beds_available: int = 50
    observation_beds_available: int = 15


@dataclass
class DispositionDecision:
    """Structured disposition decision output."""
    patient_id: str
    psi_risk_class: str
    psi_score: int
    recommended_level: str
    alternative_level: Optional[str]
    rationale: List[str]
    safety_net_plan: Dict[str, Any]
    follow_up_schedule: List[str]
    escalation_criteria: List[str]
    bed_urgency: str  # "routine", "urgent", "emergent"


class DispositionDecisionEngine:
    """
    Maps PSI/PORT risk classes to optimal disposition with bed management
    integration, safety-net planning, and escalation criteria.
    """

    DISPOSITION_MAP = {
        "I": {
            "level": DispositionLevel.HOME,
            "alternative": None,
            "bed_urgency": "routine",
            "rationale": [
                "PSI Risk Class I: very low mortality risk (0.1%)",
                "No adverse clinical features requiring hospitalization",
                "Outpatient management is standard of care",
            ],
            "safety_net": {
                "return_precautions": [
                    "Worsening shortness of breath",
                    "Unable to tolerate oral medications/fluids",
                    "Persistent fever > 48 hours on antibiotics",
                    "New confusion or altered mental status",
                    "Chest pain or hemoptysis",
                ],
                "contact_instructions": "Return to ED or call primary care within 24 hours if symptoms worsen",
            },
            "follow_up": [
                "Primary care visit within 48-72 hours",
                "Phone check-in at 24 hours",
                "Repeat chest X-ray in 6-8 weeks if symptoms persist",
            ],
            "escalation": [
                "Persistent fever > 72 hours despite antibiotics",
                "Respiratory rate increase > 5 from baseline",
                "New oxygen requirement",
            ],
        },
        "II": {
            "level": DispositionLevel.HOME,
            "alternative": DispositionLevel.OBSERVATION,
            "bed_urgency": "routine",
            "rationale": [
                "PSI Risk Class II: low mortality risk (0.6%)",
                "Safe for outpatient management with close follow-up",
                "Consider observation if social factors limit outpatient safety",
            ],
            "safety_net": {
                "return_precautions": [
                    "Increasing dyspnea or respiratory distress",
                    "Hemodynamic instability (lightheadedness, syncope)",
                    "Inability to take oral medications",
                    "Worsening mental status",
                ],
                "contact_instructions": "Return to ED within 12-24 hours if symptoms worsen",
            },
            "follow_up": [
                "Primary care or urgent care visit within 48 hours",
                "Phone follow-up at 24 and 48 hours",
                "Repeat chest X-ray in 6-8 weeks",
            ],
            "escalation": [
                "Temperature > 38.5°C at 48-hour follow-up",
                "Respiratory rate > 24 at rest",
                "Oxygen saturation < 92% on room air",
            ],
        },
        "III": {
            "level": DispositionLevel.OBSERVATION,
            "alternative": DispositionLevel.FLOOR,
            "bed_urgency": "routine",
            "rationale": [
                "PSI Risk Class III: moderate mortality risk (2.8%)",
                "Observation unit stay for 23-hour monitoring and IV antibiotics",
                "May discharge if clinically stable after observation period",
            ],
            "safety_net": {
                "return_precautions": [
                    "Clinical deterioration during observation",
                    "Failure to meet clinical stability criteria at 24h",
                    "New organ dysfunction",
                ],
                "observation_criteria": [
                    "Afebrile for > 24 hours",
                    "Heart rate < 100 bpm",
                    "Respiratory rate < 24",
                    "Systolic BP > 90 mmHg",
                    "O2 saturation > 90% on room air",
                    "Able to tolerate oral intake",
                ],
            },
            "follow_up": [
                "Reassess at 12 and 24 hours in observation",
                "Primary care visit within 48 hours of discharge",
                "Phone follow-up at 48 hours post-discharge",
            ],
            "escalation": [
                "Failure to meet stability criteria at 24 hours",
                "Transfer to floor if clinical worsening",
                "ICU transfer if respiratory failure or sepsis develops",
            ],
        },
        "IV": {
            "level": DispositionLevel.FLOOR,
            "alternative": DispositionLevel.STEP_DOWN,
            "bed_urgency": "urgent",
            "rationale": [
                "PSI Risk Class IV: high mortality risk (8.2%)",
                "Inpatient hospitalization required",
                "Consider step-down unit if borderline hemodynamic or respiratory status",
            ],
            "safety_net": {
                "monitoring_frequency": "Vital signs every 4 hours",
                "nursing_assessments": [
                    "Respiratory status q4h",
                    "Mental status checks q shift",
                    "Fluid balance monitoring",
                    "Oxygen saturation continuous",
                ],
            },
            "follow_up": [
                "Daily physician reassessment",
                "IV-to-PO conversion evaluation when clinically stable",
                "Procalcitonin at day 3 for duration guidance",
                "Discharge planning begins at admission",
            ],
            "escalation": [
                "ICU transfer if: respiratory failure requiring > 6L NC, sepsis, altered mental status",
                "Step-down transfer if: borderline stability, requiring close monitoring",
                "Rapid response if: acute deterioration in vital signs",
            ],
        },
        "V": {
            "level": DispositionLevel.ICU,
            "alternative": DispositionLevel.STEP_DOWN,
            "bed_urgency": "emergent",
            "rationale": [
                "PSI Risk Class V: very high mortality risk (29.2%)",
                "ICU admission recommended for intensive monitoring and treatment",
                "Sepsis protocol activation if applicable",
            ],
            "safety_net": {
                "monitoring_frequency": "Continuous monitoring with hourly assessments",
                "critical_care_protocols": [
                    "Sepsis bundle compliance",
                    "ARDS lung-protective ventilation if needed",
                    "Hemodynamic support as indicated",
                    "Early mobilization when stable",
                ],
            },
            "follow_up": [
                "ICU attending reassessment q12h minimum",
                "Multidisciplinary rounds daily",
                "Goals-of-care discussion within 48 hours",
                "Step-down criteria evaluation daily",
            ],
            "escalation": [
                "ECMO evaluation if refractory ARDS",
                "Palliative care consultation if poor prognosis",
                "Infectious disease consultation for complex cases",
            ],
        },
    }

    def __init__(self, bed_availability: Optional[BedAvailability] = None):
        self.beds = bed_availability or BedAvailability()

    def make_decision(
        self,
        patient_id: str,
        psi_risk_class: str,
        psi_score: int,
        social_factors: Optional[Dict[str, Any]] = None,
    ) -> DispositionDecision:
        """Generate a disposition decision with safety-net planning."""
        psi_risk_class = str(psi_risk_class).upper()
        if psi_risk_class not in self.DISPOSITION_MAP:
            psi_risk_class = "III"

        config = self.DISPOSITION_MAP[psi_risk_class]
        social_factors = social_factors or {}

        # Social factor adjustments
        rationale = list(config["rationale"])
        level = config["level"]
        alternative = config["alternative"]

        if social_factors.get("lives_alone") and psi_risk_class in ("I", "II"):
            rationale.append("Patient lives alone — consider observation for safety monitoring")
            if alternative is None:
                alternative = DispositionLevel.OBSERVATION

        if social_factors.get("no_transportation") and psi_risk_class in ("I", "II"):
            rationale.append("Limited transportation — lower threshold for observation admission")

        if social_factors.get("inadequate_follow_up") and psi_risk_class in ("I", "II", "III"):
            rationale.append("Inadequate outpatient follow-up access — favor inpatient/observation")

        # Bed availability check
        bed_map = {
            DispositionLevel.ICU: self.beds.icu_beds_available,
            DispositionLevel.STEP_DOWN: self.beds.step_down_beds_available,
            DispositionLevel.FLOOR: self.beds.floor_beds_available,
            DispositionLevel.OBSERVATION: self.beds.observation_beds_available,
        }

        if bed_map.get(level, 999) <= 0:
            rationale.append(f"⚠ {level.value} beds unavailable — using alternative disposition")
            if alternative and bed_map.get(alternative, 0) > 0:
                level = alternative
            else:
                rationale.append("All preferred beds at capacity — escalation to bed management")

        return DispositionDecision(
            patient_id=patient_id,
            psi_risk_class=psi_risk_class,
            psi_score=psi_score,
            recommended_level=level.value,
            alternative_level=alternative.value if alternative else None,
            rationale=rationale,
            safety_net_plan=config["safety_net"],
            follow_up_schedule=config["follow_up"],
            escalation_criteria=config["escalation"],
            bed_urgency=config["bed_urgency"],
        )

    def format_decision_report(self, decision: DispositionDecision) -> str:
        """Generate a formatted disposition report."""
        lines = [
            "=" * 60,
            "DISPOSITION DECISION SUPPORT",
            "=" * 60,
            f"Patient: {decision.patient_id}",
            f"PSI Score: {decision.psi_score} (Risk Class {decision.psi_risk_class})",
            f"Recommended Disposition: {decision.recommended_level.upper()}",
            f"Bed Urgency: {decision.bed_urgency.upper()}",
        ]
        if decision.alternative_level:
            lines.append(f"Alternative: {decision.alternative_level.upper()}")

        lines.append("")
        lines.append("Rationale:")
        for r in decision.rationale:
            lines.append(f"  • {r}")

        lines.append("")
        lines.append("Follow-Up Schedule:")
        for f in decision.follow_up_schedule:
            lines.append(f"  • {f}")

        lines.append("")
        lines.append("Escalation Criteria:")
        for e in decision.escalation_criteria:
            lines.append(f"  ⚠ {e}")

        if "return_precautions" in decision.safety_net_plan:
            lines.append("")
            lines.append("Return Precautions:")
            for rp in decision.safety_net_plan["return_precautions"]:
                lines.append(f"  → {rp}")

        lines.append("=" * 60)
        return "\n".join(lines)


def main():
    """CLI demo."""
    engine = DispositionDecisionEngine()
    for cls, score in [("I", 0), ("II", 55), ("III", 85), ("IV", 115), ("V", 160)]:
        decision = engine.make_decision(f"PT-{cls}", cls, score)
        print(engine.format_decision_report(decision))
        print()


if __name__ == "__main__":
    main()

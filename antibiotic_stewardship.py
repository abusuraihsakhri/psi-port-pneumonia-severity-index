#!/usr/bin/env python3
"""
PSI/PORT Antibiotic Stewardship Linkage
Illustrative antibiotic stewardship pathways for adult CAP.
PSI is prognostic; antibiotic selection depends on severity, setting, allergies,
microbiology, local guidance and individual contraindications.

Author: Dr. Abu Suraih Sakhri | License: MIT
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ResistancePattern:
    """Local antibiogram resistance data for empiric therapy guidance."""
    organism: str
    agent: str
    resistance_rate_pct: float  # 0-100
    sample_size: int
    year: int


@dataclass
class AntibioticRecommendation:
    """Structured antibiotic recommendation output."""
    psi_risk_class: str
    setting: str
    primary_regimen: str
    alternative_regimen: str
    duration_days: int
    monitoring: List[str]
    de_escalation_notes: str
    local_resistance_alerts: List[str]


class AntibioticStewardshipEngine:
    """
    Educational treatment-pathway examples only. PSI is not an antibiotic
    prescribing rule; clinical review is necessary before any treatment.
    """

    # IDSA/ATS 2019 CAP guidelines mapped to PSI risk classes
    GUIDELINE_REGIMENS = {
        "I": {
            "setting": "Outpatient",
            "no_comorbidities": {
                "primary": "Amoxicillin 1g TID × 5-7 days",
                "alternative": "Doxycycline 100mg BID × 5-7 days",
                "notes": "Macrolide only if local resistance < 25%",
            },
            "with_comorbidities": {
                "primary": "Amoxicillin-clavulanate 875/125mg BID + macrolide or doxycycline",
                "alternative": "Respiratory fluoroquinolone (levofloxacin 750mg daily × 5 days)",
                "notes": "Combination therapy preferred for comorbid patients",
            },
        },
        "II": {
            "setting": "Outpatient",
            "no_comorbidities": {
                "primary": "Amoxicillin 1g TID × 5-7 days",
                "alternative": "Doxycycline 100mg BID × 5-7 days",
                "notes": "Consider respiratory fluoroquinolone if macrolide resistance > 25%",
            },
            "with_comorbidities": {
                "primary": "Amoxicillin-clavulanate 875/125mg BID + macrolide",
                "alternative": "Respiratory fluoroquinolone monotherapy",
                "notes": "Close outpatient follow-up within 48-72 hours",
            },
        },
        "III": {
            "setting": "Observation / Short hospitalization",
            "primary": "β-lactam (ceftriaxone 1g IV daily or ampicillin-sulbactam) + macrolide",
            "alternative": "Respiratory fluoroquinolone monotherapy (IV or PO)",
            "notes": "Consider IV-to-PO switch when clinically stable",
        },
        "IV": {
            "setting": "Hospital ward",
            "primary": "β-lactam (ceftriaxone 1-2g IV daily) + macrolide (azithromycin 500mg IV/PO)",
            "alternative": "Respiratory fluoroquinolone monotherapy (levofloxacin 750mg IV daily)",
            "notes": "IV antibiotics required; de-escalate when culture results available",
        },
        "V": {
            "setting": "Hospital (ICU need requires independent severe-CAP assessment)",
            "primary": "β-lactam (ceftriaxone 2g IV or piperacillin-tazobactam) + macrolide",
            "alternative": "β-lactam + respiratory fluoroquinolone",
            "notes": "Consider MRSA coverage (vancomycin or linezolid) if risk factors present",
            "additional_considerations": [
                "Add Pseudomonas coverage if structural lung disease",
                "Consider sepsis bundle compliance",
                "Monitor for ARDS development",
            ],
        },
    }

    # Common local resistance alerts
    RESISTANCE_THRESHOLDS = {
        "macrolide_resistance": {"threshold_pct": 25, "action": "Avoid macrolide monotherapy"},
        "fluoroquinolone_resistance": {"threshold_pct": 10, "action": "Avoid fluoroquinolone monotherapy"},
        "penicillin_resistance": {"threshold_pct": 10, "action": "Increase β-lactam dose or use respiratory fluoroquinolone"},
    }

    def __init__(self, local_resistance: Optional[List[ResistancePattern]] = None):
        self.local_resistance = local_resistance or []

    def get_recommendation(
        self,
        psi_risk_class: str,
        has_comorbidities: bool = False,
        penicillin_allergy: bool = False,
        macrolide_allergy: bool = False,
    ) -> AntibioticRecommendation:
        """Generate antibiotic recommendation based on PSI class and patient factors."""
        psi_risk_class = str(psi_risk_class).upper()
        if psi_risk_class not in self.GUIDELINE_REGIMENS:
            raise ValueError("PSI class must be I, II, III, IV or V")

        regimen_info = self.GUIDELINE_REGIMENS[psi_risk_class]
        setting = regimen_info["setting"]

        # Select regimen based on comorbidities for outpatient classes
        if psi_risk_class in ("I", "II"):
            key = "with_comorbidities" if has_comorbidities else "no_comorbidities"
            reg = regimen_info[key]
            primary = reg["primary"]
            alternative = reg["alternative"]
            notes = reg.get("notes", "")
        else:
            primary = regimen_info["primary"]
            alternative = regimen_info["alternative"]
            notes = regimen_info.get("notes", "")

        # Never algorithmically substitute antimicrobials for a reported allergy.
        # The allergy phenotype and CAP severity need clinician review.
        if penicillin_allergy or macrolide_allergy:
            primary = "Individualized treatment required: review reported allergy, severity and local CAP protocol"
            alternative = "Do not select a substitute regimen based solely on the PSI class"

        # Local resistance alerts
        resistance_alerts = self._check_local_resistance(psi_risk_class)

        # Duration
        duration = 5 if psi_risk_class in ("I", "II") else 7

        # Monitoring
        monitoring = self._get_monitoring(psi_risk_class)

        return AntibioticRecommendation(
            psi_risk_class=psi_risk_class,
            setting=setting,
            primary_regimen=primary,
            alternative_regimen=alternative,
            duration_days=duration,
            monitoring=monitoring,
            de_escalation_notes=notes + " Educational example only; do not prescribe from PSI alone. Review local guidelines, renal function, allergies and clinical stability.",
            local_resistance_alerts=resistance_alerts,
        )

    def _check_local_resistance(self, psi_class: str) -> List[str]:
        """Check local antibiogram for resistance alerts relevant to the PSI class."""
        alerts = []
        for pattern in self.local_resistance:
            threshold_info = self.RESISTANCE_THRESHOLDS.get(f"{pattern.organism}_resistance")
            if threshold_info and pattern.resistance_rate_pct > threshold_info["threshold_pct"]:
                alerts.append(
                    f"ALERT: {pattern.organism} resistance to {pattern.agent} is "
                    f"{pattern.resistance_rate_pct}% (threshold: {threshold_info['threshold_pct']}%). "
                    f"Action: {threshold_info['action']}"
                )
        return alerts

    def _get_monitoring(self, psi_class: str) -> List[str]:
        """Return monitoring recommendations based on severity."""
        base = ["Clinical reassessment at 48-72 hours", "Monitor for clinical stability criteria"]
        if psi_class in ("IV", "V"):
            base.extend([
                "Daily CBC, BMP, LFTs",
                "Blood cultures at 48h if persistent fever",
                "Procalcitonin-guided duration assessment",
                "IV-to-PO conversion evaluation when afebrile ≥24h and tolerating PO",
            ])
        if psi_class == "V":
            base.extend([
                "ICU-level monitoring with continuous pulse oximetry",
                "Arterial blood gas as needed",
                "Sepsis bundle compliance monitoring",
            ])
        return base

    def generate_report(self, recommendation: AntibioticRecommendation) -> str:
        """Generate a formatted stewardship report."""
        lines = [
            "=" * 60,
            "ANTIBIOTIC STEWARDSHIP RECOMMENDATION",
            "=" * 60,
            f"PSI Risk Class: {recommendation.psi_risk_class}",
            f"Setting: {recommendation.setting}",
            f"Duration: {recommendation.duration_days} days",
            "",
            "Primary Regimen:",
            f"  {recommendation.primary_regimen}",
            "",
            "Alternative:",
            f"  {recommendation.alternative_regimen}",
        ]
        if recommendation.local_resistance_alerts:
            lines.append("")
            lines.append("LOCAL RESISTANCE ALERTS:")
            for alert in recommendation.local_resistance_alerts:
                lines.append(f"  ⚠ {alert}")
        lines.append("")
        lines.append("Monitoring:")
        for m in recommendation.monitoring:
            lines.append(f"  • {m}")
        if recommendation.de_escalation_notes:
            lines.append("")
            lines.append(f"Notes: {recommendation.de_escalation_notes}")
        lines.append("=" * 60)
        return "\n".join(lines)


def main():
    """CLI demo."""
    engine = AntibioticStewardshipEngine()
    for cls in ["I", "II", "III", "IV", "V"]:
        rec = engine.get_recommendation(cls, has_comorbidities=(cls in ("I", "II")))
        print(engine.generate_report(rec))
        print()


if __name__ == "__main__":
    main()

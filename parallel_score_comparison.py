#!/usr/bin/env python3
"""
PSI/PORT Parallel Score Comparison Engine
Calculates PSI alongside CURB-65, CRB-65, and ATS/IDSA criteria for comprehensive
pneumonia risk stratification in a single evaluation pass.

Author: Dr. Abu Suraih Sakhri | License: MIT
"""

from dataclasses import dataclass, field
import math
from psi_port import calculate_metrics, FIELD_NAMES
from typing import Any, Dict, List, Optional


@dataclass
class PneumoniaPatient:
    """Patient data model for parallel pneumonia severity scoring."""
    patient_id: str
    age: float
    sex: str  # "male" or "female"
    # PSI/PORT components
    nursing_home_resident: bool = False
    neoplastic_disease: bool = False
    liver_disease: bool = False
    congestive_heart_failure: bool = False
    cerebrovascular_disease: bool = False
    renal_disease: bool = False
    altered_mental_status: bool = False
    respiratory_rate_ge_30: bool = False
    systolic_bp_lt_90: bool = False
    temperature_lt_35: bool = False
    temperature_ge_40: bool = False
    oxygen_saturation_lt_90: bool = False
    diastolic_bp_le_60: bool = False
    pulse_ge_125: bool = False
    arterial_ph_lt_7_35: bool = False
    bun_ge_30: bool = False
    sodium_lt_130: bool = False
    glucose_ge_250: bool = False
    hematocrit_lt_30: bool = False
    pao2_lt_60: bool = False
    pleural_effusion: bool = False
    # CURB-65 / CRB-65 components
    confusion: bool = False
    urea_gt_7: bool = False  # mmol/L (CURB-65 specific)
    # ATS/IDSA components
    major_criteria: List[str] = field(default_factory=list)  # septic shock, mechanical ventilation
    minor_criteria: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate patient data on construction."""
        if not self.patient_id or not str(self.patient_id).strip():
            raise ValueError("patient_id is required and cannot be empty")
        if isinstance(self.age, bool) or not isinstance(self.age, (int, float)) or not math.isfinite(self.age) or not float(self.age).is_integer() or not 18 <= self.age <= 120:
            raise ValueError(f"age must be an integer between 18 and 120, got {self.age}")
        if str(self.sex).lower() not in ("male", "female"):
            raise ValueError(f"sex must be 'male' or 'female', got '{self.sex}'")

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


class ParallelScoreComparison:
    """
    Computes PSI/PORT, CURB-65, CRB-65, and ATS/IDSA severity scores
    simultaneously for comprehensive pneumonia risk stratification.
    """

    def compute_psi_score(self, patient: PneumoniaPatient) -> Dict[str, Any]:
        """Score using the same clinically validated PSI core as the CLI and API."""
        factors = {name: getattr(patient, name) for name in FIELD_NAMES
                   if name not in ("temperature_extreme", "hypoxemia")}
        factors["temperature_extreme"] = patient.temperature_lt_35 or patient.temperature_ge_40
        factors["hypoxemia"] = patient.pao2_lt_60 or patient.oxygen_saturation_lt_90
        result = calculate_metrics(age=int(patient.age), sex=patient.sex.lower(), **factors)
        return {
            **result,
            "estimated_mortality": "Risk class predicts relative 30-day mortality; see Fine 1997 cohorts",
        }

    def compute_curb65_score(self, patient: PneumoniaPatient) -> Dict[str, Any]:
        """Compute CURB-65 score (0-5)."""
        score = 0
        criteria = []

        if patient.confusion:
            score += 1
            criteria.append("Confusion")
        # Urea > 7 mmol/L (~BUN > 20 mg/dL)
        if patient.urea_gt_7:
            score += 1
            criteria.append("Urea > 7 mmol/L")
        if patient.respiratory_rate_ge_30:
            score += 1
            criteria.append("Respiratory rate ≥ 30")
        if patient.systolic_bp_lt_90 or patient.diastolic_bp_le_60:
            score += 1
            criteria.append("Systolic BP < 90 or Diastolic ≤ 60")
        if patient.age >= 65:
            score += 1
            criteria.append("Age ≥ 65")

        mortality_map = {0: "0.7%", 1: "3.2%", 2: "13%", 3: "17%", 4: "41%", 5: "57%"}
        if score <= 1:
            disposition = "Consider outpatient management"
        elif score == 2:
            disposition = "Consider short inpatient or supervised outpatient"
        else:
            disposition = "Hospitalize, consider ICU"

        return {
            "score": score,
            "estimated_mortality": mortality_map.get(score, "N/A"),
            "recommended_disposition": disposition,
            "criteria_met": criteria,
        }

    def compute_crb65_score(self, patient: PneumoniaPatient) -> Dict[str, Any]:
        """Compute CRB-65 score (0-4) — no laboratory values required."""
        score = 0
        criteria = []

        if patient.confusion:
            score += 1
            criteria.append("Confusion")
        if patient.respiratory_rate_ge_30:
            score += 1
            criteria.append("Respiratory rate ≥ 30")
        if patient.systolic_bp_lt_90:
            score += 1
            criteria.append("Systolic BP < 90 or Diastolic ≤ 60")
        if patient.age >= 65:
            score += 1
            criteria.append("Age ≥ 65")

        mortality_map = {0: "0.7%", 1: "3.2%", 2: "13%", 3: "17%", 4: "41%"}
        if score == 0:
            disposition = "Outpatient management"
        elif score == 1:
            disposition = "Outpatient with close follow-up"
        elif score == 2:
            disposition = "Consider hospital admission"
        else:
            disposition = "Hospitalize urgently, consider ICU"

        return {
            "score": score,
            "estimated_mortality": mortality_map.get(score, "N/A"),
            "recommended_disposition": disposition,
            "criteria_met": criteria,
        }

    def compute_ats_idsa_severity(self, patient: PneumoniaPatient) -> Dict[str, Any]:
        """Compute ATS/IDSA 2007 severe CAP criteria."""
        major_count = len(patient.major_criteria)
        minor_count = len(patient.minor_criteria)

        is_severe = major_count >= 1 or minor_count >= 3

        return {
            "major_criteria_count": major_count,
            "major_criteria": patient.major_criteria,
            "minor_criteria_count": minor_count,
            "minor_criteria": patient.minor_criteria,
            "is_severe_cap": is_severe,
            "icu_recommended": is_severe,
            "recommendation": "ICU admission recommended" if is_severe else "Standard ward management",
        }

    def compute_all_scores(self, patient: PneumoniaPatient) -> Dict[str, Any]:
        """Run all four scoring systems and return a unified comparison."""
        psi = self.compute_psi_score(patient)
        curb65 = self.compute_curb65_score(patient)
        crb65 = self.compute_crb65_score(patient)
        ats_idsa = self.compute_ats_idsa_severity(patient)

        # Consensus disposition
        dispositions = [psi["recommended_disposition"], curb65["recommended_disposition"], crb65["recommended_disposition"]]
        icu_flags = [ats_idsa["icu_recommended"], "ICU" in psi["recommended_disposition"]]
        consensus_icu = any(icu_flags)

        return {
            "patient_id": patient.patient_id,
            "psi_port": psi,
            "curb65": curb65,
            "crb65": crb65,
            "ats_idsa": ats_idsa,
            "consensus": {
                "icu_recommended": consensus_icu,
                "scores_agree_on_hospitalization": all("hospital" in d.lower() or "inpatient" in d.lower() for d in dispositions),
                "highest_risk_tool": "ATS/IDSA" if ats_idsa["is_severe_cap"] else "PSI/PORT" if psi["risk_class"] in ("IV", "V") else "CURB-65/CRB-65",
            },
        }


def main():
    """CLI demo for parallel score comparison."""
    patient = PneumoniaPatient(
        patient_id="DEMO-001",
        age=72,
        sex="male",
        confusion=True,
        respiratory_rate_ge_30=True,
        systolic_bp_lt_90=False,
        urea_gt_7=True,
        bun_ge_30=True,
        nursing_home_resident=False,
        neoplastic_disease=False,
        liver_disease=False,
        congestive_heart_failure=True,
        cerebrovascular_disease=False,
        renal_disease=False,
        altered_mental_status=True,
        arterial_ph_lt_7_35=False,
        sodium_lt_130=False,
        glucose_ge_250=False,
        hematocrit_lt_30=False,
        pao2_lt_60=True,
        pleural_effusion=False,
        major_criteria=[],
        minor_criteria=["Confusion", "BUN ≥ 20", "PaO2/FiO2 ≤ 250"],
    )

    engine = ParallelScoreComparison()
    result = engine.compute_all_scores(patient)

    import json
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
PSI/PORT Parallel Score Comparison Engine
Calculates PSI alongside CURB-65, CRB-65, and ATS/IDSA criteria for comprehensive
pneumonia risk stratification in a single evaluation pass.

Author: Dr. Abu Suraih Sakhri | License: MIT
"""

from dataclasses import dataclass, field
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

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


class ParallelScoreComparison:
    """
    Computes PSI/PORT, CURB-65, CRB-65, and ATS/IDSA severity scores
    simultaneously for comprehensive pneumonia risk stratification.
    """

    def compute_psi_score(self, patient: PneumoniaPatient) -> Dict[str, Any]:
        """Compute PSI/PORT score (0-395+) and Risk Class (I-V)."""
        score = 0
        components = []

        # Demographics
        score += int(patient.age)
        if patient.sex == "female":
            score -= 10
            components.append("Female sex: -10")

        # Comorbidities
        comorbidity_map = {
            "nursing_home_resident": ("Nursing home resident", 10),
            "neoplastic_disease": ("Neoplastic disease", 30),
            "liver_disease": ("Liver disease", 20),
            "congestive_heart_failure": ("Congestive heart failure", 10),
            "cerebrovascular_disease": ("Cerebrovascular disease", 10),
            "renal_disease": ("Renal disease", 10),
        }
        for attr, (label, pts) in comorbidity_map.items():
            if getattr(patient, attr):
                score += pts
                components.append(f"{label}: +{pts}")

        # Physical examination
        exam_map = {
            "altered_mental_status": ("Altered mental status", 20),
            "respiratory_rate_ge_30": ("Respiratory rate ≥ 30", 20),
            "systolic_bp_lt_90": ("Systolic BP < 90 mmHg", 20),
            "temperature_lt_35": ("Temperature < 35°C", 15),
            "pulse_ge_125": ("Pulse ≥ 125/min", 10),
        }
        for attr, (label, pts) in exam_map.items():
            if getattr(patient, attr):
                score += pts
                components.append(f"{label}: +{pts}")

        # Laboratory and radiographic
        lab_map = {
            "arterial_ph_lt_7_35": ("Arterial pH < 7.35", 30),
            "bun_ge_30": ("BUN ≥ 30 mg/dL", 20),
            "sodium_lt_130": ("Sodium < 130 mEq/L", 20),
            "glucose_ge_250": ("Glucose ≥ 250 mg/dL", 10),
            "hematocrit_lt_30": ("Hematocrit < 30%", 10),
            "pao2_lt_60": ("PaO2 < 60 mmHg", 10),
            "pleural_effusion": ("Pleural effusion", 10),
        }
        for attr, (label, pts) in lab_map.items():
            if getattr(patient, attr):
                score += pts
                components.append(f"{label}: +{pts}")

        # Risk class determination
        if score <= 0:
            risk_class = "I"
            mortality = "0.1%"
            disposition = "Outpatient"
        elif score <= 70:
            risk_class = "II"
            mortality = "0.6%"
            disposition = "Outpatient"
        elif score <= 90:
            risk_class = "III"
            mortality = "2.8%"
            disposition = "Observation or brief hospitalization"
        elif score <= 130:
            risk_class = "IV"
            mortality = "8.2%"
            disposition = "Hospitalize"
        else:
            risk_class = "V"
            mortality = "29.2%"
            disposition = "Hospitalize, consider ICU"

        return {
            "score": score,
            "risk_class": risk_class,
            "estimated_mortality": mortality,
            "recommended_disposition": disposition,
            "components": components,
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
        if patient.systolic_bp_lt_90:
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
                "scores_agree_on_hospitalization": "Hospitalize" in " ".join(dispositions),
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

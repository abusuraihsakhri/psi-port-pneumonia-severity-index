"""
Automated Pytest for psi-port-pneumonia-severity-index Clinical Engines.
Tests PSI/PORT scoring, antibiotic stewardship, and disposition decision support.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from parallel_score_comparison import PneumoniaPatient, ParallelScoreComparison
from antibiotic_stewardship import AntibioticStewardshipEngine, ResistancePattern
from disposition_decision_support import DispositionDecisionEngine, BedAvailability


class TestPneumoniaPatientValidation:
    """Test PneumoniaPatient input validation."""

    def test_valid_patient_creation(self):
        patient = PneumoniaPatient(patient_id="PT-001", age=65, sex="male")
        assert patient.patient_id == "PT-001"
        assert patient.age == 65
        assert patient.sex == "male"

    def test_invalid_patient_id_empty(self):
        with pytest.raises(ValueError, match="patient_id is required"):
            PneumoniaPatient(patient_id="", age=65, sex="male")

    def test_invalid_patient_id_whitespace(self):
        with pytest.raises(ValueError, match="patient_id is required"):
            PneumoniaPatient(patient_id="   ", age=65, sex="male")

    def test_invalid_age_negative(self):
        with pytest.raises(ValueError, match="age must be an integer between 18 and 120"):
            PneumoniaPatient(patient_id="PT-001", age=-5, sex="male")

    def test_invalid_age_too_high(self):
        with pytest.raises(ValueError, match="age must be between 0 and 150"):
            PneumoniaPatient(patient_id="PT-001", age=200, sex="male")

    def test_invalid_sex(self):
        with pytest.raises(ValueError, match="sex must be 'male' or 'female'"):
            PneumoniaPatient(patient_id="PT-001", age=65, sex="unknown")


class TestPSIScoring:
    """Test PSI/PORT score calculation."""

    def test_low_risk_class_I(self):
        engine = ParallelScoreComparison()
        # A 35-year-old with no listed clinical risk factors qualifies at stage 1.
        patient = PneumoniaPatient(
            patient_id="PT-001", age=35, sex="female",
            nursing_home_resident=False,
        )
        result = engine.compute_psi_score(patient)
        assert result["risk_class"] == "I"
        assert result["score"] == 25

    def test_class_II_older_adult(self):
        engine = ParallelScoreComparison()
        # 55-year-old male does not qualify for Class I, score 55 -> II
        patient = PneumoniaPatient(
            patient_id="PT-002", age=55, sex="male",
        )
        result = engine.compute_psi_score(patient)
        assert result["risk_class"] == "II"
        assert result["score"] <= 70

    def test_high_temperature_and_oxygen_saturation(self):
        engine = ParallelScoreComparison()
        patient = PneumoniaPatient(
            patient_id="PT-X", age=65, sex="male",
            temperature_ge_40=True, oxygen_saturation_lt_90=True,
        )
        result = engine.compute_psi_score(patient)
        assert result["score"] == 90
        assert result["risk_class"] == "III"

    def test_high_risk_class_V(self):
        engine = ParallelScoreComparison()
        patient = PneumoniaPatient(
            patient_id="PT-002", age=85, sex="male",
            nursing_home_resident=True,
            neoplastic_disease=True,
            liver_disease=True,
            congestive_heart_failure=True,
            cerebrovascular_disease=True,
            renal_disease=True,
            altered_mental_status=True,
            respiratory_rate_ge_30=True,
            systolic_bp_lt_90=True,
            temperature_lt_35=True,
            pulse_ge_125=True,
            arterial_ph_lt_7_35=True,
            bun_ge_30=True,
            sodium_lt_130=True,
            glucose_ge_250=True,
            hematocrit_lt_30=True,
            pao2_lt_60=True,
            pleural_effusion=True,
        )
        result = engine.compute_psi_score(patient)
        assert result["risk_class"] == "V"
        assert result["score"] > 130

    def test_female_sex_adjustment(self):
        engine = ParallelScoreComparison()
        patient_male = PneumoniaPatient(patient_id="PT-M", age=60, sex="male")
        patient_female = PneumoniaPatient(patient_id="PT-F", age=60, sex="female")
        result_male = engine.compute_psi_score(patient_male)
        result_female = engine.compute_psi_score(patient_female)
        assert result_female["score"] == result_male["score"] - 10

    def test_nursing_home_resident_bonus(self):
        engine = ParallelScoreComparison()
        patient_without = PneumoniaPatient(patient_id="PT-001", age=70, sex="male")
        patient_with = PneumoniaPatient(patient_id="PT-002", age=70, sex="male", nursing_home_resident=True)
        result_without = engine.compute_psi_score(patient_without)
        result_with = engine.compute_psi_score(patient_with)
        assert result_with["score"] == result_without["score"] + 10


class TestCURB65Scoring:
    """Test CURB-65 score calculation."""

    def test_curb65_zero_score(self):
        engine = ParallelScoreComparison()
        patient = PneumoniaPatient(
            patient_id="PT-001", age=45, sex="male",
            confusion=False, urea_gt_7=False,
            respiratory_rate_ge_30=False, systolic_bp_lt_90=False,
        )
        result = engine.compute_curb65_score(patient)
        assert result["score"] == 0

    def test_curb65_max_score(self):
        engine = ParallelScoreComparison()
        patient = PneumoniaPatient(
            patient_id="PT-001", age=70, sex="male",
            confusion=True, urea_gt_7=True,
            respiratory_rate_ge_30=True, systolic_bp_lt_90=True,
        )
        result = engine.compute_curb65_score(patient)
        assert result["score"] == 5

    def test_crb65_max_score(self):
        engine = ParallelScoreComparison()
        patient = PneumoniaPatient(
            patient_id="PT-001", age=70, sex="male",
            confusion=True, respiratory_rate_ge_30=True,
            systolic_bp_lt_90=True,
        )
        result = engine.compute_crb65_score(patient)
        assert result["score"] == 4


class TestATSIDSASeverity:
    """Test ATS/IDSA severity criteria."""

    def test_non_severe_cap(self):
        engine = ParallelScoreComparison()
        patient = PneumoniaPatient(
            patient_id="PT-001", age=55, sex="male",
            major_criteria=[], minor_criteria=["Confusion"],
        )
        result = engine.compute_ats_idsa_severity(patient)
        assert result["is_severe_cap"] is False
        assert result["icu_recommended"] is False

    def test_severe_cap_major_criteria(self):
        engine = ParallelScoreComparison()
        patient = PneumoniaPatient(
            patient_id="PT-001", age=55, sex="male",
            major_criteria=["Septic shock requiring vasopressors"],
            minor_criteria=[],
        )
        result = engine.compute_ats_idsa_severity(patient)
        assert result["is_severe_cap"] is True
        assert result["icu_recommended"] is True

    def test_severe_cap_minor_criteria(self):
        engine = ParallelScoreComparison()
        patient = PneumoniaPatient(
            patient_id="PT-001", age=55, sex="male",
            major_criteria=[],
            minor_criteria=["Confusion", "BUN >= 20", "PaO2/FiO2 <= 250"],
        )
        result = engine.compute_ats_idsa_severity(patient)
        assert result["is_severe_cap"] is True


class TestAntibioticStewardship:
    """Test antibiotic stewardship engine."""

    def test_class_I_recommendation(self):
        engine = AntibioticStewardshipEngine()
        rec = engine.get_recommendation("I")
        assert rec.psi_risk_class == "I"
        assert rec.setting == "Outpatient"
        assert rec.duration_days == 5

    def test_class_V_recommendation(self):
        engine = AntibioticStewardshipEngine()
        rec = engine.get_recommendation("V")
        assert rec.psi_risk_class == "V"
        assert rec.setting == "ICU"
        assert rec.duration_days == 7

    def test_invalid_class_defaults_to_III(self):
        engine = AntibioticStewardshipEngine()
        rec = engine.get_recommendation("INVALID")
        assert rec.psi_risk_class == "III"

    def test_penicillin_allergy_adjustment(self):
        engine = AntibioticStewardshipEngine()
        rec_normal = engine.get_recommendation("I", penicillin_allergy=False)
        rec_allergy = engine.get_recommendation("I", penicillin_allergy=True)
        assert "Amoxicillin" not in rec_allergy.primary_regimen

    def test_local_resistance_alert(self):
        resistance_data = [
            ResistancePattern(
                organism="macrolide",
                agent="azithromycin",
                resistance_rate_pct=35.0,
                sample_size=200,
                year=2024,
            )
        ]
        engine = AntibioticStewardshipEngine(local_resistance=resistance_data)
        rec = engine.get_recommendation("IV")
        assert len(rec.local_resistance_alerts) > 0
        assert "macrolide" in rec.local_resistance_alerts[0].lower()

    def test_comorbidities_adjustment(self):
        engine = AntibioticStewardshipEngine()
        rec_no_comorbid = engine.get_recommendation("I", has_comorbidities=False)
        rec_with_comorbid = engine.get_recommendation("I", has_comorbidities=True)
        assert rec_no_comorbid.primary_regimen != rec_with_comorbid.primary_regimen


class TestDispositionDecision:
    """Test disposition decision engine."""

    def test_class_I_home_disposition(self):
        engine = DispositionDecisionEngine()
        decision = engine.make_decision("PT-001", "I", 0)
        assert decision.recommended_level == "home"
        assert decision.bed_urgency == "routine"

    def test_class_V_icu_disposition(self):
        engine = DispositionDecisionEngine()
        decision = engine.make_decision("PT-001", "V", 160)
        assert decision.recommended_level == "icu"
        assert decision.bed_urgency == "emergent"

    def test_bed_unavailability_fallback(self):
        beds = BedAvailability(icu_beds_available=0, step_down_beds_available=5)
        engine = DispositionDecisionEngine(bed_availability=beds)
        decision = engine.make_decision("PT-001", "V", 160)
        # Should fall back to step_down when ICU is full
        assert decision.recommended_level == "step_down"

    def test_social_factors_adjustment(self):
        engine = DispositionDecisionEngine()
        decision = engine.make_decision(
            "PT-001", "I", 0,
            social_factors={"lives_alone": True}
        )
        assert any("lives alone" in r.lower() for r in decision.rationale)

    def test_invalid_class_defaults_to_III(self):
        engine = DispositionDecisionEngine()
        decision = engine.make_decision("PT-001", "INVALID", 85)
        assert decision.psi_risk_class == "III"
        assert decision.recommended_level == "observation"

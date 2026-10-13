"""Regression tests for the original Fine/PORT two-step adult PSI rule."""
import csv
import pytest
from psi_port import FACTORS, FIELD_NAMES, calculate_metrics, process_batch


def patient(age=65, sex="male", **findings):
    data = {"age": age, "sex": sex, **{name: False for name in FIELD_NAMES}}
    data.update(findings)
    return data


def test_class_i_from_initial_screen_not_point_cutoff():
    assert calculate_metrics(**patient(age=50))["risk_class"] == "I"
    # Class I does not depend on a numerically low point total.
    result = calculate_metrics(**patient(age=50, sex="female", arterial_ph_lt_7_35=True,
                                         bun_ge_30=True, sodium_lt_130=True))
    assert result["risk_class"] == "I"
    assert result["score"] == 110
    assert result["class_i_screen"] is True


@pytest.mark.parametrize("age,expected", [(51, "II"), (70, "II"), (71, "III"),
                                           (90, "III"), (91, "IV"), (120, "IV")])
def test_numeric_class_boundaries(age, expected):
    assert calculate_metrics(**patient(age=age))["risk_class"] == expected


def test_class_v_boundary_and_weight():
    result = calculate_metrics(**patient(age=101, neoplastic_disease=True))
    assert result["score"] == 131
    assert result["risk_class"] == "V"


def test_female_subtraction_and_high_fever():
    male = calculate_metrics(**patient(age=65, temperature_extreme=True))
    female = calculate_metrics(**patient(age=65, sex="female", temperature_extreme=True))
    assert male["score"] == 80
    assert female["score"] == 70
    assert male["risk_class"] == "III"
    assert female["risk_class"] == "II"


def test_step_one_is_excluded_by_an_abnormal_vital_or_comorbidity():
    for field in ("neoplastic_disease", "altered_mental_status", "temperature_extreme",
                  "respiratory_rate_ge_30"):
        assert calculate_metrics(**patient(age=35, **{field: True}))["risk_class"] != "I"


def test_hypoxemia_is_10_points_and_not_double_counted():
    normal = calculate_metrics(**patient(age=72))
    hypox = calculate_metrics(**patient(age=72, hypoxemia=True))
    assert hypox["score"] - normal["score"] == 10


@pytest.mark.parametrize("invalid", [
    {"age": 17}, {"age": 121}, {"age": 50.5}, {"age": float("nan")},
    {"sex": "other"}, {"neoplastic_disease": "unknown"},
    {"nursing_home_resident": None},
])
def test_reject_invalid_or_unassessed_data(invalid):
    with pytest.raises(ValueError):
        calculate_metrics(**patient(**invalid))


def test_missing_or_extra_data_is_not_accepted():
    data = patient()
    data.pop("bun_ge_30")
    with pytest.raises(ValueError, match="Missing"):
        calculate_metrics(**data)
    with pytest.raises(ValueError, match="Unknown"):
        calculate_metrics(**patient(made_up=True))


def test_csv_batch_accepts_boolean_values_and_reports_class(tmp_path):
    source, out = tmp_path / "cases.csv", tmp_path / "result.csv"
    fields = ["age", "sex", *FIELD_NAMES]
    with source.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({**patient(age=70), **{key: "false" for key in FIELD_NAMES}})
        writer.writerow({**patient(age=91), **{key: "true" if key == "hypoxemia" else "false"
                                              for key in FIELD_NAMES}})
    process_batch(str(source), str(out))
    with out.open(newline="") as handle:
        results = list(csv.DictReader(handle))
    assert [(r["score"], r["risk_class"]) for r in results] == [("70", "II"), ("101", "IV")]


def test_bad_csv_does_not_create_partially_valid_output(tmp_path):
    source, out = tmp_path / "bad.csv", tmp_path / "result.csv"
    fields = ["age", "sex", *FIELD_NAMES]
    with source.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({**patient(), **{key: "false" for key in FIELD_NAMES}})
        writer.writerow({**patient(), **{key: "" for key in FIELD_NAMES}})
    with pytest.raises(ValueError, match="line 3"):
        process_batch(str(source), str(out))
    assert not out.exists()

#!/usr/bin/env python3
"""Adult community-acquired pneumonia Pneumonia Severity Index (Fine/PORT).

The two-step PSI prediction rule estimates 30-day mortality risk, not ICU need.
All boolean findings must be explicitly supplied as assessed true/false values.
Reference: Fine MJ et al. N Engl J Med. 1997;336:243-250.
DOI: 10.1056/NEJM199701233360402
"""
import argparse
import csv
import json
import math
from pathlib import Path

# Field name, display label, points, category.
FACTORS = (
    ("nursing_home_resident", "Nursing-home resident", 10, "demographic"),
    ("neoplastic_disease", "Neoplastic disease", 30, "comorbidity"),
    ("liver_disease", "Liver disease", 20, "comorbidity"),
    ("congestive_heart_failure", "Congestive heart failure", 10, "comorbidity"),
    ("cerebrovascular_disease", "Cerebrovascular disease", 10, "comorbidity"),
    ("renal_disease", "Renal disease", 10, "comorbidity"),
    ("altered_mental_status", "Altered mental status", 20, "examination"),
    ("respiratory_rate_ge_30", "Respiratory rate ≥30/min", 20, "examination"),
    ("systolic_bp_lt_90", "Systolic BP <90 mmHg", 20, "examination"),
    ("temperature_extreme", "Temperature <35°C or ≥40°C", 15, "examination"),
    ("pulse_ge_125", "Pulse ≥125/min", 10, "examination"),
    ("arterial_ph_lt_7_35", "Arterial pH <7.35", 30, "investigation"),
    ("bun_ge_30", "BUN ≥30 mg/dL", 20, "investigation"),
    ("sodium_lt_130", "Sodium <130 mmol/L", 20, "investigation"),
    ("glucose_ge_250", "Glucose ≥250 mg/dL", 10, "investigation"),
    ("hematocrit_lt_30", "Hematocrit <30%", 10, "investigation"),
    ("hypoxemia", "PaO₂ <60 mmHg or oxygen saturation <90%", 10, "investigation"),
    ("pleural_effusion", "Pleural effusion", 10, "investigation"),
)
FIELD_NAMES = tuple(f[0] for f in FACTORS)
ALL_FIELDS = frozenset(("age", "sex", *FIELD_NAMES))
RISK_DETAILS = {
    "I": ("Very low", "Consider outpatient care if otherwise clinically appropriate"),
    "II": ("Low", "Consider outpatient care if otherwise clinically appropriate"),
    "III": ("Intermediate", "Consider observation or short hospitalization"),
    "IV": ("High", "Hospital assessment/admission generally indicated"),
    "V": ("Very high", "Hospital assessment/admission generally indicated"),
}


def _boolean(value, field):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("true", "yes", "1"):
            return True
        if normalized in ("false", "no", "0"):
            return False
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    raise ValueError(f"{field} must be explicitly true or false")


def calculate_metrics(**kwargs):
    """Return scored PSI and risk class after all assessed inputs are supplied.

    Adults only. Class I is assigned from the original initial clinical screen
    (age ≤50 with no five comorbidities or five examination abnormalities);
    it is *not* a numerical score band. Absent findings must not be assumed
    negative merely because they were unmeasured.
    """
    unknown = set(kwargs) - ALL_FIELDS
    missing = ALL_FIELDS - set(kwargs)
    if unknown:
        raise ValueError("Unknown PSI fields: " + ", ".join(sorted(unknown)))
    if missing:
        raise ValueError("Missing assessed PSI fields: " + ", ".join(sorted(missing)))
    age = kwargs["age"]
    if isinstance(age, bool) or not isinstance(age, (int, float)) or not math.isfinite(age) or not float(age).is_integer() or not 18 <= age <= 120:
        raise ValueError("age must be an integer from 18 to 120 years (adult CAP only)")
    age = int(age)
    sex = kwargs["sex"]
    if not isinstance(sex, str) or sex.strip().lower() not in ("male", "female"):
        raise ValueError("sex must be 'male' or 'female' for the original PSI formula")
    sex = sex.strip().lower()
    assessed = {name: _boolean(kwargs[name], name) for name in FIELD_NAMES}
    score = age - (10 if sex == "female" else 0)
    components = [{"factor": "Age / sex", "points": score}]
    for name, label, points, _group in FACTORS:
        if assessed[name]:
            score += points
            components.append({"factor": label, "points": points})

    qualifies_for_class_i = (
        age <= 50 and
        not any(assessed[name] for name, _, _, group in FACTORS if group in ("comorbidity", "examination"))
    )
    if qualifies_for_class_i:
        risk_class = "I"
    elif score <= 70:
        risk_class = "II"
    elif score <= 90:
        risk_class = "III"
    elif score <= 130:
        risk_class = "IV"
    else:
        risk_class = "V"
    level, disposition = RISK_DETAILS[risk_class]
    return {
        "tool": "psi-port-pneumonia-severity-index",
        "score": score,
        "risk_class": risk_class,
        "classification": "Class " + risk_class + " — " + level,
        "risk_level": level,
        "clinical_recommendation": disposition,
        "recommended_disposition": disposition,
        "class_i_screen": qualifies_for_class_i,
        "components": components,
        "inputs_evaluated": len(ALL_FIELDS),
        "note": "PSI predicts mortality risk, not ICU admission. Apply clinical judgment and severe CAP criteria.",
    }


def process_batch(input_csv, output_csv):
    """Score a CSV; fail atomically if any row is incomplete or invalid."""
    source = Path(input_csv)
    if not source.is_file():
        raise FileNotFoundError(f"Input CSV not found: {source}")
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        original_fields = reader.fieldnames or []
        if len(original_fields) != len(set(original_fields)) or not ALL_FIELDS.issubset(original_fields):
            raise ValueError("CSV needs unique column headers including age, sex and all 18 assessed PSI findings")
        output = []
        for row_number, row in enumerate(reader, start=2):
            try:
                age = int(row["age"])
                inputs = {name: row[name] for name in FIELD_NAMES}
                result = calculate_metrics(age=age, sex=row["sex"], **inputs)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid PSI data on CSV line {row_number}: {exc}") from exc
            output.append({**row, "score": result["score"], "risk_class": result["risk_class"],
                           "classification": result["classification"],
                           "clinical_recommendation": result["clinical_recommendation"]})
    with Path(output_csv).open("w", encoding="utf-8", newline="") as handle:
        extra = ["score", "risk_class", "classification", "clinical_recommendation"]
        writer = csv.DictWriter(handle, fieldnames=list(dict.fromkeys([*original_fields, *extra])))
        writer.writeheader()
        writer.writerows(output)
    print(f"Processed {len(output)} records -> {output_csv}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validated two-step adult PSI/PORT scoring")
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("single", help="Score one patient with assessed clinical findings")
    one.add_argument("--age", type=int, required=True)
    one.add_argument("--sex", choices=("male", "female"), required=True)
    for name in FIELD_NAMES:
        one.add_argument("--" + name.replace("_", "-"), action="store_true",
                         help="Mark finding present (otherwise explicitly absent)")
    one.add_argument("--assessed-all", action="store_true", required=True,
                     help="Confirm all omitted flags were assessed and absent")
    batch = sub.add_parser("batch", help="Score rows in a fully assessed CSV")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            data = vars(args)
            data.pop("command")
            data.pop("assessed_all")
            print(json.dumps(calculate_metrics(**data), indent=2, ensure_ascii=False))
        else:
            process_batch(args.input, args.output)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

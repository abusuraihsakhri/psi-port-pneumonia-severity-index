"""Public PSI API and single/batch command regression tests."""
import csv
from psi_port import FIELD_NAMES, calculate_metrics, process_batch, main


def test_single_class_ii():
    inputs = {"age": 65, "sex": "male", **{name: False for name in FIELD_NAMES}}
    result = calculate_metrics(**inputs)
    assert result["score"] == 65
    assert result["risk_class"] == "II"


def test_batch(tmp_path):
    input_csv = tmp_path / "in.csv"
    output_csv = tmp_path / "out.csv"
    columns = ["age", "sex", *FIELD_NAMES]
    with input_csv.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerow({"age": 65, "sex": "male", **{name: "false" for name in FIELD_NAMES}})
    process_batch(str(input_csv), str(output_csv))
    with output_csv.open(newline="") as stream:
        result = next(csv.DictReader(stream))
    assert result["risk_class"] == "II"


def test_single_cli(capsys):
    assert main(["single", "--age", "65", "--sex", "male", "--assessed-all"]) == 0
    assert '"risk_class": "II"' in capsys.readouterr().out

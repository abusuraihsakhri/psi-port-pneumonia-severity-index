# Pneumonia Severity Index (PSI / PORT)

An adult community-acquired pneumonia prognostic calculator implementing the two-step Pneumonia Severity Index (PSI/PORT) described by Fine and colleagues. The same point rules are implemented in Python and dependency-free browser JavaScript.

The calculator is intended for trained clinicians or clinical education. **It estimates relative 30-day mortality risk, not ICU admission criteria or a treatment prescription.** Clinical instability, oxygen needs, social circumstances and clinician judgment take precedence.

## Browser calculator

The static interface is in [`web/index.html`](web/index.html). It runs without Python, a backend, cookies, local storage or external libraries. The repository's GitHub Pages workflow publishes the contents of `web/` after Python and JavaScript tests pass. Deployment is not equivalent to clinical validation of this software.

No patient names or identifiers are requested. The browser calculator performs arithmetic locally; it does not submit input data. Do not enter protected patient information into the legacy API or logging utilities, which are not authenticated or certified for clinical PHI.

## Scoring

The PSI is a **two-stage** rule:

1. **Class I:** age 50 years or younger, with none of the five specified comorbidities and none of the five specified abnormal examination findings. This initial screen is *not* based on the point-total threshold.
2. **Classes II–V:** otherwise, sum age (minus 10 points for female sex), nursing-home status and the individual weighted clinical, laboratory and radiographic findings.

| Class | Rule | General interpretation |
| --- | --- | --- |
| I | Initial low-risk screen | Very low estimated risk |
| II | Point total ≤ 70, if not I | Low |
| III | 71–90 | Intermediate |
| IV | 91–130 | High |
| V | > 130 | Very high |

The calculator covers 18 explicitly assessed findings. Examples: neoplastic disease +30, liver disease +20, altered mental status +20, respiratory rate ≥30/min +20, temperature <35°C **or ≥40°C** +15, arterial pH <7.35 +30, BUN ≥30 mg/dL +20, and PaO₂ <60 mmHg **or** oxygen saturation <90% +10. The browser lists the full set and shows a point breakdown.

**Unmeasured does not mean normal.** To prevent silent risk underestimation, Python and API callers must explicitly supply all 18 boolean findings. In the browser, all unchecked findings must have been assessed and confirmed absent before calculation. Only adults aged 18–120 are accepted by this implementation. The historical score requires its original male/female input variable; it was not designed as a sex-inclusive model.

## Python installation and CLI

Python 3.10 or newer:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
node --test web/psi.test.cjs  # optional: browser algorithm tests, Node.js 18+
```

Single-case assessment, only when **every other checkbox-style criterion was assessed and absent**:

```bash
psi-port psi --age 65 --sex male --assessed-all
# Example with present findings:
psi-port psi --age 72 --sex female --congestive-heart-failure --hypoxemia --assessed-all
```

CSV batch evaluation:

```bash
psi-port psi-batch -i sample.csv -o results.csv
# Also available: python psi_port.py batch -i sample.csv -o results.csv
```

The CSV must contain `age`, `sex` and all 18 PSI flag columns (`true`/`false`, `yes`/`no` or `1`/`0`). See [`sample.csv`](sample.csv). Invalid or incomplete rows raise an error rather than silently producing a low-risk classification.

## Optional REST server

```bash
psi-port serve --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` for the calculator or `http://127.0.0.1:8000/docs` for the generated FastAPI documentation. `POST /api/psi` accepts `age`, `sex` and all 18 *required* boolean findings. Browser and Python results are intended to follow the same rule, with regression tests covering clinical boundaries.

The older `audit`, `chat`, `batch`, `verify-audit` commands and `/api/audit` endpoints remain for compatibility. **They are generic demonstrations, not PSI calculations, protected clinical systems or validated PHI detectors.** Mock responses are not clinical verification. Ancillary antibiotic and disposition modules contain illustrative pathways, not individualized prescribing or bed-placement decisions.

## Security and deployment

The browser tool transmits no clinical inputs and requires no Python-in-the-browser runtime. For server use, `docker-compose.yml` requires an environment-provided `AUDIT_SECRET_KEY` and binds to localhost by default:

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

The legacy in-memory HMAC ledger verifies chained signatures but is **not persistent** and is not a compliance-grade audit system. The identifier-pattern guard is not a complete PHI detection/de-identification system and does not establish HIPAA compliance. Do not expose the unauthenticated API to untrusted networks or transmit clinical identifiers to it.

## References

- Fine MJ, Auble TE, Yealy DM, et al. A prediction rule to identify low-risk patients with community-acquired pneumonia. *N Engl J Med*. 1997;336:243–250. [doi:10.1056/NEJM199701233360402](https://doi.org/10.1056/NEJM199701233360402).
- Metlay JP, Waterer GW, Long AC, et al. Diagnosis and treatment of adults with community-acquired pneumonia. *Am J Respir Crit Care Med*. 2019;200:e45–e67. [ATS/IDSA guideline](https://www.idsociety.org/practice-guideline/community-acquired-pneumonia-cap-in-adults/). This guideline recommends PSI alongside judgment for hospitalization decisions and separate severe-CAP criteria for ICU decisions.

## License

MIT — see [LICENSE](LICENSE).

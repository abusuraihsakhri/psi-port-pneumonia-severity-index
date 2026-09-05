# PSI Port Pneumonia Severity Index

> **Domain:** Privacy-Preserving Healthcare & Federated Computing  
> **Reference Guidelines & Standards:** `HIPAA Safe Harbor §164.514 & Differential Privacy RDP`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

PSI/PORT Antibiotic Stewardship Linkage
Generates empiric antibiotic recommendations based on PSI risk class and
local resistance patterns for community-acquired pneumonia.

Author: Dr. Abu Suraih Sakhri | License: MIT

PSI/PORT Disposition Decision Support
Integrates PSI score with bed management logic for optimal patient placement:
floor vs. observation vs. ICU, with safety-net follow-up plans.

Author: Dr. Abu Suraih Sakhri | License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`ResistancePattern`**: Local antibiogram resistance data for empiric therapy guidance.
- **`AntibioticRecommendation`**: Structured antibiotic recommendation output.
- **`AntibioticStewardshipEngine`**: Maps PSI/PORT risk classes to IDSA/ATS guideline-concordant empiric
antibiotic regimens, adjusted for local resistance patterns.
- **`DispositionLevel`** — dedicated module for disposition level evaluation and state verification.
- **`BedAvailability`**: Current bed availability for disposition planning.
- **`DispositionDecision`**: Structured disposition decision output.

---

## 📐 Mathematical Formulation & Logic

### PSI/PORT Score Calculation

The Pneumonia Severity Index (PSI/PORT) assigns points based on demographics, comorbidities, physical examination findings, and laboratory/radiographic results:

```text
score = age_points + comorbidity_points + exam_points + lab_points

Where:
  - age_points: Age in years (males) or age - 10 (females)
  - nursing_home_resident: +10 points
  - neoplastic disease: +30 points
  - liver disease: +20 points
  - congestive heart failure: +10 points
  - cerebrovascular disease: +10 points
  - renal disease: +10 points
  - altered mental status: +20 points
  - respiratory rate ≥ 30/min: +20 points
  - systolic BP < 90 mmHg: +20 points
  - temperature < 35°C: +15 points
  - pulse ≥ 125/min: +10 points
  - arterial pH < 7.35: +30 points
  - BUN ≥ 30 mg/dL: +20 points
  - sodium < 130 mEq/L: +20 points
  - glucose ≥ 250 mg/dL: +10 points
  - hematocrit < 30%: +10 points
  - PaO2 < 60 mmHg: +10 points
  - pleural effusion: +10 points
```

### Risk Class Stratification

| Risk Class | Score Range | 30-Day Mortality | Recommended Disposition |
|:-----------|:------------|:-----------------|:------------------------|
| I | ≤ 0 (or age <50, no comorbidities) | 0.1% | Outpatient |
| II | ≤ 70 | 0.6% | Outpatient |
| III | 71-90 | 2.8% | Observation / Brief hospitalization |
| IV | 91-130 | 8.2% | Hospitalize |
| V | > 130 | 29.2% | ICU consideration |

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --task-id <value> --target <value> --primary <value> --secondary <value>
```

### Parameter Reference
- `--task-id`: Specifies input measurement or parameter value.
- `--target`: Specifies input measurement or parameter value.
- `--primary`: Specifies input measurement or parameter value.
- `--secondary`: Specifies input measurement or parameter value.
- `--critical`: Specifies input measurement or parameter value.
- `--status`: Specifies input measurement or parameter value.
- `--input`: Specifies input measurement or parameter value.
- `--output`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🚀 Installation

### Local Development

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/psi-port-pneumonia-severity-index.git
cd psi-port-pneumonia-severity-index

# Install dependencies
pip install -e ".[dev]"
```

### Docker Deployment

```bash
docker build -t psi-port-pneumonia-severity-index .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key psi-port-pneumonia-severity-index
```

Or using Docker Compose:

```bash
docker-compose up -d
```

---

## 🧪 Testing & Verification

Run the full automated test suite:

```bash
pytest -v
```

Run with coverage:

```bash
pytest -v --cov=agents --cov=parallel_score_comparison --cov=antibiotic_stewardship --cov=disposition_decision_support
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
docker build -t psi-port-pneumonia-severity-index .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key psi-port-pneumonia-severity-index
```

### Environment Variables

| Variable | Description | Default |
|:---------|:------------|:--------|
| `AUDIT_SECRET_KEY` | HMAC-SHA256 key for audit trail integrity | Randomly generated (ephemeral) |
| `MODEL_PROVIDER` | LLM provider for chat feature | `mock` |

> **Security Note:** Always set `AUDIT_SECRET_KEY` in production to ensure persistent audit trail integrity across restarts.

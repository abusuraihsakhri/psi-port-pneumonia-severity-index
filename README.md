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

```text
  score = 0
  elif score == 2:
  if score == 0:
  elif score == 1:
  score = primary_val
```

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

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t psi-port-pneumonia-severity-index .
docker run -p 8000:8000 psi-port-pneumonia-severity-index
```

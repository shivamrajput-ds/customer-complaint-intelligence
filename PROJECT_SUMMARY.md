# Customer Complaint Intelligence Platform — Project Summary

## 1. Project Overview

**Customer Complaint Intelligence Platform** is an end-to-end analytics and NLP project built on the CFPB Consumer Complaint dataset.

The project processes a large raw complaint dataset and converts it into:

- executive dashboard insights
- company risk scores
- complaint driver analysis
- product and issue growth signals
- complaint volume forecasting
- NLP-based Product and Issue classification
- topic modeling
- recommendation engine outputs

The goal is not only to show charts, but to build a practical decision-support system for understanding complaint patterns and operational risk.

---

## 2. Problem Statement

Consumer complaint data is difficult to use directly because it is large, messy, and operationally complex.

A basic dashboard can show complaint counts, but decision-makers usually need deeper answers:

- Which companies show higher complaint risk?
- Which products or issues are growing quickly?
- Which complaint categories may need operational attention?
- What complaint volume may look like in the near future?
- Can incoming complaint narratives be classified automatically?
- Can analytical outputs be converted into recommendations?

This project solves these problems through a modular analytics and NLP pipeline.

---

## 3. Dataset

| Item | Details |
|---|---|
| Dataset | CFPB Consumer Complaint Database |
| Total complaints | ~15.95M |
| Raw data size | ~8–9 GB CSV |
| Narrative availability | ~23.84% |
| Companies | ~7.97K |
| Products | 21 |
| States / territories | 64 |

Important note: Complaint volume should not be treated as a legal or regulatory conclusion by itself. A high complaint count may be affected by company size, customer base, product mix, and population.

---

## 4. What the System Does

### Module 1 — Executive Analytics

- Executive KPI dashboard
- Product-level analysis
- Issue-level analysis
- Company-level analysis
- Resolution and timeliness analysis
- State/geography analysis
- Consumer segment analysis
- Narrative availability and text insights

### Module 2 — Advanced Intelligence

- Company Risk Score
- Complaint Driver Analysis
- Product and Issue Growth Analysis
- Monthly complaint forecasting
- Executive recommendation inputs

### Module 3 — NLP Intelligence

- Product classification from complaint narratives
- Issue classification from complaint narratives
- LDA topic modeling
- Interactive complaint analyzer

### Module 4 — Recommendation Engine

The recommendation engine combines analytical signals such as company risk, growth trends, forecasts, and complaint drivers into prioritized action recommendations.

---

## 5. Architecture

```text
Raw CFPB CSV
15.95M complaints / 8–9 GB
        |
        v
Chunked Preprocessing
Validation + cleaning + feature engineering
        |
        v
Processed Parquet Outputs
        |
        v
Dashboard Aggregations
        |
        +--> Executive Analytics
        +--> Company Risk Scoring
        +--> Growth Analysis
        +--> Driver Analysis
        +--> Forecasting
        +--> NLP Classification
        +--> Topic Modeling
        |
        v
Recommendation Engine
        |
        v
Streamlit Dashboard
        |
        v
Docker Deployment
```

The dashboard reads pre-aggregated Parquet outputs instead of loading the full raw dataset at runtime. This keeps the Streamlit app faster and more memory-efficient.

---

## 6. Tech Stack

| Area | Tools |
|---|---|
| Language | Python |
| Data processing | Pandas, PyArrow, Parquet |
| Dashboard | Streamlit |
| Visualization | Plotly |
| Machine Learning | scikit-learn |
| NLP | TF-IDF, Logistic Regression, LDA |
| Forecasting | Prophet |
| Testing | pytest |
| Deployment | Docker, Docker Hub |
| CI/CD | GitHub Actions |
| Config | YAML-based configuration |

---

## 7. Key Results

| Metric | Result |
|---|---:|
| Product classifier accuracy | 75.28% |
| Issue classifier accuracy | 62.39% |
| Forecast validation MAPE | 3.57% |
| Forecast validation MAE | 17,748 |
| Unit tests | 14/14 passing |
| Timely response rate | 99.37% |
| Average resolution delay | 0.63 days |
| Narrative availability | 23.84% |

These results should be interpreted with the documented limitations. For example, NLP performance applies only to complaints with available narrative text.

---

## 8. Key Engineering Decisions

| Decision | Why It Was Used |
|---|---|
| Chunked preprocessing | To process a large raw CSV without memory failures |
| Parquet storage | Smaller storage and faster column-based reads |
| Pre-aggregated dashboard files | Keeps Streamlit responsive |
| TF-IDF + Logistic Regression | CPU-friendly, explainable, fast baseline |
| Prophet forecasting | Suitable for monthly trend and seasonality forecasting |
| Config-driven pipeline | Keeps thresholds and paths outside code |
| Docker deployment | Reproducible local and portfolio demo setup |
| GitHub Actions | Basic CI validation before changes reach main branch |

---

## 9. Why Not Deep Learning First?

A transformer model could be used, but this project prioritizes:

- CPU-friendly deployment
- faster training and inference
- lower memory usage
- reproducibility on a normal laptop
- easier explanation during interviews

TF-IDF + Logistic Regression is a practical baseline for this project because it gives reasonable performance while keeping the system deployable without GPU dependency.

---

## 10. Current Limitations

This project is intentionally honest about its limitations:

- Geographic complaint counts are not normalized per capita.
- Product and Issue predictions currently return only the top label.
- NLP confidence scores are not calibrated probabilities.
- Forecasting uses complaint volume only and does not include external economic or regulatory signals.
- Topic modeling uses LDA with manually interpreted topics.
- Some NLP training constants should be fully migrated to `config.yaml`.
- FastAPI serving layer is planned, not part of the current final version.

---

## 11. Future Improvements

The most useful future improvements are:

1. Add Top-3 Product and Issue predictions.
2. Add confidence-aware NLP outputs.
3. Add per-capita geographic normalization.
4. Add FastAPI model serving.
5. Add model metadata and versioning.
6. Add model drift monitoring.
7. Add stronger runtime and memory benchmarks.

---

## 12. Interview Pitch

This project processes a large real-world complaint dataset and turns it into a decision-support platform. I built it to go beyond basic charts by adding company risk scoring, growth detection, forecasting, NLP classification, topic modeling, and recommendations. The main engineering challenge was handling scale on a normal laptop, so I used chunked preprocessing, Parquet outputs, pre-aggregated dashboard files, and CPU-friendly NLP models. The result is a practical analytics + ML platform that is reproducible through Docker and documented for evaluation.

---

## 13. Repository Documents

| File | Purpose |
|---|---|
| `README.md` | Main project explanation and setup |
| `PROJECT_SUMMARY.md` | Short recruiter/interviewer overview |
| `docs/INTERVIEW_QA.md` | Interview preparation questions and answers |
| `docs/architecture.md` | System architecture and module flow |
| `docs/evaluation.md` | Model metrics and validation details |
| `docs/case_study.md` | Engineering journey and trade-offs |
| `docs/docker.md` | Docker build and deployment guide |
| `docs/data_dictionary.md` | Dataset columns and engineered features |
| `docs/runbook.md` | Operational commands |
| `docs/benchmark.md` | Performance and benchmark notes |
| `docs/adr.md` | Architecture decision records |

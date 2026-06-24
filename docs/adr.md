# Architecture Decision Records (ADR)

This file records the significant technical decisions made in the Customer Complaint Intelligence Platform.

Each entry documents:

* The decision made
* The context behind it
* Alternatives considered
* Why the chosen approach was selected
* Current status

These decisions reflect real trade-offs made during development, not retrofitted justifications.

---

## ADR-001: Use Parquet for Intermediate and Dashboard Storage

**Decision:** Store the processed dataset and dashboard summaries as Parquet instead of CSV.

**Context:**
The raw CFPB dataset is approximately 8-9 GB as CSV. Repeatedly reading CSV during development and pipeline execution is slow and memory-heavy. CSV also does not support efficient column pruning.

**Alternatives considered:**

* **CSV throughout the pipeline** — rejected because every downstream module would repeatedly parse large row-oriented files even when only a few columns were needed.
* **Pickle files** — rejected because they are Python-specific and less portable for analytics workflows.
* **Database-first storage** — not needed for this portfolio-scale batch pipeline.

**Decision outcome:**
Use Parquet for:

* `complaints_processed.parquet`
* Dashboard summary outputs
* Growth, forecast, risk, driver, and recommendation outputs

**Result:**
Raw CSV size was reduced from approximately 8-9 GB to about 1.3 GB as processed Parquet, with an approximate storage reduction of 85%.

**Status:** Implemented.

---

## ADR-002: Use TF-IDF + Logistic Regression Instead of Transformer Fine-Tuning

**Decision:** Use TF-IDF vectorization with Logistic Regression for Product and Issue classification.

**Context:**
The dataset contains approximately 3.8M complaint narratives. A transformer model could potentially improve accuracy but would increase training time, memory usage, inference latency, and Docker image size.

**Alternatives considered:**

* **BERT / RoBERTa fine-tuning** — rejected for this version because the deployment target is CPU-only and single-machine.
* **Zero-shot classification** — rejected because it would be slow and expensive for large-scale inference.
* **Classical ML with TF-IDF** — selected because it is fast, reproducible, and deployment-friendly.

**Decision outcome:**
Use:

```text
TF-IDF + Logistic Regression
```

with a small tuning grid over:

```text
C
class_weight
max_features
```

**Result:**

| Classifier         | Accuracy |
| ------------------ | -------: |
| Product classifier |   75.28% |
| Issue classifier   |   62.39% |

**Status:** Implemented.

---

## ADR-003: Do Not Add Generic Sentiment Analysis

**Decision:** Do not include sentiment analysis as a dashboard feature.

**Context:**
Complaint narratives are naturally negative because users submit them when something went wrong. Generic sentiment analysis would likely classify most complaints as negative and add little business value.

**Alternatives considered:**

* **VADER sentiment analysis** — rejected because output would likely be uniformly negative.
* **Pretrained sentiment classifier** — rejected for the same reason.
* **Complaint-specific classification** — preferred, because Product, Issue, and Topic predictions map more directly to operational decisions.

**Decision outcome:**
Skip sentiment analysis and focus NLP work on:

* Product classification
* Issue classification
* Topic modeling

**Status:** Implemented as a deliberate omission.

---

## ADR-004: Pre-Aggregate Dashboard Data Instead of Reading Full Dataset in Streamlit

**Decision:** Streamlit should read only pre-computed summary files, not the full processed dataset.

**Context:**
Streamlit re-runs the script on interactions. Reading or aggregating 15.95M rows inside the app would make the dashboard slow and unstable.

**Alternatives considered:**

* **Read full Parquet directly inside Streamlit** — rejected because first load and cache invalidation would still be expensive.
* **Use Streamlit cache only** — insufficient because caching does not remove the initial heavy computation.
* **Pre-compute dashboard summaries** — selected.

**Decision outcome:**
Create small Parquet summaries under:

```text
data/processed/dashboard/
```

The dashboard reads summary outputs such as:

```text
kpis.parquet
top_products.parquet
company_risk_score.parquet
product_growth.parquet
forecast_summary.parquet
recommendations.parquet
```

**Status:** Implemented.

---

## ADR-005: Keep NLP Training Separate from the Main Analytics Pipeline

**Decision:** Do not run NLP training inside `src/pipeline.py`.

**Context:**
NLP training over hundreds of thousands of narratives is slower and less frequently needed than analytics summary generation.

**Alternatives considered:**

* **Run NLP training every time the pipeline runs** — rejected because routine analytics refreshes would become unnecessarily slow.
* **Train models once and load saved artifacts** — selected.

**Decision outcome:**
Separate commands are used:

```bash
python -m src.create_narrative_training_data
python -m src.nlp_model_training
python -m src.nlp_tuning
```

The main analytics pipeline remains:

```bash
python -m src.pipeline
```

**Status:** Implemented.

---

## ADR-006: Use Config-Driven Design with `config.yaml`

**Decision:** Move thresholds, paths, forecasting settings, risk weights, and NLP parameters into `config.yaml`.

**Context:**
Hardcoded values make experiments and deployment changes harder. A config-driven design makes the pipeline easier to tune without editing source code.

**Alternatives considered:**

* **Hardcoded constants** — rejected for most modules because values like risk thresholds and sample sizes should be adjustable.
* **Environment variables only** — rejected because nested pipeline configuration is easier to manage in YAML.
* **Central YAML config** — selected.

**Decision outcome:**
Use:

```text
config.yaml
src/config_loader.py
```

Most modules now read settings through the centralized config.

**Known exception:**
`nlp_model_training.py` still contains some hardcoded constants and is tracked as known technical debt.

**Status:** Mostly implemented.

---

## ADR-007: Add Minimum Complaint-Count Floor to Company Risk Scoring

**Decision:** Exclude companies below a configurable minimum complaint-count threshold before risk scoring.

**Context:**
Small-sample companies can produce misleading percentages. For example, a company with 2 complaints and 1 late response would have a 50% untimely rate, but that does not necessarily indicate systemic risk.

**Alternatives considered:**

* **Score every company** — rejected because low-volume companies could dominate risk rankings due to noise.
* **Score all companies and hide low-volume results in the UI** — rejected because the scoring output itself would still contain misleading rankings.
* **Apply a minimum complaint-count floor before scoring** — selected.

**Decision outcome:**
Companies below the threshold are excluded before risk-score computation.

**Status:** Implemented.

---

## ADR-008: Use Custom Exceptions with File and Line Context

**Decision:** Wrap pipeline errors in a custom exception class that includes file and line information.

**Context:**
The project contains multiple pipeline modules. When chained together, raw exceptions can be difficult to trace back to the failing stage.

**Alternatives considered:**

* **Let raw exceptions propagate** — simpler but harder to debug in a multi-stage pipeline.
* **Use custom exception wrapper** — selected for clearer debugging.

**Decision outcome:**
Use:

```text
src/exception.py
```

for consistent error messages and debugging context.

**Status:** Implemented.

---

## ADR-009: Use Prophet for Monthly Complaint Forecasting

**Decision:** Use Prophet for monthly complaint-volume forecasting.

**Context:**
The forecasting problem is monthly complaint volume with trend and seasonality. The goal is not to build the most complex forecasting system, but to provide a reliable planning signal for dashboard users.

**Alternatives considered:**

* **Naive moving average** — simple but weaker for trend and seasonality.
* **ARIMA / SARIMA** — valid, but requires more stationarity and parameter handling.
* **XGBoost regression** — possible, but would require more manual feature engineering for time effects.
* **Prophet** — selected because it handles trend and seasonality well with minimal setup.

**Decision outcome:**
Use Prophet with a holdout-based validation strategy.

**Result:**

| Metric          |             Value |
| --------------- | ----------------: |
| Validation MAPE |             3.57% |
| Validation MAE  | 17,748 complaints |

**Status:** Implemented.

---

## ADR-010: Use a Rule-Based Recommendation Engine

**Decision:** Build a rule-based recommendation engine instead of a generative or ML-based recommender.

**Context:**
The goal is to convert risk, growth, forecast, and driver signals into executive recommendations. For this project, explainability is more important than model complexity.

**Alternatives considered:**

* **Generative recommendations with an LLM** — rejected because it would introduce dependency on external APIs and make outputs harder to reproduce.
* **ML-based recommendation model** — rejected because there is no labeled training data for "correct recommendation."
* **Rule-based recommendation logic** — selected because it is transparent and auditable.

**Decision outcome:**
The recommendation engine reads outputs from:

```text
risk_analysis.py
growth_analysis.py
driver_analysis.py
forecasting.py
```

and produces:

```text
recommendations.parquet
executive_action_plan.parquet
```

**Status:** Implemented.

---

## ADR-011: Use Docker for Reproducible Dashboard Deployment

**Decision:** Package the application as a Docker image.

**Context:**
The project needs to run consistently across environments without asking users to manually recreate the local Python setup.

**Alternatives considered:**

* **Local-only setup** — rejected because dependency mismatches are common.
* **Streamlit-only deployment** — useful for demo hosting, but does not capture the full local artifact environment.
* **Docker container** — selected for reproducibility and one-command startup.

**Decision outcome:**
The image bundles:

```text
app/
src/
config.yaml
.streamlit/
data/processed/dashboard/
models/nlp/
```

and excludes:

```text
data/raw/
large training intermediates
local environment files
```

**Status:** Implemented.

---

## ADR-012: Bundle Pre-Computed Artifacts in the Docker Image

**Decision:** Include processed dashboard artifacts and trained NLP models in the Docker image.

**Context:**
The Docker image is intended for one-command dashboard execution, not for running full preprocessing and model training from scratch inside the container.

**Alternatives considered:**

* **Generate all artifacts on container startup** — rejected because startup would become slow and require the raw 8-9 GB CSV.
* **Require user to mount artifacts manually** — rejected for portfolio usability.
* **Bundle pre-computed outputs** — selected.

**Decision outcome:**
The image includes:

```text
data/processed/dashboard/
models/nlp/
```

but excludes:

```text
data/raw/
complaints_processed.parquet
narratives_training.parquet
```

**Trade-off:**
The image is larger, but the dashboard works immediately after `docker run`.

**Status:** Implemented.

---

## ADR-013: Use GitHub Actions for CI Validation

**Decision:** Use GitHub Actions to run tests and validate Docker builds.

**Context:**
Manual local testing is easy to forget. CI provides an automated check that the project still installs, tests, and builds successfully after changes.

**Alternatives considered:**

* **Manual testing only** — rejected because it does not scale well and gives no public validation signal.
* **Full deployment pipeline** — not necessary for this portfolio project.
* **GitHub Actions for test + Docker build validation** — selected.

**Decision outcome:**
CI runs:

```text
pytest tests
docker build
```

on push / pull request.

**Status:** Implemented.

---

## ADR-014: Use Streamlit Instead of a Custom React Frontend

**Decision:** Use Streamlit as the dashboard frontend.

**Context:**
The project focuses on data engineering, analytics, NLP, forecasting, and MLOps-style deployment rather than frontend engineering.

**Alternatives considered:**

* **React frontend + FastAPI backend** — more flexible but much heavier and slower to build.
* **Dash** — valid option, but Streamlit was faster for rapid analytics dashboard development.
* **Streamlit** — selected for fast dashboard development and direct Python integration.

**Decision outcome:**
Use:

```text
app/streamlit_app.py
```

as the dashboard entry point.

**Status:** Implemented.

---

## ADR-015: Keep the Project Single-Machine Instead of Spark/Airflow

**Decision:** Use a single-machine Pandas/PyArrow/Parquet pipeline instead of Spark or Airflow.

**Context:**
The project runs on a consumer laptop and handles the target 15.95M-row dataset successfully with chunking and Parquet. Adding Spark or Airflow would increase operational complexity without being necessary for the current scale.

**Alternatives considered:**

* **Spark** — rejected because current data volume is manageable after optimization and does not require distributed execution.
* **Airflow** — rejected because the workflow is batch-oriented but simple enough to run through scripts and documented commands.
* **Single-machine modular pipeline** — selected.

**Decision outcome:**
Use modular Python scripts under `src/`, executed with:

```bash
python -m src.pipeline
```

**Status:** Implemented.

---

## Summary

The core architecture choices prioritize:

* Memory-safe processing
* Reproducible outputs
* CPU-only deployment
* Transparent modeling
* Fast dashboard interaction
* Dockerized execution
* Honest documentation of limitations

The result is a production-style portfolio system rather than a notebook-only analysis project.

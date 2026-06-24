# Architecture

## Overview

The platform is split into three layers:

1. **Pipeline layer** (`src/`) — batch jobs that read raw or processed data
   and write small, pre-aggregated Parquet outputs.
2. **Presentation layer** (`app/streamlit_app.py`) — reads only the
   pre-aggregated outputs, never the raw or fully processed dataset.
3. **Deployment layer** (Docker) — packages the presentation layer plus
   already-computed artifacts (processed dashboard data, trained NLP
   models) for one-command startup.

This separation exists specifically so the dashboard stays fast and
memory-light regardless of how large the underlying dataset is — the
expensive work happens once, offline, in the pipeline layer.

---

## End-to-End Flow

```
data/raw/complaints.csv  (8-9 GB, 15.95M rows)
        │
        ▼
src/preprocessing.py
  - chunked CSV read (configurable chunksize)
  - column validation
  - missing-value handling
  - date parsing + feature engineering (Year/Month/Quarter/Day/Day_Name)
  - duplicate removal (by Complaint ID)
        │
        ▼
data/processed/complaints_processed.parquet  (~1.3 GB)
        │
        ├──────────────► src/dashboard_data.py ──► data/processed/dashboard/*.parquet
        │                  (KPIs, product/issue/company breakdowns,
        │                   narrative stats, geography — Module 1)
        │
        ├──────────────► src/risk_analysis.py ──► company_risk_score.parquet
        │                  (Module 2: Risk Intelligence)
        │
        ├──────────────► src/driver_analysis.py ──► driver_analysis.parquet,
        │                  (Module 2: Driver Analysis)   top_complaint_drivers.parquet,
        │                                               product_driver_summary.parquet
        │
        └──────────────► src/growth_analysis.py ──► product_growth.parquet,
                           (Module 2: Growth Analysis)   issue_growth.parquet,
                                                          monthly_complaint_trend.parquet
                                    │
                                    ▼
                           src/forecasting.py ──► complaint_forecast.parquet,
                           (Module 2: Forecasting)   forecast_summary.parquet
                                    │
                                    ▼
                       src/recommendation_engine.py ──► recommendations.parquet,
                       (Module 4)                        executive_action_plan.parquet
                                    │
                                    ▼
                         app/streamlit_app.py
                         (reads only data/processed/dashboard/*.parquet)


  ── Separate, occasional process (not part of the above pipeline) ──

data/processed/complaints_processed.parquet
        │
        ▼
src/create_narrative_training_data.py ──► narratives_training.parquet
        │
        ▼
src/nlp_tuning.py  (small hyperparameter grid search)
        │            or
src/nlp_model_training.py  (fixed-hyperparameter training)
        │
        ▼
models/nlp/*.pkl  (product/issue classifiers, LDA topic model)
        │
        ▼
src/nlp_predictor.py  (loaded by the Streamlit app for live predictions)
```

---

## Module Dependency Order

`src/pipeline.py` runs the analytics modules in a fixed sequence, but
that sequence is not a real dependency chain end-to-end — only some
stages actually depend on another stage's output. Collapsing this into
a single top-to-bottom arrow would overstate how coupled the modules
are, so the independent and dependent jobs are shown separately below.

**Independent jobs** (each reads `complaints_processed.parquet`
directly and could run in any order relative to each other):

```
config_loader
     │
     ├──► dashboard_data
     ├──► risk_analysis
     ├──► driver_analysis
     └──► growth_analysis
```

**Dependent jobs** (each requires a specific upstream output to exist
first):

```
growth_analysis ──► monthly_complaint_trend.parquet ──► forecasting

risk_analysis ─────┐
growth_analysis ────┼──► recommendation_engine
forecasting ────────┤    (needs Risk, Growth, Forecast, AND Driver
driver_analysis ────┘     outputs all present)
```

`pipeline.py` happens to call all of these in one fixed order
(`dashboard_data → risk_analysis → driver_analysis → growth_analysis →
forecasting → recommendation_engine`) for simplicity, but only the
`forecasting` and `recommendation_engine` orderings are load-bearing —
the first four could run in any relative order without breaking
anything.

`forecasting.py` and `recommendation_engine.py` both check for their
required input files at the start and raise a clear `FileNotFoundError` if
an upstream stage hasn't run yet, rather than failing with an obscure
`pandas` error mid-computation.

---

## Why `pipeline.py` Excludes NLP Training

`pipeline.py` intentionally does not call
`create_narrative_training_data.py`, `nlp_model_training.py`, or
`nlp_tuning.py`. NLP training runs over up to 300K sampled narratives
(configurable) and takes meaningfully longer than the rest of the
pipeline combined. Running it on every dashboard data refresh would be
wasteful — the trained models change rarely, while the dashboard's
analytics (risk scores, growth, forecasts) should refresh whenever new
complaint data arrives.

In practice this means: run `pipeline.py` regularly (e.g. whenever new
raw data lands), and run the NLP training scripts only when you actually
want to retrain the classifiers — see [`runbook.md`](runbook.md).

**Operational note:** `nlp_model_training.py` and `nlp_tuning.py` both
write to the same output filenames in `models/nlp/`
(`product_classifier_model.pkl`, `issue_classifier_model.pkl`, etc.). Only
run one of them per training cycle — whichever runs last overwrites the
other's output. `nlp_tuning.py` is the more complete version (it searches
a small hyperparameter grid and keeps the best result); `nlp_model_training.py`
trains with fixed hyperparameters and additionally produces the LDA topic
model, which `nlp_tuning.py` does not.

---

## Presentation Layer

`app/streamlit_app.py` never reads `complaints_processed.parquet` or the
raw CSV directly. Every tab in the dashboard is backed by a small,
pre-aggregated Parquet file under `data/processed/dashboard/`, loaded via
a cached `load_summary()` function. This is what keeps dashboard load
times independent of the underlying 15.95M-row dataset size.

---

## Cross-Cutting Layers

Three utilities are used by every module in the pipeline, rather than
belonging to any single stage:

### Configuration Layer

```
config.yaml
     │
     ▼
config_loader.py  (loads once, validates non-empty, fails fast if missing)
     │
     ▼
Every module in src/  (except nlp_model_training.py — see ADR-006)
```

Risk thresholds, growth-rate thresholds, forecast settings, NLP sample
sizes, and dashboard summary parameters all live in `config.yaml`
rather than as hardcoded constants. This means a threshold like the
minimum complaint count for risk scoring can be changed by editing one
YAML value, with no code change required. Full reasoning: `adr.md`
(ADR-006).

### Testing Layer

```
tests/
  └── pytest discovers and runs all test_*.py files
```

The test suite covers core utility functions — configuration loading,
custom exception formatting, the safe year-over-year growth calculation
(including the zero-previous-year edge case), risk-score min-max
scaling, and MAPE calculation. 14/14 tests currently pass. These are
unit tests against individual functions, not integration tests against
a full pipeline run — see `evaluation.md` → Unit Tests for what this
does and doesn't cover.

### Logging Layer

`src/logger.py` provides a single shared logger
(`customer_complaint_intelligence`) used across every module. It writes
to two destinations at once:
- **Console** (`StreamHandler`) — for live feedback while a script runs
- **Rotating file** (`RotatingFileHandler`, `logs/app.log`) — capped at
  10 MB per file with 5 backups kept, so log files don't grow without
  bound on a long-running or frequently-rerun pipeline

Every pipeline stage logs its start, key intermediate counts (e.g. rows
processed, companies kept after filtering), and completion, so a failed
run can be traced back to exactly which stage and which step failed.

### Exception Handling Layer

`src/exception.py` defines `CustomException`, which every module's
top-level function uses to wrap and re-raise errors. Rather than letting
a raw `pandas` or `sklearn` exception propagate with a generic Python
traceback, `CustomException` captures the originating file name and line
number at the point of failure and attaches the original error message,
so a failure in a long pipeline chain (`pipeline.py` running six
modules in sequence) is immediately traceable to its source. See
`adr.md` (ADR-008) for the reasoning behind this pattern.

### Memory Optimization Strategy

The pipeline relies on a small set of repeated techniques to stay
within consumer-hardware memory limits, rather than one single trick:

- **Chunked CSV ingestion** (`preprocessing.py`) — the raw 8-9 GB CSV
  is read in configurable-size chunks, never loaded whole into memory.
- **Column pruning** — every downstream module
  (`risk_analysis.py`, `growth_analysis.py`, `driver_analysis.py`)
  reads only the specific columns it needs from the processed Parquet
  file via `pd.read_parquet(..., columns=[...])`, rather than loading
  every column.
- **PyArrow dataset scanning** (`create_narrative_training_data.py`) —
  uses a batch-wise Arrow scanner with a filter pushed down to the
  storage layer, instead of loading the full processed dataset into a
  single Pandas DataFrame before filtering.
- **Bounded sampling for NLP** — NLP training samples a configurable,
  capped subset of narratives (default up to 300,000) rather than
  vectorizing all ~3.8M available narratives at once.
- **Dashboard pre-aggregation** — the most impactful technique
  architecturally: by computing summaries once in the pipeline layer,
  the presentation layer never needs to hold the full dataset in memory
  at all. See ADR-004.

---

## Deployment Layer

The Docker image bundles:
- The Streamlit app (`app/`)
- The pipeline source (`src/`)
- `config.yaml`
- Already-computed dashboard Parquet files (`data/processed/`)
- Already-trained NLP models (`models/nlp/`)

It deliberately excludes the raw dataset (`data/raw/`) — the image is
meant for running the dashboard against pre-computed artifacts, not for
re-running the full pipeline from scratch inside the container. Full
details: [`docker.md`](docker.md).

**Why the image is larger than a typical Streamlit app image:** it
intentionally includes the processed dashboard artifacts and trained
NLP model files, so a single `docker run` produces a fully working
dashboard without requiring the user to first run the preprocessing
pipeline or train any models themselves. This trades image size for
one-command deployability.

**Data handling note:** the raw CFPB CSV is excluded from both the
Docker image and the Git repository (see `.dockerignore` and
`.gitignore`). The container only ever serves already-processed
aggregates and already-trained models — it does not read or store raw
complaint-level data with personally identifiable fields at runtime.
The CFPB dataset itself redacts most direct identifiers in the source
narrative text (e.g. names and account numbers appear as `XXXX`), but
this project does not perform its own additional PII-scrubbing pass
beyond what CFPB already does.
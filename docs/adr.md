# Architecture Decision Records (ADR)

This file records the significant technical decisions made on this
project, the alternatives that were actually considered, and why each
decision was made. Each entry reflects a real choice made during
development — not a retrofitted justification.

---

## ADR-001: Parquet for All Intermediate Storage

**Decision:** Store the processed dataset and every dashboard summary as
Parquet, not CSV.

**Context:** The raw dataset is 8-9 GB as CSV. Repeatedly reading and
writing CSV during development and at pipeline runtime is slow and
doesn't support column pruning.

**Alternatives considered:**
- Keep using CSV throughout — rejected, since every downstream module
  would need to parse the full row width even when it only needs 2-3
  columns, and file size would stay close to 8-9 GB at every stage.

**Decision:** Parquet. Columnar storage allows each module
(`risk_analysis.py`, `growth_analysis.py`, etc.) to read only the
columns it needs, and the processed dataset shrinks from ~9 GB to
~1.3 GB.

**Status:** Implemented.

---

## ADR-002: TF-IDF + Logistic Regression Instead of a Transformer Model

**Decision:** Use TF-IDF vectorization with a tuned Logistic Regression
classifier for Product and Issue prediction, instead of fine-tuning a
transformer model (e.g. BERT).

**Context:** ~3.8M complaint narratives are available for training.
The deployment target is CPU-only, single-machine, Docker-packaged.

**Alternatives considered:**
- **Transformer fine-tuning** — would likely improve accuracy, but at
  meaningfully higher training time, RAM usage, and Docker image size,
  and would require either a GPU or substantially longer CPU training
  time. Rejected for this project's deployment constraints.

**Decision:** TF-IDF + Logistic Regression, with hyperparameters
(`C`, `class_weight`, `max_features`) tuned via a small fixed grid in
`nlp_tuning.py`.

**Result:** 75.28% Product accuracy, 62.39% Issue accuracy, fast
CPU-only inference.

**Status:** Implemented. Revisiting this decision (i.e. trying a
transformer-based approach) is listed as a known limitation, not ruled
out permanently — see `README.md` → Known Limitations.

---

## ADR-003: No Sentiment Analysis

**Decision:** Do not include a sentiment-analysis feature on complaint
narratives.

**Context:** Complaint narratives are, by definition, written because
something went wrong — the dataset is structurally skewed toward
negative sentiment regardless of complaint severity or business
relevance.

**Alternatives considered:**
- **Generic sentiment scoring** (e.g. VADER, a pretrained sentiment
  classifier) — tested conceptually and rejected, since it would
  overwhelmingly return "Negative" across the corpus and provide little
  signal to distinguish a routine complaint from a severe one.

**Decision:** Skip sentiment analysis. Focus NLP effort on Product/Issue
classification and topic modeling, which map more directly to an
operational action.

**Status:** Implemented (i.e., deliberately not built).

---

## ADR-004: Pre-Aggregated Dashboard Summaries Instead of Direct Dataset Reads

**Decision:** `app/streamlit_app.py` never reads
`complaints_processed.parquet` directly. Every tab is backed by a small,
pre-computed Parquet summary file.

**Context:** Streamlit re-runs the script on every user interaction. If
each interaction triggered a read and aggregation over 15.95M rows, the
dashboard would be unusably slow.

**Alternatives considered:**
- **Read the full processed dataset and aggregate on the fly inside
  Streamlit**, relying on `@st.cache_data` to avoid repeated reads —
  rejected, since the *first* load (and any cache invalidation) would
  still require processing the full dataset, and every new dashboard
  feature would add more repeated work inside the app itself rather
  than in a controlled batch step.

**Decision:** A dedicated aggregation layer (`dashboard_data.py` plus
the Module 2/4 scripts) computes every summary the dashboard needs
ahead of time, as part of `pipeline.py`.

**Status:** Implemented.

---

## ADR-005: NLP Training Kept Separate from the Main Pipeline

**Decision:** `pipeline.py` does not call
`create_narrative_training_data.py`, `nlp_model_training.py`, or
`nlp_tuning.py`.

**Context:** NLP training operates on up to 300,000 sampled narratives
and takes meaningfully longer than the rest of the analytics pipeline
combined. The trained models don't need to change every time new
complaint data arrives.

**Alternatives considered:**
- **Include NLP training in `pipeline.py`** — rejected, since it would
  make every routine data refresh (which should be fast) as slow as the
  least frequent operation (full retraining).

**Decision:** Treat NLP training as a separate, manually-triggered
process (see `runbook.md`), distinct from the regularly-run analytics
pipeline.

**Status:** Implemented. See `architecture.md` for the operational note
on `nlp_model_training.py` and `nlp_tuning.py` overwriting the same
output files — only one should be run per training cycle.

---

## ADR-006: Configuration-Driven Design via `config.yaml`

**Decision:** Externalize thresholds, paths, and model parameters
(risk-score weights, growth thresholds, forecast settings, NLP
parameters) into `config.yaml`, loaded once via `config_loader.py`.

**Context:** Early versions of several modules (e.g. `risk_analysis.py`,
`growth_analysis.py`) had these values hardcoded as module-level
constants.

**Alternatives considered:**
- **Keep hardcoded constants** — rejected, since changing a single
  threshold (e.g. the minimum complaint count for risk scoring) would
  require a code change and redeploy rather than a config edit.

**Decision:** Centralize configuration in `config.yaml`. Every module
except `nlp_model_training.py` now reads its settings from `config`
rather than hardcoding them.

**Status:** Mostly implemented. `nlp_model_training.py` is a known,
tracked exception — see `README.md` → Known Limitations.

---

## ADR-007: Minimum Complaint-Count Floor for Company Risk Scoring

**Decision:** Companies with fewer than `risk.min_company_complaints`
total complaints (configurable, see `config_reference.md`) are excluded
from risk scoring entirely.

**Context:** Without a floor, a company with e.g. 2 total complaints
where 1 was late would show a 50% untimely-response rate — a number
driven entirely by sample-size noise, not a real pattern — and could
outrank a company with tens of thousands of complaints and a genuinely
low (but nonzero) untimely-response rate.

**Alternatives considered:**
- **Score every company regardless of volume** — this was the original
  implementation, and was identified as a flaw: small-sample companies
  could dominate the "High Risk" list for statistically meaningless
  reasons.

**Decision:** Apply a minimum complaint-count floor before scoring.
Companies below the floor are excluded from the output entirely, rather
than scored and then hidden, so the exclusion is auditable from the row
count alone.

**Status:** Implemented.

---

## ADR-008: Custom Exception Class with File/Line Context

**Decision:** Wrap exceptions across the pipeline in a `CustomException`
class that captures the originating file name and line number, instead
of letting raw exceptions propagate.

**Context:** With many modules chained together in `pipeline.py`, a
generic stack trace from deep inside a `pandas` operation can be hard
to map back to which pipeline stage actually failed.

**Alternatives considered:**
- **Let exceptions propagate as-is** — simpler, but loses the
  consistent "which module, which line, what message" framing across
  the whole codebase.

**Decision:** Every module's top-level function catches exceptions,
logs them via the shared `logger`, and re-raises as `CustomException`.

**Status:** Implemented.
# Runbook

Step-by-step operational commands for running every part of this
platform. All commands assume you're in the project root with the
virtual environment activated.

---

## 1. First-Time Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Place the raw CFPB CSV at the path configured in `config.yaml` under
`paths.raw_data_path` (default: `data/raw/complaints.csv`).

---

## 2. Preprocessing (Run Once Per Raw Data Update)

```bash
python -m src.preprocessing
```

**What it does:** reads the raw CSV in chunks (size controlled by
`preprocessing.chunksize` in `config.yaml`), validates required columns,
handles missing values, parses dates, engineers features, removes
duplicate complaints by `Complaint ID`, and writes
`data/processed/complaints_processed.parquet`.

**When to run:** whenever the raw CSV changes or this is the first run.

**Expected failure modes:**
- `FileNotFoundError` — raw CSV not at the configured path.
- `ValueError: Missing required columns` — the CSV schema doesn't match
  `REQUIRED_COLUMNS` in `preprocessing.py`.

---

## 3. Run the Full Analytics Pipeline

```bash
python -m src.pipeline
```

**What it does:** runs, in order, `dashboard_data.py` →
`risk_analysis.py` → `driver_analysis.py` → `growth_analysis.py` →
`forecasting.py` → `recommendation_engine.py`. Writes all Parquet
outputs to `data/processed/dashboard/`.

**When to run:** after preprocessing, and any time you want the
dashboard's analytics (risk scores, growth, forecasts, recommendations)
to reflect the latest processed data.

**Expected failure modes:**
- `FileNotFoundError: Processed data not found` — run step 2 first.
- `FileNotFoundError: Monthly trend file not found` — `forecasting.py`
  depends on `growth_analysis.py`'s output; this shouldn't happen if
  you ran `pipeline.py` as a whole, but can happen if you try to run
  `forecasting.py` standalone before `growth_analysis.py`.

**Note:** this command does **not** train or retrain NLP models — see
step 5.

---

## 4. Run Individual Pipeline Stages (Optional)

Each stage can also be run standalone, useful for debugging a single
module without re-running everything:

```bash
python -m src.dashboard_data
python -m src.risk_analysis
python -m src.driver_analysis
python -m src.growth_analysis
python -m src.forecasting          # requires growth_analysis output
python -m src.recommendation_engine # requires risk/growth/forecast/driver outputs
```

---

## 5. Train / Retrain NLP Models

This is a **separate** process from the main pipeline (see
`architecture.md` for why). Run it only when you want to (re)train the
Product/Issue classifiers and topic model.

### Step 5a: Build the narrative training dataset

```bash
python -m src.create_narrative_training_data
```

Reads `complaints_processed.parquet` via a PyArrow scanner, keeps only
rows with a valid narrative, Product, and Issue, and writes
`data/processed/narratives_training.parquet`.

### Step 5b: Train with fixed hyperparameters

```bash
python -m src.nlp_model_training
```

Trains the Product classifier, Issue classifier, and LDA topic model
using fixed hyperparameters, and saves all artifacts to `models/nlp/`.

### Step 5c — Alternative to 5b: Hyperparameter tuning

```bash
python -m src.nlp_tuning
```

Searches a fixed 6-combination grid (`C`, `class_weight`, `max_features`)
for the Product and Issue classifiers and saves the best model found.
**Does not** train the topic model.

> **Important:** Steps 5b and 5c both write to the same output
> filenames in `models/nlp/` (e.g. `product_classifier_model.pkl`).
> Run only one of them per training cycle — whichever you run last is
> what `nlp_predictor.py` will load. If you want both the tuned
> classifiers *and* the topic model, run `nlp_tuning.py` first, then
> run only the topic-modeling portion — see `architecture.md` for
> details on this overlap.

---

## 6. Launch the Dashboard

```bash
streamlit run app/streamlit_app.py
```

Opens at `http://localhost:8501`. Requires the Parquet outputs from
step 3 (and trained NLP models from step 5, for the NLP Prediction tab)
to already exist.

---

## 7. Run Tests

```bash
pytest
```

Runs the test suite covering core utility functions (config loading,
exception handling, growth-rate calculation, risk-score scaling, MAPE
calculation).

---

## 8. Docker

### Build

```bash
docker build -t customer-complaint-intelligence:v1 .
```

### Run

```bash
docker run -p 8501:8501 customer-complaint-intelligence:v1
```

### Pull pre-built image

Docker Hub: [hub.docker.com/repository/docker/shivamrajput130/customer-complaint-intelligence](https://hub.docker.com/repository/docker/shivamrajput130/customer-complaint-intelligence)

```bash
docker pull shivamrajput130/customer-complaint-intelligence:latest
docker run -p 8501:8501 shivamrajput130/customer-complaint-intelligence:latest
```

### Verify container is running

```bash
docker ps
docker logs -f customer-complaint-intelligence
```

Full Docker troubleshooting: see `docker.md`.

---

## Recovery Guide

What to do when a stage fails, based on the actual errors each module
raises.

### Pipeline (`python -m src.pipeline`) fails

`pipeline.py` wraps every stage in `CustomException`, so the console
output will show which underlying error occurred and at what file/line.
Common cases:

| Error | Cause | Recovery |
|---|---|---|
| `FileNotFoundError: Processed data not found` | Step 2 (preprocessing) hasn't been run, or ran but didn't write to the configured path | Run `python -m src.preprocessing`, then re-run `python -m src.pipeline` |
| `FileNotFoundError: Monthly trend file not found` | `forecasting.py` ran before `growth_analysis.py` produced `monthly_complaint_trend.parquet` | Shouldn't happen via `pipeline.py` (correct order is built in) — if running stages individually, run `growth_analysis.py` first |
| `ValueError: Processed complaints dataset is empty` | `complaints_processed.parquet` exists but has 0 rows — likely every chunk failed `validate_columns()` during preprocessing | Re-check the raw CSV's column headers against `REQUIRED_COLUMNS` in `preprocessing.py` |
| `FileNotFoundError: Required file not found` (from `recommendation_engine.py`) | One of the upstream outputs (risk, growth, forecast, or driver) is missing | Run the full pipeline in order rather than `recommendation_engine.py` alone |

### NLP training fails

| Error | Cause | Recovery |
|---|---|---|
| `FileNotFoundError: Processed data not found` (from `create_narrative_training_data.py`) | Preprocessing hasn't been run | Run `python -m src.preprocessing` first |
| `ValueError: No valid narrative rows found for NLP training` | The processed dataset has rows, but none have a non-null narrative *and* Product *and* Issue simultaneously | Check `Has_Narrative` / narrative availability stats in the dashboard; if availability is genuinely near-zero, this may indicate a preprocessing issue upstream |
| `ValueError: Not enough classes` (from `nlp_tuning.py`) | After dropping classes with fewer than 50 samples, fewer than 2 classes remain for the target column | Usually means the sampled subset (`TUNING_SAMPLE_SIZE` in `config.yaml`) is too small relative to the number of classes — increase the sample size |
| Model loads with stale/wrong predictions in the dashboard | `nlp_model_training.py` and `nlp_tuning.py` write to the same filenames — whichever ran most recently is what's currently loaded | Re-run whichever training script you intended to be the source of truth; see `architecture.md` for the overlap explanation |

### Docker fails

| Error | Cause | Recovery |
|---|---|---|
| `Bind for 0.0.0.0:8501 failed: port is already allocated` | Another process (or another container) already bound to host port 8501 | Run with a different host port: `docker run -p 8502:8501 ...` |
| Container exits immediately / NLP model loading error in logs | `numpy`/`scikit-learn`/`joblib` version mismatch between the environment that pickled the models and the one installed in the image | Pin versions in `requirements.txt` to match the training environment, then rebuild |
| Dashboard loads but shows "Summary file not found" errors | The image was built before the pipeline was run, so `data/processed/dashboard/*.parquet` files don't exist inside the image | Run `python -m src.preprocessing && python -m src.pipeline` locally first, then rebuild the image so the artifacts get copied in |
| Streamlit loads with default (non-dark) theme | `.streamlit/config.toml` is missing from the image, or was placed at the project root instead of inside `.streamlit/` | Confirm the file exists at `.streamlit/config.toml` exactly, then rebuild |

---

## Typical End-to-End Sequence (Fresh Setup)

```bash
# 1. Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Process raw data
python -m src.preprocessing

# 3. Run analytics pipeline
python -m src.pipeline

# 4. Train NLP models (one-time, or whenever retraining is needed)
python -m src.create_narrative_training_data
python -m src.nlp_tuning

# 5. Launch dashboard
streamlit run app/streamlit_app.py
```
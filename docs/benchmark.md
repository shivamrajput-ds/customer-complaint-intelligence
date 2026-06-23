# Benchmark

This document tracks measured performance numbers for the platform.
Where a number hasn't actually been measured yet, it's marked as such
rather than estimated — the goal is for every figure here to be
something you could re-verify by running the corresponding command.

---

## Storage Optimization

| Stage | Size | Measured By |
|---|---|---|
| Raw CSV | 8-9 GB | File size on disk |
| Processed Parquet (`complaints_processed.parquet`) | ~1.3 GB | File size on disk |
| Reduction | ~85% | (1 − 1.3/9) |

---

## Model Accuracy (from `evaluation.md`)

| Model | Metric | Value |
|---|---|---|
| Product classifier | Accuracy | 75.28% |
| Issue classifier | Accuracy | 62.39% |
| Forecast (Prophet) | Validation MAPE | 3.57% |
| Forecast (Prophet) | Validation MAE | 17,748 complaints |

---

## Dataset Scale

| Metric | Value |
|---|---|
| Total complaints processed | 15.95M |
| Narratives available for NLP | ~3.8M (23.84%) |
| Narratives sampled for NLP training | up to 300,000 (configurable via `config.yaml`) |
| Narratives sampled for hyperparameter tuning | up to 100,000 (configurable via `config.yaml`) |

---

## Testing

| Metric | Value |
|---|---|
| Unit tests | 14/14 passing |

---

## Not Yet Measured

The following are reasonable things to benchmark but have **not**
actually been measured and timed yet. They're listed here explicitly so
this file doesn't imply more rigor than currently exists:

- Preprocessing wall-clock time (raw CSV → processed Parquet) for the
  full 15.95M-row dataset
- `pipeline.py` end-to-end wall-clock time
- NLP training time (`nlp_model_training.py` / `nlp_tuning.py`) on the
  configured sample size
- Streamlit dashboard cold-start time and per-tab render time
- Single-prediction inference latency for `analyze_complaint()`
  (product, issue, and topic prediction combined)
- Docker image size and container cold-start time
- Peak RAM usage during preprocessing and during NLP training

### Ready-to-Run Measurement Snippets

Rather than guessing at these numbers, here's exactly how to produce
real ones. Each snippet can be dropped into the relevant script's
`if __name__ == "__main__":` block or run from a notebook.

**Pipeline / preprocessing wall-clock time:**

```python
import time

start = time.perf_counter()
preprocess_data()  # or build_forecast(), run_pipeline(), etc.
elapsed = time.perf_counter() - start
print(f"Elapsed: {elapsed:.2f} seconds")
```

**Single-prediction inference latency:**

```python
import time
from src.nlp_predictor import analyze_complaint

sample_text = "Someone opened fraudulent accounts in my name..."

start = time.perf_counter()
result = analyze_complaint(sample_text)
elapsed_ms = (time.perf_counter() - start) * 1000
print(f"Inference latency: {elapsed_ms:.1f} ms")
```

For a more representative number, wrap this in a loop over 50-100
sample texts and report the mean and p95, since a single call includes
one-time costs (e.g. first-call overhead) that a single measurement
would overstate.

**Peak RAM usage (requires `pip install memory-profiler`):**

```bash
python -m memory_profiler src/preprocessing.py
```

Or, for a running process, watch RSS directly:

```bash
# while the pipeline is running, in a separate terminal:
ps -o pid,rss,command -p <pid>
```

**Docker image size:**

```bash
docker images customer-complaint-intelligence:v1
```

**Container cold-start time:**

```bash
time docker run --rm -d -p 8501:8501 customer-complaint-intelligence:v1
# then poll http://localhost:8501 until it responds, and note the gap
```

Once these are run, this file should be updated to move each metric
from "Not Yet Measured" into a proper results table above, with the
exact command used noted alongside the number — the same pattern
already used for Storage Optimization and Model Accuracy below.

This section is intentionally left as a how-to rather than filled with
placeholder numbers, since a fabricated benchmark is worse than an
acknowledged gap.
# Changelog

All notable changes to this project are documented in this file.

---

## [1.2.0] — Tuned NLP Pipeline, Recommendation Engine, Docker Deployment

### Added
- NLP hyperparameter tuning pipeline (`nlp_tuning.py`) with a fixed 6-combination
  parameter grid over `C`, `class_weight`, and `max_features`
- Tuned Product classifier and Issue classifier
- Recommendation Engine (`recommendation_engine.py`) — converts risk, growth,
  forecast, and driver signals into prioritized recommendations
- Executive Action Plan output
- Pytest test suite covering core utility functions
- Docker Hub deployment
- Streamlit custom dark theme (`.streamlit/config.toml`)
- Minimum complaint-count floor in company risk scoring, to prevent
  low-volume companies from appearing in "High Risk" based on a
  statistically noisy small sample
- "New / Emerging" growth label for products/issues with zero complaints
  in the prior year (previously misleadingly labeled "Stable")
- Forecast validation (holdout-based MAE / MAPE), in addition to the
  point forecast

### Changed
- Product classifier updated to best found parameters:
  `C=2.0`, `class_weight=None`, `max_features=20000`
- Issue classifier updated to best found parameters:
  `C=2.0`, `class_weight=None`, `max_features=20000`
- All path, threshold, and parameter values migrated from hardcoded
  constants to `config.yaml`, read via `config_loader.py` — with the
  exception of `nlp_model_training.py`, which still uses hardcoded
  constants (tracked as known debt, see `README.md` → Known Limitations)

### Results
- Product classifier accuracy: 75.28%
- Issue classifier accuracy: 62.39%
- Forecast validation MAPE: 3.57%
- Forecast validation MAE: 17,748
- Unit tests: 14/14 passed

### Breaking Changes
None.

---

## [1.1.0] — Prophet Forecasting & Driver Analytics

### Added
- Prophet-based monthly complaint volume forecasting
- Next-month, next-3-month, and next-6-month forecast figures
- Forecast validation using a 6-month holdout window (MAE, MAPE)
- Complaint driver analysis (Product → Issue → Sub-issue)
- Product driver summary
- Growth analysis (year-over-year, product and issue level)
- Executive Risk Dashboard tab

### Results
- Forecast validation MAPE: 3.57%
- Forecast validation MAE: 17,748

### Breaking Changes
None.

---

## [1.0.0] — Initial Ingestion, EDA & Parquet Optimization

### Added
- Chunk-based raw CSV preprocessing
- Required-column validation
- Missing-value handling
- Date-based feature engineering (Year, Month, Quarter, Day, Day_Name)
- Duplicate complaint removal (by Complaint ID)
- Parquet storage for all processed and intermediate data
- Dashboard summary generation (Module 1)
- Product, Issue, Company, Geography, Resolution, and Narrative
  intelligence tabs

### Engineering Notes
- Raw data size: 8-9 GB CSV, 15.95M rows
- Processed data stored in Parquet (~1.3 GB)
- Streamlit reads pre-aggregated summary files rather than the full
  processed dataset

### Breaking Changes
None.

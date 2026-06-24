# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog principles and follows semantic versioning.

---

# [v1.2.0] - 2026-06-24

## Tuned NLP Pipeline, Recommendation Engine, Docker & CI/CD

### Added

* NLP hyperparameter tuning pipeline (`nlp_tuning.py`)
* Fixed 6-combination search grid over:

  * `C`
  * `class_weight`
  * `max_features`
* Tuned Product classifier
* Tuned Issue classifier
* Recommendation Engine (`recommendation_engine.py`)
* Executive Action Plan output
* GitHub Actions CI pipeline
* Automated Docker build validation
* Docker Hub deployment
* Streamlit custom dark theme (`.streamlit/config.toml`)
* Pytest test suite covering core utility functions
* Forecast validation using holdout-based MAE and MAPE metrics
* Minimum complaint-count floor in company risk scoring
* "New / Emerging" growth label for products and issues with zero complaints in the prior year

### Changed

* Product classifier updated to best-performing parameters:

  * `C=2.0`
  * `class_weight=None`
  * `max_features=20000`

* Issue classifier updated to best-performing parameters:

  * `C=2.0`
  * `class_weight=None`
  * `max_features=20000`

* Configuration migrated from hardcoded constants to `config.yaml`

* Centralized configuration loading via `config_loader.py`

* Improved recommendation prioritization logic

* Improved growth classification logic

### Results

* Product Classifier Accuracy: **75.28%**
* Issue Classifier Accuracy: **62.39%**
* Forecast Validation MAPE: **3.57%**
* Forecast Validation MAE: **17,748**
* Unit Tests: **14/14 Passed**

### Fixed

* Growth-analysis edge case where new categories were incorrectly labeled as Stable
* Risk-scoring noise caused by extremely low-volume companies
* Docker deployment reproducibility issues through dependency pinning

### Breaking Changes

None.

---

# [v1.1.0] - 2026-06-20

## Forecasting, Risk Intelligence & Driver Analytics

### Added

* Prophet-based complaint forecasting
* Monthly complaint forecasting pipeline
* Next-month forecast output
* Next-3-month forecast output
* Next-6-month forecast output
* Forecast validation framework
* 6-month holdout evaluation window
* Complaint driver analysis
* Product → Issue → Sub-Issue hierarchy analysis
* Product driver summary
* Growth analysis
* Product-level growth tracking
* Issue-level growth tracking
* Executive Risk Dashboard

### Changed

* Risk scoring thresholds refined
* Dashboard expanded with advanced analytics outputs
* Growth classification framework standardized

### Results

* Forecast Validation MAPE: **3.57%**
* Forecast Validation MAE: **17,748**

### Breaking Changes

None.

---

# [v1.0.0] - 2026-06-15

## Initial Data Platform, Analytics Dashboard & Parquet Optimization

### Added

* Chunk-based CSV preprocessing
* Required-column validation
* Missing-value handling
* Date parsing and cleaning
* Duplicate complaint removal
* Feature engineering:

  * Year
  * Month
  * Quarter
  * Day
  * Day_Name
* Parquet-based storage architecture
* Dashboard summary generation
* Executive KPI dashboard
* Product analysis
* Issue analysis
* Company analysis
* Resolution analysis
* Geography analysis
* Narrative intelligence dashboard

### Engineering Notes

* Raw Dataset:

  * 15.95M complaint records
  * 8-9 GB CSV

* Processed Dataset:

  * ~1.3 GB Parquet

* Storage Reduction:

  * ~85% reduction versus raw CSV

* Dashboard Optimization:

  * Streamlit reads pre-aggregated summary files
  * Avoids loading the full processed dataset at runtime

### Architecture Decisions

* Adopted Parquet as the primary storage format
* Separated preprocessing from dashboard serving
* Implemented pre-aggregation strategy for dashboard performance
* Designed modular pipeline architecture for future expansion

### Breaking Changes

None.

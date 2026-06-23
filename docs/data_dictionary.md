# Data Dictionary

This document describes every column used by the pipeline — both the raw
CFPB columns and the derived/engineered columns added during
preprocessing. Source: `src/preprocessing.py`.

---

## Raw Columns (from `complaints.csv`)

These are the columns `preprocessing.py`'s `validate_columns()` requires
to be present in the raw CSV before processing begins.

| Column | Type (raw) | Description | Business Meaning | Missing-Value Handling |
|---|---|---|---|---|
| `Date received` | string → datetime | Date the CFPB received the complaint | Drives all time-series analysis — yearly/monthly trend, forecasting input | Parsed with `format="mixed"`, invalid dates become `NaT` (`errors="coerce"`) |
| `Product` | string | High-level financial product category (e.g. "Credit reporting", "Mortgage") | Primary business unit / portfolio dimension — which product line is generating complaint volume | Left as-is if present; used as a primary grouping dimension throughout the dashboard |
| `Sub-product` | string | More specific product category under `Product` | Finer-grained portfolio segmentation | Filled with `"Unknown"` |
| `Issue` | string | The general issue category for the complaint | Root-cause category — what specifically went wrong | Filled with `"Unknown"` |
| `Sub-issue` | string | More specific issue category under `Issue` | Finer-grained root cause, used in driver analysis | Filled with `"Unknown"` |
| `Consumer complaint narrative` | string (free text) | The consumer's own description of the complaint, when provided | Input to all NLP modules; richest signal for understanding *why* a complaint was filed | Left as `NaN` if missing — this is intentional, since narrative *availability* itself is tracked as a feature (`Has_Narrative`) |
| `Company public response` | string | The company's public (CFPB-published) response, if any | Transparency signal — whether the company chose to respond publicly | Filled with `"No public response"` |
| `Company` | string | Name of the company the complaint was filed against | Risk-scoring entity — the unit `risk_analysis.py` ranks | Rows with missing company are dropped in `risk_analysis.py` (a company can't be risk-scored without a name) |
| `State` | string | US state or territory of the consumer | Geographic distribution signal | Filled with `"Unknown"` |
| `ZIP code` | string | Consumer's ZIP code (often partially redacted by CFPB) | Finer geographic detail (currently unused by any analytics module) | Filled with `"Unknown"` |
| `Tags` | string | Special consumer-group tag, when applicable (e.g. "Older American", "Servicemember") | Vulnerable-population indicator — used for consumer-segment analysis | Filled with `"Normal Consumer"` |
| `Submitted via` | string | Channel the complaint was submitted through (Web, Phone, Referral, etc.) | Channel-mix signal — where consumer effort is concentrated | Left as-is |
| `Date sent to company` | string → datetime | Date the complaint was forwarded to the company | Used to compute response timeliness and delay | Parsed with `format="mixed"`, invalid dates become `NaT` |
| `Company response to consumer` | string | How the company resolved or responded to the complaint | Resolution-quality signal | Filled with `"Unknown"` |
| `Timely response?` | string (`"Yes"` / `"No"`) | Whether the company responded within the required timeframe | **Compliance KPI** — directly feeds the risk score's `Untimely_Response_Pct` | Left as-is |
| `Complaint ID` | integer/string | Unique identifier for the complaint | Deduplication key — ensures each complaint is counted once | Used as the deduplication key (`remove_duplicates()`) |

---

## Derived / Engineered Columns

Added by `create_features()` and `standardize_tags()` during preprocessing.
None of these exist in the raw CSV.

| Column | Derived From | Logic | Business Meaning |
|---|---|---|---|
| `Year` | `Date received` | `.dt.year` | Time-series grouping |
| `Month` | `Date received` | `.dt.month` | Time-series grouping, seasonality |
| `Quarter` | `Date received` | `.dt.quarter` | Quarterly reporting alignment |
| `Day` | `Date received` | `.dt.day` | Day-level granularity (rarely used directly) |
| `Day_Name` | `Date received` | `.dt.day_name()` (e.g. "Monday") | Day-of-week submission pattern |
| `Resolution_Delay` | `Date sent to company` − `Date received` | Difference in days | **Operational KPI** — feeds `Avg_Resolution_Delay` in the risk score; a proxy for internal CFPB routing speed, not the company's own response time |
| `Has_Narrative` | `Consumer complaint narrative` | `1` if a narrative is present, `0` otherwise | Data-completeness indicator — determines NLP eligibility |
| `Narrative_Length` | `Consumer complaint narrative` | Character count of the narrative string (`0` if missing) | Rough complaint-complexity proxy |
| `Narrative_Word_Count` | `Consumer complaint narrative` | Word count of the narrative string (`0` if missing) | Complaint-complexity bucket input (`Low`/`Medium`/`High` in the dashboard) |
| `Consumer_Group` | `Tags` | Simplified label: `"Servicemember"`, `"Older American"`, `"Older American + Servicemember"`, or `"Normal Consumer"` | Vulnerable-population reporting segment |

---

## Dataset-Level Statistics

These are measured values from the actual processed dataset, not
assumptions:

| Statistic | Value |
|---|---|
| Total complaints | 15.95M |
| Companies | 7.97K |
| Products | 21 |
| States / territories | 64 |
| Narrative availability | 23.84% (≈3.8M complaints have a narrative) |
| Timely response rate | 99.37% |
| Average resolution delay | 0.63 days |

---

## Columns Used by Each Module

| Module | Columns Read |
|---|---|
| `dashboard_data.py` (Module 1) | `Year`, `Company`, `Product`, `State`, `Timely response?`, `Resolution_Delay`, `Has_Narrative`, `Narrative_Word_Count`, `Issue`, `Sub-issue`, `Company response to consumer`, `Submitted via`, `Consumer_Group` |
| `risk_analysis.py` (Module 2) | `Company`, `Timely response?`, `Resolution_Delay` |
| `driver_analysis.py` (Module 2) | `Product`, `Issue`, `Sub-issue` |
| `growth_analysis.py` (Module 2) | `Year`, `Month`, `Product`, `Issue` |
| `forecasting.py` (Module 2) | Reads `monthly_complaint_trend.parquet` (output of `growth_analysis.py`), not the raw processed dataset directly |
| `create_narrative_training_data.py` / NLP training (Module 3) | `Consumer complaint narrative`, `Product`, `Issue` |
| `recommendation_engine.py` (Module 4) | Reads only the Parquet outputs of the modules above, not the raw processed dataset |

---

## Notes on Data Quality

- **Narrative availability is low (23.84%).** Most complaints do not
  include free text from the consumer, which is why the NLP pipeline
  operates on a subset (~3.8M rows) while the rest of the analytics
  operates on the full 15.95M-row dataset.
- **`ZIP code` is often partially redacted** in the source CFPB data
  (a CFPB privacy practice, not a defect introduced by this pipeline).
  It is currently loaded and cleaned but not used by any analytics
  module.
- **State-level analysis is not population-normalized.** `State` is
  used as-is for geographic breakdowns; see `README.md` → Known
  Limitations for the per-capita normalization gap.
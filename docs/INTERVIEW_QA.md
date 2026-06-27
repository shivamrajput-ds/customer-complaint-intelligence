# Customer Complaint Intelligence Platform — Interview Q&A

## 1. What problem does this project solve?

This project turns a large consumer complaint dataset into an analytics and NLP decision-support platform.

Instead of only showing complaint counts, it helps answer business questions such as:

- Which companies have higher complaint risk?
- Which products or issues are growing?
- What complaint volume may look like in the future?
- Can complaint narratives be classified automatically?
- What actions should an operations or compliance team prioritize?

---

## 2. Why did you choose the CFPB Consumer Complaint dataset?

I chose it because it is large, messy, public, and realistic. It contains millions of complaint records across products, companies, issues, geographies, responses, and complaint narratives.

This made it suitable for showing both data engineering and machine learning skills.

---

## 3. What was the biggest engineering challenge?

The biggest challenge was processing a very large raw CSV on a normal laptop.

The raw dataset is around 8–9 GB and contains about 15.95M complaints. Loading everything directly into memory can cause performance or memory issues.

I handled this by using:

- chunked ingestion
- column selection
- cleaning and validation
- Parquet outputs
- pre-aggregated dashboard files

This allowed the Streamlit dashboard to stay lightweight.

---

## 4. Why did you use Parquet instead of only CSV?

Parquet is columnar and compressed, so it is usually more efficient for analytical workloads.

In this project, Parquet helped with:

- smaller processed storage
- faster reads for selected columns
- better dashboard performance
- easier separation of raw and processed data

CSV is good for raw exchange, but Parquet is better for repeated analytical reads.

---

## 5. Why did you pre-aggregate dashboard files?

The full dataset is too large to load every time the dashboard refreshes.

So the heavy computation is done in the pipeline stage, and the dashboard reads smaller processed summary files. This makes the Streamlit app faster and more stable.

---

## 6. What are the main modules in the project?

The project has four main parts:

1. Executive Analytics
2. Advanced Intelligence
3. NLP Intelligence
4. Recommendation Engine

Executive Analytics covers KPIs and dashboard views. Advanced Intelligence covers risk scoring, drivers, growth, and forecasting. NLP Intelligence classifies complaint narratives and extracts topics. The Recommendation Engine converts signals into suggested actions.

---

## 7. How does the company risk score work?

The company risk score combines multiple complaint-related signals instead of using complaint volume alone.

The main signals are:

- complaint volume
- untimely response rate
- average resolution delay

This is more useful than raw complaint count alone because a large company may naturally receive more complaints. Risk scoring gives a more structured way to compare companies, although it is still not a legal or regulatory conclusion.

---

## 8. Why did you add a minimum complaint threshold for risk scoring?

Without a minimum threshold, small companies with very few complaints can appear risky due to random noise.

For example, if a company has only 2 complaints and 1 is delayed, its delay rate may look very high. A minimum sample threshold reduces this kind of distortion.

---

## 9. What is driver analysis?

Driver analysis identifies the combinations of Product, Issue, and Sub-issue that contribute most to complaint volume.

It helps answer:

- What is driving complaints in a product category?
- Which issue areas should be prioritized?
- Are there repeated operational patterns?

---

## 10. What is growth analysis?

Growth analysis compares complaint volume over time and labels products or issues based on their year-over-year movement.

Example labels include:

- Stable
- Rising
- Rising Fast
- Declining
- New / Emerging

This helps identify early signals before they become major complaint volume problems.

---

## 11. Why did you use Prophet for forecasting?

Prophet is useful for time-series forecasting with trend and seasonality. Complaint volume is naturally time-based, so Prophet was a practical choice for monthly forecasting.

I also validated the forecast on a holdout period instead of only fitting on all historical data.

---

## 12. What does Forecast MAPE mean?

MAPE stands for Mean Absolute Percentage Error. It measures forecast error as a percentage.

A lower MAPE means the forecast is closer to the actual values. In this project, the validation MAPE is documented as 3.57%, which means the model performed well on the selected validation setup.

---

## 13. Why did you use TF-IDF + Logistic Regression instead of BERT?

I used TF-IDF + Logistic Regression because it is:

- CPU-friendly
- fast to train
- fast at inference
- easier to explain
- reproducible on consumer hardware
- strong as a baseline for text classification

A transformer model like BERT may improve performance, but it would increase training time, inference cost, and deployment complexity.

For this project, the goal was a practical end-to-end platform, not only the highest possible NLP score.

---

## 14. What were the NLP results?

The documented results are:

| Model | Metric |
|---|---:|
| Product classifier | 75.28% accuracy |
| Issue classifier | 62.39% accuracy |

The Product classifier performs better because Product categories are broader and easier to separate. Issue classification is harder because issue labels are more detailed and semantically overlapping.

---

## 15. Why is Issue classifier accuracy lower than Product classifier accuracy?

Issue classification is more difficult because:

- there are more issue classes
- many issue labels have similar language
- complaint narratives can be noisy
- some classes may have fewer examples
- one complaint can contain signals for multiple issues

So 62.39% is not perfect, but it is a reasonable baseline for a CPU-friendly model.

---

## 16. Why did you use LDA topic modeling?

LDA helps discover repeated themes in complaint narratives without needing labels.

It is useful for exploratory analysis and for understanding what kinds of words/topics appear frequently in complaint text. The topic names are manually interpreted, so they should be treated as analytical support, not perfect labels.

---

## 17. Why not use sentiment analysis?

Most complaint narratives are negative by nature. Generic sentiment analysis would mostly say “negative” and would not add much business value.

Classification, topic modeling, drivers, growth, and recommendations are more useful for this dataset.

---

## 18. What does the recommendation engine do?

The recommendation engine combines signals from:

- company risk scores
- product growth
- issue growth
- complaint drivers
- forecasts

It converts those signals into prioritized recommendations and executive action guidance.

This makes the project more useful than a dashboard that only shows charts.

---

## 19. How is this project different from a normal dashboard?

A normal dashboard mostly describes what happened.

This project also tries to answer:

- what is risky
- what is growing
- what may happen next
- what should be prioritized
- how to classify new complaint narratives

So it moves from descriptive analytics toward decision intelligence.

---

## 20. How did you evaluate the project?

The project evaluation includes:

- NLP accuracy metrics
- forecasting validation metrics
- unit tests
- dashboard output validation
- documented limitations
- Docker build/run validation
- CI/CD workflow validation

The README reports 14/14 unit tests passing, Product classifier accuracy of 75.28%, Issue classifier accuracy of 62.39%, and forecast validation MAPE of 3.57%.

---

## 21. What are the main limitations?

The main limitations are:

- Geographic complaint counts are not normalized by population.
- NLP predictions currently return only the top label.
- NLP confidence scores are not calibrated probabilities.
- Forecasting does not include external economic or regulatory signals.
- Topic modeling uses manually interpreted LDA topics.
- Some NLP training constants should be fully moved to config.
- FastAPI serving layer is planned for future improvement.

---

## 22. What would you improve next?

The best next improvements are:

1. Add Top-3 Product and Issue predictions.
2. Add calibrated or confidence-aware NLP outputs.
3. Normalize state-level complaints per capita.
4. Add FastAPI model serving.
5. Add model versioning and metadata.
6. Add drift monitoring for NLP models.
7. Add stronger runtime and memory benchmarks.

---

## 23. Why is per-capita normalization important?

Raw complaint count by state can be misleading because larger states naturally have more people and more customers.

Per-capita normalization would make geographic comparison fairer by adjusting for population.

---

## 24. What is the most impressive part of this project for placement?

The strongest part is the combination of scale and business usefulness.

It shows:

- large-data handling
- analytics pipeline design
- NLP modeling
- forecasting
- recommendation logic
- dashboarding
- Docker deployment
- testing and documentation

This makes it stronger than a single notebook-based ML project.

---

## 25. How would you explain this project in 60 seconds?

This is an end-to-end analytics and NLP platform built on the CFPB Consumer Complaint dataset with around 15.95M complaints. I processed the large raw CSV using chunked preprocessing and Parquet outputs, then built dashboards for executive KPIs, product trends, company risk, complaint drivers, growth analysis, forecasting, NLP classification, topic modeling, and recommendations. The project uses CPU-friendly ML models like TF-IDF + Logistic Regression and Prophet, and it is packaged with Streamlit, Docker, tests, CI/CD, and technical documentation.

---

## 26. What should you not overclaim in an interview?

Do not overclaim that:

- the risk score is a legal or regulatory judgment
- the NLP model is perfect
- the forecast includes all external factors
- topic modeling gives exact human-level categories
- complaint count alone proves company quality
- the system is a full enterprise SaaS product

The honest explanation is stronger: this is a production-style portfolio project with clear next improvements.

---

## 27. Final interview answer: why should this project be considered strong?

This project is strong because it combines data engineering, analytics, machine learning, NLP, forecasting, dashboarding, Docker deployment, testing, and documentation on a real large-scale public dataset. It also explains its limitations clearly, which shows practical engineering maturity instead of only showing polished charts.

"""
nlp_inference.py

Loads trained NLP models and provides prediction functions for:
1. Product prediction
2. Issue prediction
3. Topic detection
4. Full complaint analysis
"""

import re
from pathlib import Path
from typing import Any

import joblib

from src.config_loader import config


MODEL_DIR = Path(config["paths"]["model_dir"])

PRODUCT_MODEL_PATH = MODEL_DIR / "product_classifier_model.pkl"
PRODUCT_VECTORIZER_PATH = MODEL_DIR / "product_classifier_vectorizer.pkl"

ISSUE_MODEL_PATH = MODEL_DIR / "issue_classifier_model.pkl"
ISSUE_VECTORIZER_PATH = MODEL_DIR / "issue_classifier_vectorizer.pkl"

TOPIC_MODEL_PATH = MODEL_DIR / "topic_model.pkl"
TOPIC_VECTORIZER_PATH = MODEL_DIR / "topic_vectorizer.pkl"
TOPIC_WORDS_PATH = MODEL_DIR / "topic_words.pkl"


def clean_text(text: str) -> str:
    """
    Clean complaint text before prediction.

    Steps:
    - Convert to lowercase
    - Remove masked CFPB tokens like XX, XXXX
    - Remove numbers
    - Remove special characters
    - Remove extra spaces
    """
    text = str(text).lower()
    text = re.sub(r"\bxx+\b", " ", text)
    text = re.sub(r"\d+", " ", text)
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def load_model(path: Path) -> Any:
    """
    Load a saved joblib model safely.

    Raises a clear error if the model file is missing.
    """
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")

    return joblib.load(path)


product_model = load_model(PRODUCT_MODEL_PATH)
product_vectorizer = load_model(PRODUCT_VECTORIZER_PATH)

issue_model = load_model(ISSUE_MODEL_PATH)
issue_vectorizer = load_model(ISSUE_VECTORIZER_PATH)

topic_model = load_model(TOPIC_MODEL_PATH)
topic_vectorizer = load_model(TOPIC_VECTORIZER_PATH)
topic_words = load_model(TOPIC_WORDS_PATH)


def validate_input_text(text: str) -> str:
    """
    Validate input complaint text.

    Empty text should not be sent to models because vectorizers
    may produce weak or meaningless predictions.
    """
    cleaned = clean_text(text)

    if not cleaned:
        raise ValueError("Complaint text is empty after cleaning")

    return cleaned


def predict_product(text: str) -> str:
    """Predict product category from complaint narrative."""
    cleaned = validate_input_text(text)
    vector = product_vectorizer.transform([cleaned])

    return product_model.predict(vector)[0]


def predict_issue(text: str) -> str:
    """Predict issue category from complaint narrative."""
    cleaned = validate_input_text(text)
    vector = issue_vectorizer.transform([cleaned])

    return issue_model.predict(vector)[0]


def predict_topic(text: str) -> dict:
    """
    Predict topic ID, topic keywords, and confidence score.

    topic_model.transform() returns probability distribution over topics.
    """
    cleaned = validate_input_text(text)
    vector = topic_vectorizer.transform([cleaned])

    topic_probs = topic_model.transform(vector)
    topic_id = int(topic_probs.argmax())

    return {
        "topic_id": topic_id,
        "topic_words": topic_words[topic_id],
        "confidence": float(topic_probs[0][topic_id]),
    }


def analyze_complaint(text: str) -> dict:
    """
    Run complete NLP analysis on one complaint narrative.

    Output:
    - predicted product
    - predicted issue
    - detected topic
    """
    return {
        "product": predict_product(text),
        "issue": predict_issue(text),
        "topic": predict_topic(text),
    }


if __name__ == "__main__":
    sample_text = """
    Someone opened fraudulent accounts in my name and there are inquiries
    on my credit report that I do not recognize.
    """

    result = analyze_complaint(sample_text)
    print(result)
import re
import sys
from pathlib import Path

import joblib
import pandas as pd

from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from src.logger import logger
from src.exception import CustomException


TRAINING_DATA_PATH = Path("data/processed/narratives_training.parquet")
MODEL_DIR = Path("models/nlp")

RANDOM_STATE = 42
SAMPLE_SIZE = 300_000


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"\bxx+\b", " ", text)
    text = re.sub(r"\d+", " ", text)
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_training_data() -> pd.DataFrame:
    logger.info("Loading narrative training data")

    df = pd.read_parquet(TRAINING_DATA_PATH)

    logger.info(f"Total narrative rows: {len(df)}")

    if len(df) > SAMPLE_SIZE:
        df = df.sample(
            n=SAMPLE_SIZE,
            random_state=RANDOM_STATE,
        ).copy()

    logger.info(f"Sampled training rows: {len(df)}")

    df["clean_text"] = (
        df["Consumer complaint narrative"]
        .apply(clean_text)
    )

    return df


def train_classifier(df: pd.DataFrame, target_col: str, model_prefix: str) -> None:
    logger.info(f"Training started: {model_prefix}")

    model_df = df[["clean_text", target_col]].dropna().copy()

    class_counts = model_df[target_col].value_counts()
    valid_classes = class_counts[class_counts >= 50].index

    model_df = model_df[
        model_df[target_col].isin(valid_classes)
    ].copy()

    X = model_df["clean_text"]
    y = model_df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=20_000,
        ngram_range=(1, 2),
        min_df=3,
    )

    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(
        max_iter=2000,
        n_jobs=-1,
    )

    model.fit(X_train_vec, y_train)

    y_pred = model.predict(X_test_vec)

    accuracy = accuracy_score(y_test, y_pred)

    report = classification_report(
        y_test,
        y_pred,
        zero_division=0,
    )

    logger.info(f"{model_prefix} accuracy: {accuracy}")
    logger.info(f"\n{report}")

    joblib.dump(model, MODEL_DIR / f"{model_prefix}_model.pkl")
    joblib.dump(vectorizer, MODEL_DIR / f"{model_prefix}_vectorizer.pkl")

    with open(MODEL_DIR / f"{model_prefix}_metrics.txt", "w", encoding="utf-8") as f:
        f.write(f"Accuracy: {accuracy}\n\n")
        f.write(report)

    logger.info(f"Training completed: {model_prefix}")


def train_topic_model(df: pd.DataFrame) -> None:
    logger.info("Topic modeling started")

    vectorizer = CountVectorizer(
        stop_words="english",
        max_features=10_000,
        min_df=10,
        ngram_range=(1, 2),
    )

    X_topic = vectorizer.fit_transform(df["clean_text"])

    lda = LatentDirichletAllocation(
        n_components=10,
        random_state=RANDOM_STATE,
        learning_method="batch",
    )

    lda.fit(X_topic)

    feature_names = vectorizer.get_feature_names_out()

    topic_words = {}

    for topic_idx, topic in enumerate(lda.components_):
        words = [
            feature_names[i]
            for i in topic.argsort()[-15:][::-1]
        ]

        topic_words[topic_idx] = words
        logger.info(f"Topic {topic_idx}: {words}")

    joblib.dump(lda, MODEL_DIR / "topic_model.pkl")
    joblib.dump(vectorizer, MODEL_DIR / "topic_vectorizer.pkl")
    joblib.dump(topic_words, MODEL_DIR / "topic_words.pkl")

    logger.info("Topic modeling completed")


def train_nlp_models() -> None:
    try:
        logger.info("Final NLP training started")

        MODEL_DIR.mkdir(parents=True, exist_ok=True)

        if not TRAINING_DATA_PATH.exists():
            raise FileNotFoundError(
                f"Narrative training data not found: {TRAINING_DATA_PATH}. "
                "Run create_narrative_training_data.py first."
            )

        df = load_training_data()

        logger.info(f"Training data shape: {df.shape}")

        train_classifier(
            df=df,
            target_col="Product",
            model_prefix="product_classifier",
        )

        train_classifier(
            df=df,
            target_col="Issue",
            model_prefix="issue_classifier",
        )

        train_topic_model(df)

        logger.info("Final NLP training completed")

    except Exception as e:
        logger.exception("Final NLP training failed")
        raise CustomException(e, sys)


if __name__ == "__main__":
    train_nlp_models()
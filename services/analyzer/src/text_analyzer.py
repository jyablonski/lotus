from typing import Any

from transformers import pipeline

# Load once on startup
sentiment_pipeline = pipeline("sentiment-analysis")


def analyze_text(text: str) -> dict[str, Any]:
    result = sentiment_pipeline(text)[0]
    label = result["label"].lower()  # e.g. "positive" or "negative"
    score = result["score"]  # confidence score between 0 and 1

    # Simple keyword extraction (can be improved later)
    keywords = [word for word in text.lower().split() if len(word) > 4][:10]

    # Convert to numeric sentiment_score (positive=score, negative=-score)
    sentiment_score = score if label == "positive" else -score

    return {
        "sentiment_score": sentiment_score,
        "mood_label": label,
        "keywords": keywords,
    }

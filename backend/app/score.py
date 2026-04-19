"""
Trend Worthiness Score — Scoring Engine
========================================
Loads your trained models and exposes a single function: score_trend()
This is what your FastAPI endpoint will call.

Model files expected (copy to same directory as this file, or set MODEL_DIR):
  - kmeans.pkl
  - scaler_km.pkl
  - hgb_pipeline.pkl
  - cluster_features.pkl
  - classifier_features.pkl
  - archetype_names.pkl
"""

import os
import joblib
import numpy as np
import pandas as pd

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────

MODEL_DIR = os.getenv("MODEL_DIR", "models")

# Imputed median log_views — used for clustering since log_views
# is a post-publish signal and won't be available at prediction time.
# Update this with df["log_views"].median() from your training data.
LOG_VIEWS_MEDIAN = 10.5

# ─────────────────────────────────────────────
# Archetype advice
# ─────────────────────────────────────────────

ARCHETYPE_ADVICE = {
    "Flash Viral":       "Skip it — high engagement but burns out before most creators can publish.",
    "Fast Mover":        "Move fast — the window is open but closing. Publish within 48 hours.",
    "Mid-Burn Trending": "Viable if you can turn around quality content in 3–5 days.",
    "Sustained Grower":  "Good opportunity — the trend has legs. Take time to do it well.",
    "Legacy Evergreen":  "Strong buy — high view ceiling, long relevance window. Publish whenever ready.",
}

ARCHETYPE_COLOR = {
    "Flash Viral":       "red",
    "Fast Mover":        "orange",
    "Mid-Burn Trending": "yellow",
    "Sustained Grower":  "green",
    "Legacy Evergreen":  "blue",
}

# ─────────────────────────────────────────────
# Model loading (cached at module level)
# ─────────────────────────────────────────────

_models = None

def _load_models():
    global _models
    if _models is None:
        _models = {
            "kmeans":     joblib.load(os.path.join(MODEL_DIR, "kmeans.pkl")),
            "scaler":     joblib.load(os.path.join(MODEL_DIR, "scaler_km.pkl")),
            "hgb":        joblib.load(os.path.join(MODEL_DIR, "hgb_pipeline.pkl")),
            "km_feats":   joblib.load(os.path.join(MODEL_DIR, "cluster_features.pkl")),
            "clf_feats":  joblib.load(os.path.join(MODEL_DIR, "classifier_features.pkl")),
            "archetypes": joblib.load(os.path.join(MODEL_DIR, "archetype_names.pkl")),
        }
    return _models


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _timing_label(days_to_trend: float) -> str:
    """Convert days_to_trend into a plain-English timing window."""
    if days_to_trend <= 1:
        return "Trending now — act within 24 hours or skip."
    elif days_to_trend <= 7:
        return "Early trend — publish within 48–72 hours."
    elif days_to_trend <= 30:
        return "Growing trend — you have up to a week."
    elif days_to_trend <= 180:
        return "Slow burn — topic has time, don't rush quality."
    else:
        return "Evergreen topic — publish whenever you're ready."


def _score_label(score: int) -> str:
    """Convert 0–100 score into a human-readable tier."""
    if score >= 75:
        return "Strong"
    elif score >= 50:
        return "Moderate"
    elif score >= 25:
        return "Weak"
    else:
        return "Skip"


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

def score_trend(features: dict) -> dict:
    """
    Translate raw creator inputs into a Trend Worthiness Score.

    Parameters
    ----------
    features : dict
        Required keys:
            category_id   (int)   — YouTube category ID (e.g. 24 = Entertainment)
            days_to_trend (float) — days since video was published
            like_rate     (float) — likes / views, e.g. 0.08 for 8%
            comment_rate  (float) — comments / views, e.g. 0.02 for 2%
            tag_count     (int)   — number of tags (0 = no tags)
            publish_hour  (int)   — hour of publish (0–23, UTC)
            publish_dow   (int)   — day of week (0 = Monday, 6 = Sunday)

        has_tags is derived automatically from tag_count.

    Returns
    -------
    dict:
        archetype       (str)  — cluster name
        score           (int)  — 0–100 worthiness score
        score_label     (str)  — "Strong" / "Moderate" / "Weak" / "Skip"
        timing          (str)  — plain-English timing window
        recommendation  (str)  — archetype-specific action advice
        color           (str)  — UI hint: red / orange / yellow / green / blue
        worth_joining   (bool) — shorthand: score >= 50
    """
    m = _load_models()

    # Derive has_tags
    features = features.copy()
    features["has_tags"] = int(features.get("tag_count", 0) > 0)

    # Clamp engagement ratios to training caps
    features["like_rate"]    = min(features["like_rate"],    0.20)
    features["comment_rate"] = min(features["comment_rate"], 0.05)

    # ── K-Means clustering ───────────────────────────────────────────
    # log_views is a post-publish signal — impute with training median
    km_row = {k: features.get(k) for k in m["km_feats"] if k != "log_views"}
    km_row["log_views"] = LOG_VIEWS_MEDIAN

    km_input  = pd.DataFrame([{k: km_row.get(k) for k in m["km_feats"]}])
    km_scaled = m["scaler"].transform(km_input)
    cluster_id = int(m["kmeans"].predict(km_scaled)[0])
    archetype  = m["archetypes"].get(cluster_id, f"Cluster {cluster_id}")

    # ── HGB classification ───────────────────────────────────────────
    clf_input  = pd.DataFrame([{k: features[k] for k in m["clf_feats"]}])
    prob       = float(m["hgb"].predict_proba(clf_input)[0][1])
    confidence = int(round(prob * 100))

    return {
        "archetype":      archetype,
        "confidence":     confidence,   # 0–100, supporting context only
        "timing":         _timing_label(features["days_to_trend"]),
        "recommendation": ARCHETYPE_ADVICE.get(archetype, ""),
        "color":          ARCHETYPE_COLOR.get(archetype, "gray"),
    }


# ─────────────────────────────────────────────
# Smoke test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    test_cases = [
        {
            "label": "Fast-moving entertainment video with good engagement",
            "input": {
                "category_id": 24, "days_to_trend": 3, "like_rate": 0.08,
                "comment_rate": 0.02, "tag_count": 12,
                "publish_hour": 15, "publish_dow": 1,
            },
        },
        {
            "label": "Old video, low engagement, no tags",
            "input": {
                "category_id": 10, "days_to_trend": 500, "like_rate": 0.01,
                "comment_rate": 0.001, "tag_count": 0,
                "publish_hour": 3, "publish_dow": 6,
            },
        },
        {
            "label": "Just published, high engagement, many tags",
            "input": {
                "category_id": 20, "days_to_trend": 0, "like_rate": 0.12,
                "comment_rate": 0.04, "tag_count": 30,
                "publish_hour": 18, "publish_dow": 4,
            },
        },
    ]

    for tc in test_cases:
        print(f"\n── {tc['label']}")
        result = score_trend(tc["input"])
        print(f"   Archetype:  {result['archetype']}  ({result['color']})")
        print(f"   Score:      {result['score']}/100  [{result['score_label']}]")
        print(f"   Timing:     {result['timing']}")
        print(f"   Advice:     {result['recommendation']}")
        print(f"   Worth it?   {'Yes' if result['worth_joining'] else 'No'}")
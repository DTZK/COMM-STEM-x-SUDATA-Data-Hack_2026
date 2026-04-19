"""
Trend Worthiness Score — FastAPI Backend
=========================================
Run from the backend/ directory:
    uvicorn main:app --reload --port 8000

Endpoints:
    GET  /health        — liveness check
    GET  /categories    — list of YouTube category id + name pairs
    POST /predict       — returns archetype, score, timing, recommendation
    POST /score-csv     — score every row in an uploaded CSV file
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from app.score import score_trend

import io
import numpy as np
import pandas as pd

app = FastAPI(
    title="Trend Worthiness Score API",
    version="1.0.0",
)

# ─────────────────────────────────────────────
# CORS — allow the Vite dev server to call this
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # fallback
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# YouTube category reference
# ─────────────────────────────────────────────

CATEGORIES = {
    1:  "Film & Animation",
    2:  "Autos & Vehicles",
    10: "Music",
    15: "Pets & Animals",
    17: "Sports",
    18: "Short Movies",
    19: "Travel & Events",
    20: "Gaming",
    21: "Videoblogging",
    22: "People & Blogs",
    23: "Comedy",
    24: "Entertainment",
    25: "News & Politics",
    26: "Howto & Style",
    27: "Education",
    28: "Science & Technology",
    29: "Nonprofits & Activism",
}

# ─────────────────────────────────────────────
# Required CSV columns
# ─────────────────────────────────────────────
 
REQUIRED_COLUMNS = {
    "title", "category_id", "views", "likes",
    "comments", "publish_time", "trending_date", "tags"
}
 
# ─────────────────────────────────────────────
# Feature engineering 
# ─────────────────────────────────────────────
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Parse dates
    df["publish_time"] = pd.to_datetime(df["publish_time"], utc=True, errors="coerce")

    # trending_date format is YY.DD.MM 
    df["trending_date_parsed"] = pd.to_datetime(
        df["trending_date"].astype(str).str.replace(
            r"(\d+)\.(\d+)\.(\d+)", r"20\1-\3-\2", regex=True
        ),
        utc=True,
        errors="coerce",
    )

    # Drop sub-1000 view noise
    df = df[df["views"] >= 1000].copy()

    # Velocity
    df["days_to_trend"] = (
        df["trending_date_parsed"] - df["publish_time"]
    ).dt.days.clip(lower=0)

    # Engagement ratios
    df["like_rate"]    = (df["likes"] / df["views"]).clip(upper=0.20)
    df["comment_rate"] = (df["comments"] / df["views"]).clip(upper=0.05)

    # Tag features
    df["has_tags"]  = (df["tags"] != "[none]").astype(int)
    df["tag_count"] = df["tags"].apply(
        lambda x: len(str(x).split("|")) if x != "[none]" else 0
    )

    # Publish timing
    df["publish_hour"] = df["publish_time"].dt.hour
    df["publish_dow"]  = df["publish_time"].dt.dayofweek

    return df

# ─────────────────────────────────────────────
# Request / Response schemas
# ─────────────────────────────────────────────

class PredictRequest(BaseModel):
    category_id:   int   = Field(..., description="YouTube category ID")
    days_to_trend: float = Field(..., ge=0, description="Days since publish")
    like_rate:     float = Field(..., ge=0, le=1,  description="Likes / views (0–1)")
    comment_rate:  float = Field(..., ge=0, le=1,  description="Comments / views (0–1)")
    tag_count:     int   = Field(..., ge=0, description="Number of tags (0 = none)")
    publish_hour:  int   = Field(..., ge=0, le=23, description="Hour of publish (0–23 UTC)")
    publish_dow:   int   = Field(..., ge=0, le=6,  description="Day of week (0=Mon, 6=Sun)")

    @field_validator("category_id")
    @classmethod
    def validate_category(cls, v):
        if v not in CATEGORIES:
            raise ValueError(f"Unknown category_id {v}. Valid IDs: {sorted(CATEGORIES)}")
        return v


class PredictResponse(BaseModel):
    archetype:      str
    confidence:     int   # 0-100, supporting context only
    timing:         str
    recommendation: str
    color:          str


class CategoryItem(BaseModel):
    id:   int
    name: str


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/categories", response_model=list[CategoryItem])
def get_categories():
    """Return all supported YouTube category id + name pairs."""
    return [{"id": k, "name": v} for k, v in sorted(CATEGORIES.items(), key=lambda x: x[1])]


@app.post("/predict", response_model=PredictResponse)
def predict(body: PredictRequest):
    """Score a trend based on pre-publish signals."""
    try:
        result = score_trend(body.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return result

@app.post("/score-csv")
async def score_csv(file: UploadFile = File(...)):
    """
    Upload a CSV with YouTube trending data.
    Returns scored results as a downloadable CSV.
 
    Required columns:
        title, category_id, views, likes, comments,
        publish_time, trending_date, tags
    """

    #Read upload
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    
    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")
    
    #Validate columns
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required columns: {sorted(missing)}"
        )
    
    #Feature Engineering
    try:
        df = engineer_features(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature engineering failed: {e}")
 
    if df.empty:
        raise HTTPException(
            status_code=422,
            detail="No valid rows remaining after cleaning (all videos had < 1000 views or unparseable dates)."
        )
    
    #Score every row
    results = []
    for _, row in df.iterrows():
        try:
            scored = score_trend({
                "category_id":   int(row["category_id"]),
                "days_to_trend": float(row["days_to_trend"]),
                "like_rate":     float(row["like_rate"]),
                "comment_rate":  float(row["comment_rate"]),
                "tag_count":     int(row["tag_count"]),
                "publish_hour":  int(row["publish_hour"]),
                "publish_dow":   int(row["publish_dow"]),
            })
            results.append({
                "title":          row.get("title", ""),
                "category":       CATEGORIES.get(int(row["category_id"]), str(row["category_id"])),
                "days_to_trend":  int(row["days_to_trend"]),
                "archetype":      scored["archetype"],
                "confidence":     f"{scored['confidence']}/100",
                "timing":         scored["timing"],
                "recommendation": scored["recommendation"],
            })
        except Exception:
            # Skip rows that fail scoring individually
            continue

    if not results:
        raise HTTPException(status_code=500, detail="No rows could be scored.")
    
    #Return as downloadable CSV
    output_df = pd.DataFrame(results)
    csv_buf = io.StringIO()
    output_df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)

    return StreamingResponse(
    iter([csv_buf.getvalue()]),
    media_type="text/csv",
    headers={"Content-Disposition": "attachment; filename=trend_scores.csv"},
    )

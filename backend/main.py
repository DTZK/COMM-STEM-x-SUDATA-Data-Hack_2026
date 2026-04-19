"""
Trend Worthiness Score — FastAPI Backend
=========================================
Run from the backend/ directory:
    uvicorn main:app --reload --port 8000

Endpoints:
    GET  /health        — liveness check
    GET  /categories    — list of YouTube category id + name pairs
    POST /predict       — returns archetype, score, timing, recommendation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from app.score import score_trend

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
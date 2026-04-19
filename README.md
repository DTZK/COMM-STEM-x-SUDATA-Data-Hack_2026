# TrendScore — YouTube Trend Worthiness Score
> COMM-STEM × SUDATA Data Hack 2026

**TrendScore** helps YouTube creators and agencies decide whether to jump on a trend — and exactly when to publish — using pre-publish signals and machine learning.

---

## 🔴 Live Demo
👉 [trendscore.streamlit.app](https://comm-stem-x-sudata-data-hack2026-7dc5axbm4dnf2hcpp9z9a9.streamlit.app/)

---

## The Problem
Creators have no tool that tells them *when* to jump on a trend — only that a trend exists. TrendScore fills that gap by predicting whether a YouTube trend is worth a creator's production time based on signals available *before* publishing.

---

## How It Works

### Data
- **Dataset:** US YouTube Trending (16,400 rows, Feb 2026 snapshot)
- **After cleaning:** 15,894 usable rows (dropped sub-1,000 view videos, capped engagement ratios, removed nulls)

### Features Engineered
| Feature | Type | What it captures |
|---|---|---|
| `days_to_trend` | Derived | Velocity — how fast the video hit trending |
| `like_rate` | Derived | Engagement quality (capped at 20%) |
| `comment_rate` | Derived | Discussion depth (capped at 5%) |
| `has_tags` | Derived | Tagging strategy (binary) |
| `tag_count` | Derived | Number of tags used |
| `publish_hour` | Derived | Upload timing strategy |
| `publish_dow` | Derived | Day of week uploaded |
| `category_id` | Raw | Content niche |

### ML Pipeline

**Stage 1 — K-Means Clustering (5 Archetypes)**
| Archetype | Avg days to trend | Like rate | Worth joining % |
|---|---|---|---|
| ⚡ Flash Viral | 12 days | 11% | 0% |
| 🚀 Fast Mover | 203 days | 3% | 30% |
| 🔥 Mid-Burn Trending | 314 days | 11% | 18% |
| 📈 Sustained Grower | 415 days | 3% | 37% |
| 🌿 Legacy Evergreen | 4,555 days | 1% | 67% |

**Stage 2 — HistGradientBoostingClassifier**
| Metric | Value |
|---|---|
| Test AUC | 0.872 |
| CV AUC | 0.874 ± 0.006 |
| Accuracy | 84% |

Top feature: `days_to_trend` (importance: 0.203)

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/categories` | YouTube category list |
| POST | `/predict` | Score a single trend |
| POST | `/score-csv` | Batch score an uploaded CSV |

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── score.py          # Scoring engine
│   ├── models/               # Trained pkl files
│   ├── streamlit/
│   │   └── app.py            # Streamlit dashboard
│   ├── main.py               # FastAPI app
│   └── requirements.txt
├── src/                      # React/TypeScript frontend
└── README.md
```

---

## Running Locally

**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Streamlit**
```bash
cd backend
streamlit run streamlit/app.py
```

**React Frontend**
```bash
npm install
npm run dev
```

---

## Tech Stack
- **ML:** scikit-learn (KMeans + HistGradientBoostingClassifier)
- **Backend:** FastAPI + uvicorn
- **Frontend:** Streamlit + Plotly
- **React UI:** Vite + TypeScript
- **Deployment:** Render (API) + Streamlit Community Cloud

---

## Team
> COMM-STEM × SUDATA Data Hack 2026

"""
YouTube Trend Worthiness Dashboard
===================================
Run from the backend/streamlit/ directory:
    streamlit run app.py

Requires the FastAPI backend running at http://localhost:8000:
    cd ../  &&  uvicorn main:app --reload --port 8000
"""

import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timezone

API_BASE = "http://localhost:8000"

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="TrendScore — YouTube Analytics",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────

st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0f0f0f; color: #f1f1f1; }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1a1a1a; border-right: 1px solid #282828; }
    [data-testid="stSidebar"] .stMarkdown { color: #aaaaaa; }

    /* Header */
    .hero-header {
        background: linear-gradient(135deg, #ff0000 0%, #cc0000 50%, #990000 100%);
        padding: 28px 32px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .hero-header h1 { color: white; margin: 0; font-size: 2.2rem; font-weight: 800; }
    .hero-header p  { color: rgba(255,255,255,0.85); margin: 6px 0 0; font-size: 1rem; }

    /* Archetype card */
    .archetype-card {
        padding: 24px 28px;
        border-radius: 12px;
        border-left: 6px solid;
        margin-bottom: 16px;
    }
    .archetype-card h2 { margin: 0 0 6px; font-size: 1.6rem; font-weight: 800; }
    .archetype-card p  { margin: 0; font-size: 0.95rem; opacity: 0.9; }

    /* Metric tiles */
    .metric-tile {
        background: #1a1a1a;
        border: 1px solid #282828;
        border-radius: 10px;
        padding: 18px 20px;
        text-align: center;
        height: 100%;
    }
    .metric-tile .label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: #aaa; margin-bottom: 8px; }
    .metric-tile .value { font-size: 2rem; font-weight: 800; color: #f1f1f1; }
    .metric-tile .sub   { font-size: 0.8rem; color: #888; margin-top: 4px; }

    /* Insight boxes */
    .insight-box {
        background: #1a1a1a;
        border: 1px solid #282828;
        border-radius: 10px;
        padding: 20px 22px;
        margin-bottom: 12px;
    }
    .insight-box .icon  { font-size: 1.4rem; margin-bottom: 8px; }
    .insight-box .title { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: #888; margin-bottom: 6px; }
    .insight-box .body  { font-size: 0.95rem; color: #e0e0e0; line-height: 1.5; }

    /* Tips list */
    .tip-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 10px 0;
        border-bottom: 1px solid #282828;
        font-size: 0.9rem;
        color: #cccccc;
    }
    .tip-item:last-child { border-bottom: none; }
    .tip-bullet { color: #ff0000; font-weight: 800; margin-top: 1px; }

    /* Section headers */
    .section-header {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #666;
        margin: 24px 0 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #282828;
    }

    /* Hide Streamlit branding */
    #MainMenu, footer { visibility: hidden; }
    .stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

ARCHETYPE_PALETTES = {
    "Flash Viral":       {"bg": "#1a0000", "border": "#ff3333", "text": "#ff6666"},
    "Fast Mover":        {"bg": "#1a0d00", "border": "#ff8800", "text": "#ffaa44"},
    "Mid-Burn Trending": {"bg": "#1a1a00", "border": "#ffcc00", "text": "#ffdd44"},
    "Sustained Grower":  {"bg": "#001a00", "border": "#00cc66", "text": "#44ffaa"},
    "Legacy Evergreen":  {"bg": "#00001a", "border": "#3399ff", "text": "#66bbff"},
}

ARCHETYPE_ICONS = {
    "Flash Viral":       "⚡",
    "Fast Mover":        "🚀",
    "Mid-Burn Trending": "🔥",
    "Sustained Grower":  "📈",
    "Legacy Evergreen":  "🌿",
}

ARCHETYPE_TIPS = {
    "Flash Viral": [
        "Post within the next 6–12 hours — this trend peaks fast and collapses.",
        "Use a clickbait-adjacent title with the trending keyword front-loaded.",
        "Keep the video under 8 minutes to maximise watch-through rate.",
        "Pin a comment driving viewers to your other content immediately.",
        "Don't invest heavy production — speed beats polish here.",
    ],
    "Fast Mover": [
        "Publish within 48 hours or the window closes.",
        "Front-load your hook in the first 15 seconds — retention is everything.",
        "Add 10–15 targeted tags using the exact trending search terms.",
        "Share across all your community channels the moment you go live.",
        "Set up an end-screen pointing to your next planned video now.",
    ],
    "Mid-Burn Trending": [
        "You have a 3–5 day window — take a day to improve production quality.",
        "Aim for a more comprehensive take: go deeper than the initial viral clips.",
        "A/B test your thumbnail in the first 2 hours using YouTube's built-in tool.",
        "Collaborate or react to another creator in this niche for extra reach.",
        "Upload a Shorts version to capture the algorithm's cross-format boost.",
    ],
    "Sustained Grower": [
        "Publish steadily — consistency matters more than timing for this archetype.",
        "Optimise for SEO: focus on long-tail keywords in title, description, and tags.",
        "Build a series or playlist around this topic to compound view sessions.",
        "Answer viewer questions in your comments to boost engagement signals.",
        "Link to complementary videos in your description to reduce bounce rate.",
    ],
    "Legacy Evergreen": [
        "Prioritise depth and production value — this video will live for years.",
        "Target a 15–30 minute run-time: watchers want comprehensive coverage.",
        "Update the title and thumbnail every 6–12 months to stay fresh in search.",
        "Build internal links: reference this video in every related upload.",
        "Monetise via mid-roll ads — high CPM on long-watch evergreen content.",
    ],
}

@st.cache_data(ttl=300)
def fetch_categories():
    try:
        r = requests.get(f"{API_BASE}/categories", timeout=5)
        r.raise_for_status()
        return {item["name"]: item["id"] for item in r.json()}
    except Exception:
        return {}


def call_predict(payload: dict) -> dict | None:
    try:
        r = requests.post(f"{API_BASE}/predict", json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach the API at http://localhost:8000 — is the FastAPI server running?")
    except requests.exceptions.HTTPError as e:
        st.error(f"API error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
    return None


def confidence_gauge(confidence: int, color: str) -> go.Figure:
    palette = {
        "red": "#ff3333", "orange": "#ff8800", "yellow": "#ffcc00",
        "green": "#00cc66", "blue": "#3399ff",
    }
    bar_color = palette.get(color, "#ff0000")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence,
        number={"suffix": "%", "font": {"size": 42, "color": "#f1f1f1"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#444", "tickfont": {"color": "#888"}},
            "bar": {"color": bar_color, "thickness": 0.28},
            "bgcolor": "#1a1a1a",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  40], "color": "#1a1a1a"},
                {"range": [40, 70], "color": "#222222"},
                {"range": [70, 100], "color": "#2a2a2a"},
            ],
            "threshold": {
                "line": {"color": bar_color, "width": 3},
                "thickness": 0.8,
                "value": confidence,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="#0f0f0f",
        plot_bgcolor="#0f0f0f",
        height=220,
        margin=dict(t=20, b=0, l=20, r=20),
        font={"color": "#f1f1f1"},
    )
    return fig


def timing_bar(days_to_trend: float) -> go.Figure:
    windows = [1, 7, 30, 180]
    labels  = ["< 1 day\nAct Now", "1–7 days\nEarly", "7–30 days\nGrowing", "30–180 days\nSlow Burn", "> 180 days\nEvergreen"]
    colors  = ["#ff3333", "#ff8800", "#ffcc00", "#00cc66", "#3399ff"]

    idx = 4
    if days_to_trend <= 1:   idx = 0
    elif days_to_trend <= 7:  idx = 1
    elif days_to_trend <= 30: idx = 2
    elif days_to_trend <= 180:idx = 3

    bar_colors = ["#282828"] * 5
    bar_colors[idx] = colors[idx]

    fig = go.Figure(go.Bar(
        x=labels,
        y=[1, 1, 1, 1, 1],
        marker_color=bar_colors,
        text=["" if i != idx else "▲ You are here" for i in range(5)],
        textposition="outside",
        textfont={"color": colors[idx], "size": 11},
    ))
    fig.update_layout(
        paper_bgcolor="#0f0f0f",
        plot_bgcolor="#0f0f0f",
        height=160,
        margin=dict(t=32, b=0, l=0, r=0),
        yaxis={"visible": False},
        xaxis={"tickfont": {"size": 10, "color": "#888"}, "tickcolor": "#282828"},
        showlegend=False,
        bargap=0.15,
    )
    fig.update_xaxes(linecolor="#282828", gridcolor="#0f0f0f")
    return fig


def engagement_radar(like_rate: float, comment_rate: float) -> go.Figure:
    categories = ["Like Rate", "Comment Rate", "Engagement Mix"]
    like_pct    = min(like_rate * 100 / 20 * 100, 100)    # 20% like_rate = 100%
    comment_pct = min(comment_rate * 100 / 5 * 100, 100)  # 5% comment_rate = 100%
    mix_pct     = (like_pct * 0.6 + comment_pct * 0.4)

    fig = go.Figure(go.Scatterpolar(
        r=[like_pct, comment_pct, mix_pct, like_pct],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(255, 0, 0, 0.15)",
        line={"color": "#ff3333", "width": 2},
        marker={"size": 6, "color": "#ff3333"},
    ))
    fig.update_layout(
        polar={
            "bgcolor": "#1a1a1a",
            "radialaxis": {"visible": True, "range": [0, 100], "tickfont": {"color": "#555"}, "gridcolor": "#282828"},
            "angularaxis": {"tickfont": {"color": "#aaa"}, "gridcolor": "#282828", "linecolor": "#282828"},
        },
        paper_bgcolor="#0f0f0f",
        height=240,
        margin=dict(t=16, b=16, l=16, r=16),
        showlegend=False,
    )
    return fig


# ─────────────────────────────────────────────
# Sidebar — inputs
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ▶ TrendScore")
    st.markdown("<p style='color:#666;font-size:0.8rem;margin-top:-8px;'>YouTube Trend Intelligence</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown("### Video Details")

    categories = fetch_categories()
    if not categories:
        st.warning("Could not load categories from API. Using defaults.")
        categories = {
            "Film & Animation": 1, "Autos & Vehicles": 2, "Music": 10,
            "Pets & Animals": 15, "Sports": 17, "Travel & Events": 19,
            "Gaming": 20, "People & Blogs": 22, "Comedy": 23,
            "Entertainment": 24, "News & Politics": 25, "Howto & Style": 26,
            "Education": 27, "Science & Technology": 28,
        }

    selected_category_name = st.selectbox(
        "Video Category",
        options=sorted(categories.keys()),
        index=sorted(categories.keys()).index("Gaming") if "Gaming" in categories else 0,
        help="YouTube category your video belongs to",
    )
    category_id = categories[selected_category_name]

    st.markdown("---")
    st.markdown("### Timing")

    now_utc = datetime.now(timezone.utc)
    publish_hour = st.slider(
        "Publish Hour (UTC)",
        min_value=0, max_value=23,
        value=now_utc.hour,
        format="%d:00",
        help="Hour you plan to (or did) publish, in UTC",
    )

    dow_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    publish_dow = st.selectbox(
        "Publish Day of Week",
        options=list(range(7)),
        format_func=lambda i: dow_labels[i],
        index=now_utc.weekday(),
    )

    days_to_trend = st.number_input(
        "Days Since Published",
        min_value=0.0, max_value=365.0,
        value=0.0, step=0.5,
        help="How many days ago the video was published (0 = not yet / just published)",
    )

    st.markdown("---")
    st.markdown("### Metadata")

    tag_count = st.slider(
        "Number of Tags",
        min_value=0, max_value=50,
        value=15,
        help="Tags you've added to the video",
    )

    st.markdown("---")
    st.markdown("### Engagement (if published)")

    like_rate = st.slider(
        "Like Rate  (likes ÷ views)",
        min_value=0.000, max_value=0.200,
        value=0.040, step=0.001,
        format="%.3f",
        help="Typical range: 0.01–0.08",
    )

    comment_rate = st.slider(
        "Comment Rate  (comments ÷ views)",
        min_value=0.000, max_value=0.050,
        value=0.005, step=0.001,
        format="%.3f",
        help="Typical range: 0.002–0.015",
    )

    st.markdown("---")
    predict_btn = st.button("▶  Analyse Trend", type="primary", use_container_width=True)

# ─────────────────────────────────────────────
# Hero header
# ─────────────────────────────────────────────

st.markdown("""
<div class="hero-header">
  <h1>▶ TrendScore</h1>
  <p>Know whether your next video will trend — and exactly when to hit publish.</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Initial state — before prediction
# ─────────────────────────────────────────────

if "result" not in st.session_state:
    st.session_state.result = None
    st.session_state.last_payload = None

if predict_btn:
    payload = {
        "category_id":   category_id,
        "days_to_trend": days_to_trend,
        "like_rate":     like_rate,
        "comment_rate":  comment_rate,
        "tag_count":     tag_count,
        "publish_hour":  publish_hour,
        "publish_dow":   publish_dow,
    }
    with st.spinner("Scoring your video…"):
        result = call_predict(payload)
    if result:
        st.session_state.result = result
        st.session_state.last_payload = payload

# ─────────────────────────────────────────────
# Results
# ─────────────────────────────────────────────

result  = st.session_state.result
payload = st.session_state.last_payload

if result is None:
    # Welcome state
    st.markdown("""
    <div style="background:#1a1a1a;border:1px solid #282828;border-radius:12px;padding:40px;text-align:center;">
        <div style="font-size:3rem;margin-bottom:12px;">▶</div>
        <h3 style="color:#f1f1f1;margin:0 0 8px;">Ready to score your video</h3>
        <p style="color:#888;margin:0;font-size:0.95rem;">
            Fill in your video details in the sidebar and click <strong>Analyse Trend</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="section-header">How it works</p>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    steps = [
        ("1", "Input your details", "Enter your video category, publish timing, tag count, and engagement metrics in the sidebar."),
        ("2", "AI scoring engine", "Our two-stage ML model — K-Means clustering + Gradient Boosting — classifies your video into a trend archetype."),
        ("3", "Act on the insight", "Get a precise timing window and personalised action plan to maximise your video's reach."),
    ]
    for col, (num, title, body) in zip([col1, col2, col3], steps):
        with col:
            st.markdown(f"""
            <div class="insight-box" style="text-align:center;">
                <div style="font-size:2rem;font-weight:900;color:#ff0000;margin-bottom:8px;">{num}</div>
                <div style="font-weight:700;color:#f1f1f1;margin-bottom:6px;">{title}</div>
                <div style="color:#888;font-size:0.85rem;">{body}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<p class="section-header">The 5 Trend Archetypes</p>', unsafe_allow_html=True)
    archetypes = [
        ("Flash Viral",       "red",    "⚡", "Explodes in 24 hours. Act now or skip."),
        ("Fast Mover",        "orange", "🚀", "Narrow 48-hour publish window."),
        ("Mid-Burn Trending", "yellow", "🔥", "3–5 day opportunity. Polish counts."),
        ("Sustained Grower",  "green",  "📈", "Week-long window. SEO matters."),
        ("Legacy Evergreen",  "blue",   "🌿", "Publish anytime. Think long-term."),
    ]
    cols = st.columns(5)
    palette = {"red": "#ff3333", "orange": "#ff8800", "yellow": "#ffcc00", "green": "#00cc66", "blue": "#3399ff"}
    for col, (name, color, icon, desc) in zip(cols, archetypes):
        c = palette[color]
        with col:
            st.markdown(f"""
            <div style="background:#1a1a1a;border:1px solid {c};border-radius:10px;padding:16px;text-align:center;">
                <div style="font-size:1.6rem;margin-bottom:8px;">{icon}</div>
                <div style="font-weight:700;color:{c};font-size:0.9rem;margin-bottom:6px;">{name}</div>
                <div style="color:#888;font-size:0.8rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

else:
    archetype    = result["archetype"]
    confidence   = result["confidence"]
    timing_txt   = result["timing"]
    recommendation = result["recommendation"]
    api_color    = result["color"]

    pal = ARCHETYPE_PALETTES.get(archetype, {"bg": "#1a1a1a", "border": "#ff0000", "text": "#ff4444"})
    icon = ARCHETYPE_ICONS.get(archetype, "▶")

    # ── Archetype banner ────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="archetype-card" style="background:{pal['bg']};border-color:{pal['border']};color:{pal['text']};">
        <h2>{icon} {archetype}</h2>
        <p>{timing_txt}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI row ─────────────────────────────────────────────────────────────
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.markdown(f"""
        <div class="metric-tile">
            <div class="label">Trend Confidence</div>
            <div class="value" style="color:{pal['text']};">{confidence}%</div>
            <div class="sub">Model confidence</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:
        days_label = f"{payload['days_to_trend']:.1f}d" if payload['days_to_trend'] > 0 else "Pre-publish"
        st.markdown(f"""
        <div class="metric-tile">
            <div class="label">Days to Trend</div>
            <div class="value">{days_label}</div>
            <div class="sub">Since publish</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi3:
        like_pct = f"{payload['like_rate']*100:.2f}%"
        st.markdown(f"""
        <div class="metric-tile">
            <div class="label">Like Rate</div>
            <div class="value">{like_pct}</div>
            <div class="sub">Likes ÷ Views</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi4:
        hour_label = f"{payload['publish_hour']:02d}:00 UTC"
        st.markdown(f"""
        <div class="metric-tile">
            <div class="label">Publish Time</div>
            <div class="value" style="font-size:1.4rem;">{hour_label}</div>
            <div class="sub">{dow_labels[payload['publish_dow']]}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts row ──────────────────────────────────────────────────────────
    chart_col1, chart_col2, chart_col3 = st.columns([1, 1.4, 1])

    with chart_col1:
        st.markdown('<p class="section-header">Trend Confidence</p>', unsafe_allow_html=True)
        st.plotly_chart(confidence_gauge(confidence, api_color), use_container_width=True, config={"displayModeBar": False})

    with chart_col2:
        st.markdown('<p class="section-header">Timing Window</p>', unsafe_allow_html=True)
        st.plotly_chart(timing_bar(payload["days_to_trend"]), use_container_width=True, config={"displayModeBar": False})

    with chart_col3:
        st.markdown('<p class="section-header">Engagement Signals</p>', unsafe_allow_html=True)
        st.plotly_chart(engagement_radar(payload["like_rate"], payload["comment_rate"]),
                        use_container_width=True, config={"displayModeBar": False})

    # ── Insight + Tips row ──────────────────────────────────────────────────
    insight_col, tips_col = st.columns([1, 1])

    with insight_col:
        st.markdown('<p class="section-header">AI Recommendation</p>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="insight-box" style="border-left:3px solid {pal['border']};">
            <div class="icon">{icon}</div>
            <div class="title">What the model says</div>
            <div class="body">{recommendation}</div>
        </div>
        """, unsafe_allow_html=True)

        # Video metadata summary
        st.markdown(f"""
        <div class="insight-box">
            <div class="title">Input Summary</div>
            <div class="body">
                <b style="color:#aaa">Category:</b> {selected_category_name}<br>
                <b style="color:#aaa">Tags:</b> {payload['tag_count']}<br>
                <b style="color:#aaa">Comment Rate:</b> {payload['comment_rate']*100:.3f}%<br>
                <b style="color:#aaa">Published:</b> {dow_labels[payload['publish_dow']]} at {payload['publish_hour']:02d}:00 UTC
            </div>
        </div>
        """, unsafe_allow_html=True)

    with tips_col:
        st.markdown('<p class="section-header">Creator Action Plan</p>', unsafe_allow_html=True)
        tips = ARCHETYPE_TIPS.get(archetype, [])
        tips_html = "".join(
            f'<div class="tip-item"><span class="tip-bullet">→</span><span>{tip}</span></div>'
            for tip in tips
        )
        st.markdown(f"""
        <div class="insight-box">
            <div class="title">5 steps for {archetype} videos</div>
            {tips_html}
        </div>
        """, unsafe_allow_html=True)

    # ── Archetype comparison ─────────────────────────────────────────────────
    st.markdown('<p class="section-header">Archetype Reference</p>', unsafe_allow_html=True)

    archetype_data = [
        {"Archetype": "⚡ Flash Viral",        "Timing Window": "< 24 hours",   "Urgency": 5, "SEO Weight": 1, "Production Value": 1, "Longevity": 1},
        {"Archetype": "🚀 Fast Mover",         "Timing Window": "48 hours",      "Urgency": 4, "SEO Weight": 2, "Production Value": 2, "Longevity": 2},
        {"Archetype": "🔥 Mid-Burn Trending",  "Timing Window": "3–5 days",      "Urgency": 3, "SEO Weight": 3, "Production Value": 3, "Longevity": 3},
        {"Archetype": "📈 Sustained Grower",   "Timing Window": "1+ week",       "Urgency": 2, "SEO Weight": 4, "Production Value": 4, "Longevity": 4},
        {"Archetype": "🌿 Legacy Evergreen",   "Timing Window": "Anytime",       "Urgency": 1, "SEO Weight": 5, "Production Value": 5, "Longevity": 5},
    ]
    df = pd.DataFrame(archetype_data)

    def highlight_row(row):
        matched = archetype in row["Archetype"]
        color = "background-color: #1a1a1a; color: #f1f1f1;" if not matched else \
                f"background-color: {pal['bg']}; color: {pal['text']}; font-weight: bold;"
        return [color] * len(row)

    styled = df.style.apply(highlight_row, axis=1).set_properties(**{
        "text-align": "center",
        "border": "1px solid #282828",
        "padding": "8px 12px",
    }).hide(axis="index")

    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Urgency":          st.column_config.ProgressColumn("Urgency",          min_value=0, max_value=5),
            "SEO Weight":       st.column_config.ProgressColumn("SEO Weight",       min_value=0, max_value=5),
            "Production Value": st.column_config.ProgressColumn("Production Value", min_value=0, max_value=5),
            "Longevity":        st.column_config.ProgressColumn("Longevity",        min_value=0, max_value=5),
        },
    )

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────

st.markdown("""
<hr style="border-color:#282828;margin:32px 0 16px;">
<p style="text-align:center;color:#444;font-size:0.8rem;">
    TrendScore · COMM-STEM × SUDATA Data Hack 2026 · Powered by scikit-learn & FastAPI
</p>
""", unsafe_allow_html=True)

import { useState, useEffect, useCallback } from "react";
import {
  fetchCategories,
  predict,
  scoreCsv,
  type CategoryItem,
  type PredictRequest,
  type PredictResponse,
} from "./api.ts";
import { ARCHETYPE_CONFIG, DOW_LABELS, ARCHETYPES_LIST } from "./constants";
import "./App.css";

// ─── Confidence Gauge ────────────────────────────────────────────
function ConfidenceGauge({ value, color }: { value: number; color: string }) {
  const radius = 54;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (value / 100) * circ * 0.75;
  const startAngle = 135;

  return (
    <div className="gauge-wrap">
      <svg viewBox="0 0 140 100" className="gauge-svg">
        {/* Track */}
        <circle
          cx="70" cy="80" r={radius}
          fill="none" stroke="#1e1e1e" strokeWidth="10"
          strokeDasharray={`${circ * 0.75} ${circ}`}
          strokeDashoffset="0"
          strokeLinecap="round"
          transform={`rotate(${startAngle} 70 80)`}
        />
        {/* Fill */}
        <circle
          cx="70" cy="80" r={radius}
          fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={`${circ * 0.75} ${circ}`}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(${startAngle} 70 80)`}
          style={{ transition: "stroke-dashoffset 1s ease" }}
        />
      </svg>
      <div className="gauge-label">
        <span className="gauge-value" style={{ color }}>{value}</span>
        <span className="gauge-unit">/100</span>
        <span className="gauge-sub">confidence</span>
      </div>
    </div>
  );
}

// ─── Timing Bar ──────────────────────────────────────────────────
function TimingBar({ days }: { days: number }) {
  const buckets = [
    { label: "Now", sub: "< 1 day",    color: "#ff3333", max: 1 },
    { label: "Early", sub: "1–7 days",   color: "#ff8800", max: 7 },
    { label: "Growing", sub: "7–30 days",  color: "#ffcc00", max: 30 },
    { label: "Slow Burn", sub: "30–180 days", color: "#00cc66", max: 180 },
    { label: "Evergreen", sub: "> 180 days", color: "#3399ff", max: Infinity },
  ];

  const activeIdx =
    days <= 1   ? 0 :
    days <= 7   ? 1 :
    days <= 30  ? 2 :
    days <= 180 ? 3 : 4;

  return (
    <div className="timing-bar">
      {buckets.map((b, i) => (
        <div key={i} className={`timing-bucket ${i === activeIdx ? "active" : ""}`}>
          <div
            className="timing-fill"
            style={{ background: i === activeIdx ? b.color : "#1e1e1e", borderColor: i === activeIdx ? b.color : "#2a2a2a" }}
          />
          <span className="timing-label" style={{ color: i === activeIdx ? b.color : "#555" }}>{b.label}</span>
          <span className="timing-sub">{b.sub}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Input Slider ────────────────────────────────────────────────
function InputSlider({
  label, value, min, max, step, format, onChange, help,
}: {
  label: string; value: number; min: number; max: number; step: number;
  format: (v: number) => string; onChange: (v: number) => void; help?: string;
}) {
  return (
    <div className="input-row">
      <div className="input-header">
        <label className="input-label">{label}</label>
        <span className="input-value">{format(value)}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="slider"
      />
      {help && <p className="input-help">{help}</p>}
    </div>
  );
}

// ─── Welcome Screen ──────────────────────────────────────────────
function WelcomeScreen() {
  return (
    <div className="welcome">
      <div className="welcome-hero">
        <div className="welcome-icon">▶</div>
        <h2>Ready to score your trend</h2>
        <p>Fill in your video details in the sidebar and click <strong>Analyse Trend</strong>.</p>
      </div>

      <div className="how-it-works">
        <p className="section-label">How it works</p>
        <div className="steps-grid">
          {[
            { n: "1", title: "Input your details", body: "Enter your video category, publish timing, tag count, and engagement metrics." },
            { n: "2", title: "AI scoring engine", body: "Two-stage ML model — K-Means clustering + Gradient Boosting — classifies your trend." },
            { n: "3", title: "Act on the insight", body: "Get a precise timing window and personalised action plan to maximise reach." },
          ].map(({ n, title, body }) => (
            <div className="step-card" key={n}>
              <div className="step-num">{n}</div>
              <div className="step-title">{title}</div>
              <div className="step-body">{body}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="archetypes-grid-section">
        <p className="section-label">The 5 Trend Archetypes</p>
        <div className="archetypes-grid">
          {ARCHETYPES_LIST.map(({ name, desc }) => {
            const cfg = ARCHETYPE_CONFIG[name];
            return (
              <div className="archetype-pill" key={name} style={{ borderColor: cfg.color }}>
                <span className="archetype-pill-icon">{cfg.icon}</span>
                <span className="archetype-pill-name" style={{ color: cfg.color }}>{name}</span>
                <span className="archetype-pill-desc">{desc}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ─── Result Screen ───────────────────────────────────────────────
function ResultScreen({ result, payload, categoryName }: {
  result: PredictResponse;
  payload: PredictRequest;
  categoryName: string;
}) {
  const cfg = ARCHETYPE_CONFIG[result.archetype] ?? {
    icon: "▶", color: "#ff0000", border: "#ff0000", bg: "#1a0000", text: "#ff4444", tips: [],
  };

  return (
    <div className="result">
      {/* Archetype Banner */}
      <div className="archetype-banner" style={{ background: cfg.bg, borderColor: cfg.border }}>
        <div className="archetype-banner-left">
          <span className="archetype-icon-large">{cfg.icon}</span>
          <div>
            <h2 className="archetype-name" style={{ color: cfg.text }}>{result.archetype}</h2>
            <p className="archetype-timing">{result.timing}</p>
          </div>
        </div>
        <div className="archetype-badge" style={{ background: cfg.color + "22", border: `1px solid ${cfg.color}`, color: cfg.color }}>
          {cfg.timing} window
        </div>
      </div>

      {/* KPI Row */}
      <div className="kpi-row">
        {[
          { label: "Confidence", value: `${result.confidence}/100`, sub: "Model score" },
          { label: "Days to Trend", value: payload.days_to_trend > 0 ? `${payload.days_to_trend}d` : "Pre-publish", sub: "Since publish" },
          { label: "Like Rate", value: `${(payload.like_rate * 100).toFixed(2)}%`, sub: "Likes ÷ Views" },
          { label: "Publish Time", value: `${String(payload.publish_hour).padStart(2, "0")}:00 UTC`, sub: DOW_LABELS[payload.publish_dow] },
        ].map(({ label, value, sub }) => (
          <div className="kpi-tile" key={label}>
            <span className="kpi-label">{label}</span>
            <span className="kpi-value" style={label === "Confidence" ? { color: cfg.color } : {}}>{value}</span>
            <span className="kpi-sub">{sub}</span>
          </div>
        ))}
      </div>

      {/* Gauge + Timing */}
      <div className="charts-row">
        <div className="chart-card">
          <p className="section-label">Trend Confidence</p>
          <ConfidenceGauge value={result.confidence} color={cfg.color} />
        </div>
        <div className="chart-card chart-card-wide">
          <p className="section-label">Timing Window</p>
          <TimingBar days={payload.days_to_trend} />
        </div>
        <div className="chart-card">
          <p className="section-label">Engagement</p>
          <div className="engagement-bars">
            <div className="eng-row">
              <span className="eng-label">Like Rate</span>
              <div className="eng-track">
                <div className="eng-fill" style={{ width: `${Math.min(payload.like_rate / 0.2 * 100, 100)}%`, background: cfg.color }} />
              </div>
              <span className="eng-pct">{(payload.like_rate * 100).toFixed(1)}%</span>
            </div>
            <div className="eng-row">
              <span className="eng-label">Comment Rate</span>
              <div className="eng-track">
                <div className="eng-fill" style={{ width: `${Math.min(payload.comment_rate / 0.05 * 100, 100)}%`, background: cfg.color }} />
              </div>
              <span className="eng-pct">{(payload.comment_rate * 100).toFixed(2)}%</span>
            </div>
            <div className="eng-row">
              <span className="eng-label">Tags</span>
              <div className="eng-track">
                <div className="eng-fill" style={{ width: `${Math.min(payload.tag_count / 50 * 100, 100)}%`, background: cfg.color }} />
              </div>
              <span className="eng-pct">{payload.tag_count}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendation + Tips */}
      <div className="insight-row">
        <div className="insight-card">
          <p className="section-label">AI Recommendation</p>
          <div className="insight-box" style={{ borderLeftColor: cfg.border }}>
            <div className="insight-icon">{cfg.icon}</div>
            <p className="insight-title">What the model says</p>
            <p className="insight-body">{result.recommendation}</p>
          </div>
          <div className="insight-box">
            <p className="insight-title">Input Summary</p>
            <div className="summary-grid">
              <span className="summary-key">Category</span><span className="summary-val">{categoryName}</span>
              <span className="summary-key">Tags</span><span className="summary-val">{payload.tag_count}</span>
              <span className="summary-key">Comment Rate</span><span className="summary-val">{(payload.comment_rate * 100).toFixed(3)}%</span>
              <span className="summary-key">Published</span><span className="summary-val">{DOW_LABELS[payload.publish_dow]} {String(payload.publish_hour).padStart(2, "0")}:00 UTC</span>
            </div>
          </div>
        </div>

        <div className="tips-card">
          <p className="section-label">Creator Action Plan</p>
          <div className="tips-box">
            <p className="insight-title">5 steps for {result.archetype} videos</p>
            {cfg.tips.map((tip, i) => (
              <div className="tip-row" key={i}>
                <span className="tip-arrow" style={{ color: cfg.color }}>→</span>
                <span className="tip-text">{tip}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Archetype Reference Table */}
      <div className="reference-section">
        <p className="section-label">Archetype Reference</p>
        <div className="reference-table">
          <div className="ref-header">
            <span>Archetype</span><span>Window</span><span>Urgency</span><span>SEO</span><span>Production</span><span>Longevity</span>
          </div>
          {[
            { name: "Flash Viral",       window: "< 24h",   urgency: 5, seo: 1, prod: 1, long: 1 },
            { name: "Fast Mover",        window: "48h",      urgency: 4, seo: 2, prod: 2, long: 2 },
            { name: "Mid-Burn Trending", window: "3–5 days", urgency: 3, seo: 3, prod: 3, long: 3 },
            { name: "Sustained Grower",  window: "1+ week",  urgency: 2, seo: 4, prod: 4, long: 4 },
            { name: "Legacy Evergreen",  window: "Anytime",  urgency: 1, seo: 5, prod: 5, long: 5 },
          ].map((row) => {
            const c = ARCHETYPE_CONFIG[row.name];
            const isActive = row.name === result.archetype;
            return (
              <div className={`ref-row ${isActive ? "ref-row-active" : ""}`} key={row.name}
                style={isActive ? { background: c.bg, borderColor: c.border } : {}}>
                <span style={{ color: isActive ? c.text : "#ccc" }}>{c.icon} {row.name}</span>
                <span style={{ color: isActive ? c.color : "#888" }}>{row.window}</span>
                {[row.urgency, row.seo, row.prod, row.long].map((val, i) => (
                  <div className="ref-bar-wrap" key={i}>
                    <div className="ref-bar-track">
                      <div className="ref-bar-fill" style={{ width: `${val / 5 * 100}%`, background: isActive ? c.color : "#333" }} />
                    </div>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ─── CSV Upload Tab ───────────────────────────────────────────────
function CsvTab() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setDone(false);
    try {
      const blob = await scoreCsv(file);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "trend_scores.csv";
      a.click();
      URL.revokeObjectURL(url);
      setDone(true);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="csv-tab">
      <div className="csv-hero">
        <h2>Batch Score Your Videos</h2>
        <p>Upload a CSV with YouTube trending data. We'll score every row and return a downloadable results file.</p>
      </div>

      <div className="csv-required">
        <p className="section-label">Required Columns</p>
        <div className="col-chips">
          {["title", "category_id", "views", "likes", "comments", "publish_time", "trending_date", "tags"].map((c) => (
            <span className="col-chip" key={c}>{c}</span>
          ))}
        </div>
      </div>

      <div
        className={`drop-zone ${file ? "drop-zone-filled" : ""}`}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          const f = e.dataTransfer.files[0];
          if (f?.name.endsWith(".csv")) setFile(f);
        }}
        onClick={() => document.getElementById("csv-input")?.click()}
      >
        <input
          id="csv-input" type="file" accept=".csv" style={{ display: "none" }}
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        {file ? (
          <div className="drop-filled">
            <span className="drop-file-icon">📄</span>
            <span className="drop-filename">{file.name}</span>
            <span className="drop-filesize">{(file.size / 1024).toFixed(1)} KB</span>
          </div>
        ) : (
          <div className="drop-empty">
            <span className="drop-icon">↑</span>
            <span className="drop-text">Drop your CSV here or click to browse</span>
          </div>
        )}
      </div>

      {error && <div className="csv-error">{error}</div>}
      {done && <div className="csv-success">✓ Download started — check your Downloads folder for trend_scores.csv</div>}

      <button
        className="analyse-btn"
        onClick={handleUpload}
        disabled={!file || loading}
        style={{ marginTop: "1.5rem", width: "100%", maxWidth: "400px" }}
      >
        {loading ? "Scoring rows…" : "Score & Download CSV"}
      </button>
    </div>
  );
}

// ─── Main App ────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState<"manual" | "csv">("manual");
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [selectedCatId, setSelectedCatId] = useState<number>(24);
  const [daysToTrend, setDaysToTrend] = useState(0);
  const [likeRate, setLikeRate] = useState(0.04);
  const [commentRate, setCommentRate] = useState(0.005);
  const [tagCount, setTagCount] = useState(15);
  const [publishHour, setPublishHour] = useState(new Date().getUTCHours());
  const [publishDow, setPublishDow] = useState(new Date().getUTCDay() === 0 ? 6 : new Date().getUTCDay() - 1);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [lastPayload, setLastPayload] = useState<PredictRequest | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCategories()
      .then(setCategories)
      .catch(() => {});
  }, []);

  const selectedCat = categories.find((c) => c.id === selectedCatId);

  const handleAnalyse = useCallback(async () => {
    setLoading(true);
    setError(null);
    const payload: PredictRequest = {
      category_id: selectedCatId,
      days_to_trend: daysToTrend,
      like_rate: likeRate,
      comment_rate: commentRate,
      tag_count: tagCount,
      publish_hour: publishHour,
      publish_dow: publishDow,
    };
    try {
      const res = await predict(payload);
      setResult(res);
      setLastPayload(payload);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [selectedCatId, daysToTrend, likeRate, commentRate, tagCount, publishHour, publishDow]);

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">▶</span>
          <div>
            <div className="brand-name">TrendScore</div>
            <div className="brand-sub">YouTube Trend Intelligence</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button className={`nav-btn ${tab === "manual" ? "active" : ""}`} onClick={() => setTab("manual")}>
            Manual Score
          </button>
          <button className={`nav-btn ${tab === "csv" ? "active" : ""}`} onClick={() => setTab("csv")}>
            CSV Upload
          </button>
        </nav>

        {tab === "manual" && (
          <div className="sidebar-form">
            <p className="sidebar-section">Video Details</p>

            <div className="input-row">
              <label className="input-label">Category</label>
              <select
                className="select-input"
                value={selectedCatId}
                onChange={(e) => setSelectedCatId(Number(e.target.value))}
              >
                {[...categories].sort((a, b) => a.name.localeCompare(b.name)).map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            <p className="sidebar-section">Timing</p>

            <InputSlider
              label="Days Since Published" value={daysToTrend} min={0} max={365} step={0.5}
              format={(v) => v === 0 ? "Pre-publish" : `${v}d`}
              onChange={setDaysToTrend}
            />

            <div className="input-row">
              <label className="input-label">Publish Hour (UTC)</label>
              <select className="select-input" value={publishHour} onChange={(e) => setPublishHour(Number(e.target.value))}>
                {Array.from({ length: 24 }, (_, i) => (
                  <option key={i} value={i}>{String(i).padStart(2, "0")}:00</option>
                ))}
              </select>
            </div>

            <div className="input-row">
              <label className="input-label">Day of Week</label>
              <select className="select-input" value={publishDow} onChange={(e) => setPublishDow(Number(e.target.value))}>
                {DOW_LABELS.map((d, i) => <option key={i} value={i}>{d}</option>)}
              </select>
            </div>

            <p className="sidebar-section">Metadata</p>

            <InputSlider
              label="Number of Tags" value={tagCount} min={0} max={50} step={1}
              format={(v) => `${v} tags`}
              onChange={setTagCount}
            />

            <p className="sidebar-section">Engagement</p>

            <InputSlider
              label="Like Rate" value={likeRate} min={0} max={0.2} step={0.001}
              format={(v) => `${(v * 100).toFixed(1)}%`}
              onChange={setLikeRate}
              help="likes ÷ views, typical: 1–8%"
            />

            <InputSlider
              label="Comment Rate" value={commentRate} min={0} max={0.05} step={0.001}
              format={(v) => `${(v * 100).toFixed(2)}%`}
              onChange={setCommentRate}
              help="comments ÷ views, typical: 0.2–1.5%"
            />

            {error && <div className="sidebar-error">{error}</div>}

            <button className="analyse-btn" onClick={handleAnalyse} disabled={loading}>
              {loading ? "Scoring…" : "▶  Analyse Trend"}
            </button>
          </div>
        )}
      </aside>

      {/* Main */}
      <main className="main">
        <header className="top-bar">
          <div className="top-bar-hero">
            <h1>▶ TrendScore</h1>
            <p>Know whether your next video will trend — and exactly when to hit publish.</p>
          </div>
        </header>

        <div className="content">
          {tab === "csv" ? (
            <CsvTab />
          ) : result && lastPayload ? (
            <ResultScreen result={result} payload={lastPayload} categoryName={selectedCat?.name ?? ""} />
          ) : (
            <WelcomeScreen />
          )}
        </div>
      </main>
    </div>
  );
}
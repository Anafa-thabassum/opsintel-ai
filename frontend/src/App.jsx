
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity, AlertTriangle, ArrowDownRight, ArrowRight, Bot,
  ChevronDown, ChevronRight, CircleDot,
  Database, FileSearch, GitBranch, LayoutDashboard, LoaderCircle, LockKeyhole,
  RefreshCw, Search, ShieldCheck, Sparkles, Sun, Moon, Terminal, Zap,
} from "lucide-react";
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip,
  XAxis, YAxis,
} from "recharts";
import "./App.css";
import VerifiedMemory from "./VerifiedMemory";
import PublicData from "./PublicData";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const categoryLabels = {
  incomplete_data: "Incomplete data",
  early_termination: "Early termination",
  timeout: "Timeout",
  schema_mismatch: "Schema mismatch",
  dependency_failure: "Dependency failure",
  delayed_run: "Delayed run",
  duplicate_data: "Duplicate data",
  conflicting_evidence: "Conflicting evidence",
  unclassified: "Unknown — evidence insufficient",
};

function navigate(route) {
  window.location.hash = `/${route}`;
}

function App() {
  const currentRoute = window.location.hash.replace(/^#\/?/, "") || "home";
  const [route, setRoute] = useState(currentRoute);
  const [hasDemoSession, setHasDemoSession] = useState(
    () => sessionStorage.getItem("opsintel-demo-session") === "true"
  );

  useEffect(() => {
    const handleHashChange = () => {
      setRoute(window.location.hash.replace(/^#\/?/, "") || "home");
    };
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  if (route === "dashboard" && hasDemoSession) {
    return <Dashboard onExit={() => {
      sessionStorage.removeItem("opsintel-demo-session");
      setHasDemoSession(false);
      navigate("home");
    }} />;
  }

  if (route === "public") return <PublicData />;
  if (route === "scorecard") return <PublicScorecard />;

  if (route === "login" || route === "dashboard") {
    return <DemoAccess onEnter={() => {
      sessionStorage.setItem("opsintel-demo-session", "true");
      setHasDemoSession(true);
      navigate("dashboard");
    }} />;
  }

  return <LandingPage />;
}

function Brand() {
  return (
    <span className="public-brand">
      <span className="brand-mark"><Activity size={23} /></span>
      <span>
        <span className="brand-name">opsintel<span>AI</span></span>
        <span className="brand-caption">OPERATIONS INTELLIGENCE</span>
      </span>
    </span>
  );
}

function LandingPage() {
  return (
    <div className="public-shell">
      <header className="public-nav">
        <a href="#/home" aria-label="OpsIntel AI home"><Brand /></a>
        <div className="public-nav-actions">
          <span className="track-chip">EXATHON INDIA 2026 · TRACK 04</span>
          <button className="ghost-button" onClick={() => navigate("login")}>Demo access</button>
        </div>
      </header>

      <main>
        <section className="hero-section">
          <div className="hero-copy">
            <div className="eyebrow"><Sparkles size={14} /> EVIDENCE-BASED PIPELINE INVESTIGATION</div>
            <h1>Investigate pipeline failures from <span>evidence—not guesswork.</span></h1>
            <p>OpsIntel brings pipeline status, row-count discrepancies, and logs into one traceable investigation so data engineers know what to check next.</p>
            <div className="hero-actions">
              <button className="primary-button hero-button" onClick={() => navigate("public")}>Investigate public incidents <ArrowRight size={16} /></button>
              <button className="secondary-button" onClick={() => navigate("scorecard")}>View classifier scorecard</button>
              <button className="secondary-button" onClick={() => navigate("login")}>Open synthetic demo</button>
              <a className="secondary-link" href="https://github.com/Anafa-thabassum/opsintel-ai" target="_blank" rel="noreferrer"><GitBranch size={16} /> View repository</a>
            </div>
            <div className="hero-trust"><ShieldCheck size={16} /><span>No automated repair. Root causes remain unconfirmed until a human verifies them.</span></div>
          </div>

          <div className="evidence-preview" aria-label="Public Apache Airflow issue excerpt">
            <div className="preview-top"><span>APACHE AIRFLOW · ISSUE #46378</span><span className="status-badge public"><span />PUBLIC SOURCE</span></div>
            <div className="preview-title"><FileSearch size={20} /><span>Source error excerpt</span></div>
            <blockquote className="public-excerpt">AirflowTaskTimeout: DagBag import timeout</blockquote>
            <div className="preview-step"><Database size={15} /><div><strong>Source category</strong><span>dag_parse_or_import_timeout</span></div></div>
            <div className="preview-step violet"><Sparkles size={15} /><div><strong>OpsIntel mapping</strong><span>timeout · project-mapped label</span></div></div>
            <div className="preview-confirm"><ShieldCheck size={15} /> <a href="https://github.com/apache/airflow/issues/46378" target="_blank" rel="noreferrer">Open public source issue</a></div>
          </div>
        </section>

        <section className="public-features" aria-label="How OpsIntel works">
          <div><Database size={20} /><span>01</span><h2>Analyze in Exasol</h2><p>SQL analytical views calculate completeness, rolling baselines, and incident context close to the data.</p></div>
          <div><FileSearch size={20} /><span>02</span><h2>Follow the evidence</h2><p>Every observation points back to a pipeline record or log instead of presenting an unsupported answer.</p></div>
          <div><ShieldCheck size={20} /><span>03</span><h2>Confirm carefully</h2><p>Rules and an optional LLM suggest what to inspect; a human remains responsible for confirmation and action.</p></div>
        </section>
      </main>

      <footer className="public-footer"><span>Follow the evidence. Investigate faster. Confirm carefully.</span><span>ExaThon India 2026</span></footer>
    </div>
  );
}

function PublicScorecard() {
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API}/scorecard/public`)
      .then((response) => {
        if (!response.ok) throw new Error(`Public scorecard returned HTTP ${response.status}`);
        return response.json();
      })
      .then(setReport)
      .catch((err) => setError(err.message || "Unable to load the public scorecard."));
  }, []);

  return (
    <div className="public-shell scorecard-shell">
      <header className="public-nav">
        <a href="#/home" aria-label="OpsIntel AI home"><Brand /></a>
        <div className="public-nav-actions">
          <span className="track-chip">PUBLIC SOURCE CORPUS · V2</span>
          <button className="ghost-button" onClick={() => navigate("home")}>Back to overview</button>
        </div>
      </header>
      <main className="scorecard-content">
        <div className="eyebrow"><ShieldCheck size={14} /> PUBLIC-DATA SCORECARD</div>
        <h1>Classifier compatibility on sourced failure messages</h1>
        <p className="page-subtitle">Real excerpts from public Apache Airflow and dbt issue records. No generated incidents, run counts, or trend data.</p>
        {error && <div className="error-banner">{error}</div>}
        {!report && !error && <div className="panel">Loading public corpus…</div>}
        {report && <>
          <section className="scorecard-summary">
            <div className="metric-card"><div className="metric-top">Exact category matches</div><div className="metric-value">{report.correct}/{report.total}</div><div className="metric-detail">{report.accuracy_pct}% on this project-mapped corpus</div></div>
            <div className="metric-card"><div className="metric-top">Public cases</div><div className="metric-value">{report.total}</div><div className="metric-detail">Apache Airflow and dbt sources</div></div>
          </section>
          <p className="scorecard-notice">{report.data_notice} {report.transformations}</p>
          <section className="scorecard-cases" aria-label="Public source cases">
            {report.results.map((item) => <article className="panel scorecard-case" key={item.id}>
              <div className="scorecard-case-heading"><div><span className="panel-kicker">{item.id} · {item.project}</span><h2>{item.correct ? "Category matched" : "Category mismatch"}</h2></div><span className={`scorecard-result ${item.correct ? "matched" : "mismatch"}`}>{item.predicted}</span></div>
              <blockquote>{item.excerpt}</blockquote>
              <div className="scorecard-labels"><span>Source label: <strong>{item.source_category}</strong></span><span>OpsIntel mapping: <strong>{item.expected}</strong></span><span>Classifier: <strong>{item.predicted}</strong></span></div>
              <p>{item.labelling_rationale || item.labelling_note}</p>
              <div className="scorecard-sources"><a href={item.source_url} target="_blank" rel="noreferrer">Public source</a><a href={item.license_url} target="_blank" rel="noreferrer">Repository licence</a><span>{item.license}</span></div>
            </article>)}
          </section>
        </>}
      </main>
    </div>
  );
}

function DemoAccess({ onEnter }) {
  const [email, setEmail] = useState("");

  return (
    <div className="access-shell">
      <a className="access-brand" href="#/home"><Brand /></a>
      <main className="access-card">
        <div className="access-icon"><LockKeyhole size={22} /></div>
        <div className="eyebrow">JUDGE DEMO ACCESS</div>
        <h1>Enter the investigation workspace</h1>
        <p>Use any valid email address to create a temporary session in this browser.</p>
        <form onSubmit={(event) => { event.preventDefault(); onEnter(); }}>
          <label htmlFor="demo-email">Email address</label>
          <input id="demo-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="judge@example.com" required autoFocus />
          <button className="primary-button access-button" type="submit">Continue to workspace <ArrowRight size={16} /></button>
        </form>
        <div className="demo-disclosure"><ShieldCheck size={15} /><span>Hackathon demo gate only—not production authentication. No password or personal data is stored.</span></div>
        <button className="text-button" onClick={() => navigate("home")}>← Back to overview</button>
      </main>
    </div>
  );
}

function Dashboard({ onExit }) {
  const [theme, setTheme] = useState(() => localStorage.getItem("opsintel-theme") || "dark");
  const [incidents, setIncidents] = useState([]);
  const [trend, setTrend] = useState([]);
  const [cascades, setCascades] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [investigation, setInvestigation] = useState(null);
  const [rootCauses, setRootCauses] = useState(null);
  const [health, setHealth] = useState("checking");
  const [loading, setLoading] = useState(true);
  const [investigating, setInvestigating] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [activeNav, setActiveNav] = useState("Overview");
  const [refreshKey, setRefreshKey] = useState(0);
  const [reviewByRun, setReviewByRun] = useState({});
  const investigationRequest = useRef(0);
  const [trendError, setTrendError] = useState("");
  const [confirmedCount, setConfirmedCount] = useState(null);
  const [confirmedRecord, setConfirmedRecord] = useState(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("opsintel-theme", theme);
  }, [theme]);
  
  async function loadIncidents() {
    setLoading(true);
    setError("");
    setTrendError("");

    try {
      const [healthResult, incidentsResult, trendResult, cascadeResult] = await Promise.allSettled([
        fetch(`${API}/health`),
        fetch(`${API}/incidents`),
        fetch(`${API}/analytics/trend`),
        fetch(`${API}/analytics/cascades`),
      ]);

      const healthResponse = healthResult.status === "fulfilled" ? healthResult.value : null;
      const incidentsResponse = incidentsResult.status === "fulfilled" ? incidentsResult.value : null;
      const trendResponse = trendResult.status === "fulfilled" ? trendResult.value : null;
      const cascadeResponse = cascadeResult.status === "fulfilled" ? cascadeResult.value : null;

      setHealth(healthResponse?.ok ? "connected" : "error");

      if (!incidentsResponse?.ok) {
        const detail = incidentsResponse
          ? `Incident API returned HTTP ${incidentsResponse.status}`
          : "Unable to connect to the incident API";
        throw new Error(detail);
      }

      const data = await incidentsResponse.json();
      const rows = Array.isArray(data.incidents) ? data.incidents : [];
      setIncidents(rows);

      if (trendResponse?.ok) {
        try {
          const trendData = await trendResponse.json();
          if (Array.isArray(trendData.trend)) {
            setTrend(trendData.trend);
            setTrendError("");
          } else {
            setTrend([]);
            setTrendError("Trend API returned an invalid data format.");
          }
        } catch {
          setTrend([]);
          setTrendError("Unable to read trend analytics data.");
        }
      } else {
        setTrend([]);
        setTrendError(
          trendResponse
            ? `Trend analytics returned HTTP ${trendResponse.status}.`
            : "Unable to connect to the trend analytics endpoint."
        );
      }

      if (cascadeResponse?.ok) {
        try {
          const cascadeData = await cascadeResponse.json();
          setCascades(Array.isArray(cascadeData.cascades) ? cascadeData.cascades : []);
        } catch {
          setCascades([]);
        }
      } else {
        setCascades([]);
      }

      const nextId = rows.some((item) => item.run_id === selectedId)
        ? selectedId
        : rows[0]?.run_id ?? null;

      setSelectedId(nextId);
    } catch (err) {
      setHealth("error");
      setError(
        err?.message || "Unable to connect to the OpsIntel API. Make sure your FastAPI server is running at 127.0.0.1:8000."
      );
      setIncidents([]);
      setTrend([]);
      setCascades([]);
      setSelectedId(null);
    } finally {
      setLoading(false);
    }
  }

  
async function loadInvestigation(runId) {
  if (runId == null) return;

  const requestId = ++investigationRequest.current;

  setInvestigating(true);
  setError("");
  setInvestigation(null);
  setRootCauses(null);

  try {
    const investigationResponse = await fetch(`${API}/investigate/${runId}`);

    if (!investigationResponse.ok) {
      throw new Error(
        `Investigation returned HTTP ${investigationResponse.status}`
      );
    }

    const data = await investigationResponse.json();

    if (requestId !== investigationRequest.current) return;

    setInvestigation(data);
    setRootCauses(data.root_causes || null);
  } catch (err) {
    if (requestId !== investigationRequest.current) return;

    setError(err.message || "Unable to load this investigation.");
  } finally {
    if (requestId === investigationRequest.current) {
      setInvestigating(false);
    }
  }
}


  useEffect(() => {
    loadIncidents();
  }, [refreshKey]);

  useEffect(() => {
    if (selectedId != null) loadInvestigation(selectedId);
  }, [selectedId]);

  const filteredIncidents = useMemo(() => {
    return incidents.filter((incident) => {
      const matchesSearch = incident.pipeline_name
        .toLowerCase()
        .includes(search.toLowerCase());
      const matchesFilter = filter === "all" || incident.status === filter;
      return matchesSearch && matchesFilter;
    });
  }, [incidents, search, filter]);

  const totalMissing = incidents.reduce(
    (total, item) => total + Number(item.missing_rows ?? 0),
    0
  );

  const chartData = useMemo(
    () => trend.map((item) => ({
      time: item.run_day?.slice(5) ?? "Unknown",
      incidents: Number(item.incident_count ?? 0),
      dailyFailureRate:
        item.daily_failure_rate_pct == null
          ? null
          : Number(item.daily_failure_rate_pct),
    })),
    [trend]
  );

  const cascadeGroups = useMemo(() => {
    const groups = new Map();
    for (const cascade of cascades) {
      const key = `${cascade.root_run_id}`;
      if (!groups.has(key)) groups.set(key, {
        root_pipeline: cascade.root_pipeline,
        root_run_id: cascade.root_run_id,
        root_run_time: cascade.root_run_time,
        edges: [],
      });
      groups.get(key).edges.push(cascade);
    }
    return [...groups.values()];
  }, [cascades]);

  const formatNumber = (value) => value == null
    ? "Unknown"
    : Number(value).toLocaleString("en-IN");
  const completeness = (expected, actual) => {
    if (expected == null || actual == null) return null;
    if (Number(expected) === 0) return Number(actual) === 0 ? 100 : null;
    return Math.round((Number(actual) / Number(expected)) * 100);
  };
  const formatComparisonValue = (difference, value) => (
    value == null
      ? "Unknown"
      : difference.unit === "percentage points"
      ? `${Number(value).toFixed(1)}%`
      : formatNumber(value)
  );
  const formatDelta = (difference) => {
    if (difference.delta == null) return "Unknown";
    const value = Number(difference.delta);
    const suffix = difference.unit === "percentage points" ? " pp" : "";
    return `${value > 0 ? "+" : ""}${value.toLocaleString("en-IN")}${suffix}`;
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={(e) => e.preventDefault()}>
          <div className="brand-mark"><Activity size={23} /></div>
          <div>
            <div className="brand-name">opsintel<span>AI</span></div>
            <div className="brand-caption">OPERATIONS INTELLIGENCE</div>
          </div>
        </a>

        <div className="workspace-label">WORKSPACE</div>
        <nav className="nav-list">
          {[
            { label: "Overview", icon: LayoutDashboard },
            { label: "Incidents", icon: AlertTriangle },
            { label: "Investigations", icon: FileSearch },
            { label: "Verified Memory", icon: ShieldCheck },
            { label: "Public Data", icon: Database },
          ].map(({ label, icon: Icon }) => (
            <button
              key={label}
              className={`nav-item ${activeNav === label ? "active" : ""}`}
              onClick={() => {
                setActiveNav(label);
                if (label === "Incidents") {
                  document.getElementById("incident-list")?.scrollIntoView({ behavior: "smooth" });
                } else if (label === "Investigations") {
                  document.getElementById("investigation-panel")?.scrollIntoView({ behavior: "smooth" });
                } else if (label === "Verified Memory") {
                  document.getElementById("verified-memory")?.scrollIntoView({ behavior: "smooth" });
                } else if (label === "Public Data") {
                  navigate("public");
                } else {
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }
              }}
            >
              <Icon size={18} />
              <span>{label}</span>
              {label === "Incidents" && <span className="nav-count">{incidents.length}</span>}
            </button>
          ))}
        </nav>

        <div className="workspace-label system-label">SYSTEM</div>
        <div className="system-card">
          <div className="system-card-icon"><Database size={17} /></div>
          <div className="system-copy">
            <strong>Exasol database</strong>
            <span><i className={`status-dot ${health === "connected" ? "online" : ""}`} />{health === "connected" ? "Connected" : health === "checking" ? "Connecting…" : "Disconnected"}</span>
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="avatar">OI</div>
          <div className="profile-copy">
            <strong>OpsIntel Workspace</strong>
            <span>Hackathon environment</span>
          </div>
          <ChevronDown size={15} className="muted-icon" />
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span><ChevronRight size={14} /><strong>{activeNav}</strong>
          </div>
          <div className="topbar-actions">
            <div className="live-indicator"><span /> SYSTEM {health === "connected" ? "OPERATIONAL" : health === "checking" ? "CHECKING" : "DEGRADED"}</div>
            <button className="icon-button" title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`} onClick={() => setTheme((value) => value === "dark" ? "light" : "dark")}>{theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}</button>
            <button className="icon-button" title="Refresh data" onClick={() => setRefreshKey((n) => n + 1)}><RefreshCw size={17} /></button>
            <button className="top-avatar" title="Exit demo workspace" aria-label="Exit demo workspace" onClick={onExit}>A</button>
          </div>
        </header>

        <div className="page-content">
          <section className="welcome-row">
            <div>
              <div className="eyebrow"><Sparkles size={14} /> INTELLIGENCE OVERVIEW</div>
              <h1>Operations <span>command center</span></h1>
              <p className="page-subtitle">Understand failures. Follow the evidence. Restore reliability.</p>
            </div>
            <button className="primary-button" onClick={() => setRefreshKey((n) => n + 1)}>
              <RefreshCw size={16} /> Refresh intelligence
            </button>
          </section>

          {error && <div className="error-banner"><AlertTriangle size={17} />{error}</div>}

          <section className="metric-grid">
            <MetricCard
              label="Pipeline incidents"
              value={loading ? "—" : formatNumber(incidents.length)}
              detail="Requires investigation"
              icon={AlertTriangle}
              tone="red"
              trend="Live API data"
            />
            <MetricCard
              label="Known rows missing"
              value={loading ? "—" : formatNumber(totalMissing)}
              detail="Across runs with row counts"
              icon={Database}
              tone="purple"
              trend="Data quality signal"
            />
            <MetricCard
              label="Evidence records"
              value={investigation ? formatNumber(investigation.evidence?.length) : "—"}
              detail="Selected investigation"
              icon={FileSearch}
              tone="cyan"
              trend="Traceable observations"
            />
            <MetricCard
              label="Confirmed causes"
              value={confirmedCount == null ? "—" : formatNumber(confirmedCount)}
              detail={confirmedCount == null ? "Connect verified memory to view" : "Reviewer-confirmed records"}
              icon={ShieldCheck}
              tone="green"
              trend="Exasol verified memory"
            />
          </section>

          <section className="overview-grid">
            <div className="panel chart-panel">
              <div className="panel-heading">
                <div>
                  <div className="panel-kicker">INCIDENT TELEMETRY</div>
                  <h2>Failure activity</h2>
                </div>
                <span className="subtle-pill"><span className="mini-dot" /> Exasol analytics</span>
              </div>

              <div className="chart-summary">
                <strong>{loading ? "—" : incidents.length}</strong>
                <span>Incidents across pipeline history</span>
              </div>

              <div className="chart-wrap">
                {loading ? (
                  <div className="empty-state">
                    <LoaderCircle className="spin" size={22} />
                    Loading trend analytics…
                  </div>
                ) : trendError ? (
                  <div className="empty-state" role="status">
                    <AlertTriangle size={20} />
                    <span>{trendError}</span>
                  </div>
                ) : chartData.length === 0 ? (
                  <div className="empty-state">No trend data available yet.</div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={chartData}
                      margin={{ top: 8, right: 8, left: -22, bottom: 0 }}
                    >
                      <defs>
                        <linearGradient id="incidentFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#8b7cff" stopOpacity={0.32} />
                          <stop offset="100%" stopColor="#8b7cff" stopOpacity={0} />
                        </linearGradient>
                      </defs>

                      <CartesianGrid stroke="#20273a" strokeDasharray="3 5" vertical={false} />

                      <XAxis
                        dataKey="time"
                        tick={{ fill: "#7f8ba5", fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                      />

                      <YAxis
                        yAxisId="count"
                        allowDecimals={false}
                        tick={{ fill: "#7f8ba5", fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                      />

                      <YAxis
                        yAxisId="rate"
                        orientation="right"
                        domain={[0, 100]}
                        tickFormatter={(value) => `${value}%`}
                        tick={{ fill: "#f59e0b", fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                      />

                      <Tooltip
                        contentStyle={{
                          background: "#121827",
                          border: "1px solid #303951",
                          borderRadius: 10,
                          color: "#f1f4ff",
                        }}
                        labelStyle={{ color: "#aab4cc" }}
                        formatter={(value, name) => [
                          value == null
                            ? "Unavailable"
                            : name === "Daily failure rate"
                              ? `${Number(value).toFixed(1)}%`
                              : Number(value).toLocaleString("en-IN"),
                          name,
                        ]}
                      />

                      <Area
                        type="monotone"
                        dataKey="incidents"
                        name="Daily incidents"
                        yAxisId="count"
                        stroke="#9c8cff"
                        strokeWidth={2.5}
                        fill="url(#incidentFill)"
                      />

                      <Area
                        type="monotone"
                        dataKey="dailyFailureRate"
                        name="Daily failure rate"
                        yAxisId="rate"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        fill="none"
                        connectNulls={false}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>

              <div className="chart-footer">
                <span><i className="legend-dot" /> Daily incidents</span>
                <span><i className="legend-dot" style={{ background: "#f59e0b" }} /> Daily failure rate (%)</span>
                <span>Calculated from pipeline history in Exasol</span>
              </div>
            </div>

            <div className="panel signal-panel">
              <div className="panel-heading">
                <div>
                  <div className="panel-kicker">SYSTEM STATUS</div>
                  <h2>Operational health</h2>
                </div>
                <Activity size={18} className="muted-icon" />
              </div>
              <div className="health-orb">
                <div className="orb-ring ring-one" />
                <div className="orb-ring ring-two" />
                <div className="orb-center"><Activity size={31} /></div>
              </div>
              <div className="health-title">{health === "connected" ? "Data source reachable" : health === "checking" ? "Checking connection" : "Connection needs attention"}</div>
              <p className="health-description">{health === "connected" ? "FastAPI and the database health endpoint responded successfully." : "Check that your API server is running."}</p>
              <div className="service-list">
                <ServiceRow name="FastAPI service" status={health === "connected"} />
                <ServiceRow name="Exasol connection" status={health === "connected"} />
                <ServiceRow name="Incident endpoint" status={!error && !loading} />
                <ServiceRow name="Cascade analytics" status={!error && !loading} />
              </div>
            </div>
          </section>

          {cascades.length > 0 && (
            <section className="panel cascade-panel" aria-label="Cross-pipeline failure cascade">
              <div className="panel-heading">
                <div>
                  <div className="panel-kicker">EXASOL CONNECT BY</div>
                  <h2>Cross-pipeline failure cascade</h2>
                  <p className="panel-description">Failures occurred downstream within a 120-minute window. Temporal correlation — causation not confirmed.</p>
                </div>
                <span className="subtle-pill"><GitBranch size={12} /> {cascades.length} downstream failures</span>
              </div>
              <div className="dependency-graph" aria-label="Interactive dependency failure graph">
                {cascadeGroups.map((group) => <div className="dependency-graph-row" key={group.root_run_id}>
                  <button className="dependency-node root" onClick={() => setSelectedId(group.root_run_id)} aria-label={`Investigate root ${group.root_pipeline}, run ${group.root_run_id}`}>
                    <small>ROOT FAILURE</small><strong>{group.root_pipeline}</strong><span>RUN-{String(group.root_run_id).padStart(4, "0")} · {group.root_run_time}</span>
                  </button>
                  <div className="dependency-edges" aria-label={`Downstream pipelines from ${group.root_pipeline}`}>
                    {group.edges.map((cascade) => <button className="dependency-edge" key={`${cascade.root_run_id}-${cascade.downstream_run_id}`} onClick={() => setSelectedId(cascade.downstream_run_id)} aria-label={`Investigate downstream ${cascade.downstream_pipeline}, run ${cascade.downstream_run_id}`}>
                      <span className="dependency-edge-line" aria-hidden="true">→</span>
                      <span className="dependency-node downstream"><small>DEPTH {cascade.dependency_depth} · +{Number(cascade.correlation_lag_minutes).toFixed(1)} MIN</small><strong>{cascade.downstream_pipeline}</strong><span>RUN-{String(cascade.downstream_run_id).padStart(4, "0")} · {cascade.downstream_run_time}</span><em>{cascade.dependency_path}</em></span>
                    </button>)}
                  </div>
                </div>)}
              </div>
            </section>
          )}

          <section className="panel incidents-panel" id="incident-list">
            <div className="panel-heading incident-heading">
              <div>
                <div className="panel-kicker">LIVE FROM EXASOL</div>
                <h2>Pipeline incidents <span className="count-chip">{incidents.length}</span></h2>
                <p className="panel-description">Select an incident to inspect its evidence and diagnostic recommendations.</p>
              </div>
              <div className="table-tools">
                <div className="search-box"><Search size={15} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search pipelines..." /></div>
                <select value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Filter incidents">
                  <option value="all">All statuses</option>
                  <option value="FAILED">Failed</option>
                  <option value="SUCCESS">Success</option>
                </select>
              </div>
            </div>

            <div className="incident-table">
              <div className="table-header">
                <span>PIPELINE / RUN</span><span>STATUS</span><span>ROW COMPLETENESS</span><span>MISSING</span><span />
              </div>
              {loading ? (
                <div className="empty-state"><LoaderCircle className="spin" size={22} /> Loading incidents from Exasol…</div>
              ) : filteredIncidents.length === 0 ? (
                <div className="empty-state">No matching incidents found.</div>
              ) : filteredIncidents.map((item) => {
                const completenessPct = completeness(
                  item.expected_rows,
                  item.actual_rows
                );
                const isSelected = item.run_id === selectedId;

                return (
                  <button
                    key={item.run_id}
                    className={`incident-row ${isSelected ? "selected" : ""}`}
                    onClick={() => setSelectedId(item.run_id)}
                  >
                    <span className="pipeline-cell">
                      <span className={`pipeline-icon ${isSelected ? "selected-icon" : ""}`}><GitBranch size={16} /></span>
                      <span><strong>{item.pipeline_name}</strong><small>RUN-{String(item.run_id).padStart(4, "0")}</small></span>
                    </span>
                    <span><span className={`status-badge ${item.status === "FAILED" ? "failed" : "success"}`}><span />{item.status}</span></span>
                    <span className="completeness-cell">
                      <span className="completeness-meta">{completenessPct == null ? "Unknown" : `${completenessPct}%`}<small>{formatNumber(item.actual_rows)} / {formatNumber(item.expected_rows)}</small></span>
                      <span className="progress-track"><span style={{ width: `${Math.min(100, completenessPct ?? 0)}%` }} /></span>
                    </span>
                    <span className={`missing-value ${item.missing_rows > 0 ? "has-missing" : ""}`}>{formatNumber(item.missing_rows)}</span>
                    <span className="row-chevron"><ChevronRight size={17} /></span>
                  </button>
                );
              })}
            </div>
            <div className="table-footer"><span><CircleDot size={13} /> Data retrieved from your API</span><span>{filteredIncidents.length} visible · {incidents.length} total</span></div>
          </section>

          <section className="investigation-layout" id="investigation-panel">
            <div className="panel investigation-panel">
              <div className="panel-heading">
                <div>
                  <div className="panel-kicker"><Sparkles size={12} /> INVESTIGATION ENGINE</div>
                  <h2>AI investigation copilot</h2>
                </div>
                <span className="ai-status"><span /> ANALYSIS READY</span>
              </div>

              {investigating ? (
                <div className="investigating-state"><div className="ai-loader"><Sparkles size={23} /></div><strong>Inspecting pipeline evidence</strong><span>Retrieving logs and diagnostic candidates…</span></div>
              ) : investigation ? (
                <>
                  <div className="selected-pipeline-banner">
                    <div className="selected-pipeline-icon"><Bot size={21} /></div>
                    <div className="selected-pipeline-copy"><span>SELECTED INCIDENT · RUN #{investigation.run_id}</span><strong>{investigation.pipeline_name}</strong></div>
                    <span className="confidence-badge"><span /> LOW CONFIDENCE</span>
                  </div>

                  <div className="hypothesis-block">
                    <div className="hypothesis-heading"><Sparkles size={16} /> Evidence-based assessment</div>
                    <h3>{categoryLabels[investigation.category] || investigation.category}</h3>
                    <p>{investigation.hypothesis}</p>
                    <div className="assessment-tags"><span><ShieldCheck size={13} /> Cause unconfirmed</span><span><FileSearch size={13} /> {investigation.evidence?.length || 0} evidence items</span></div>
                  </div>

                  {investigation.comparison?.status === "available" && (
                    <section className="run-diff-panel" aria-label="Failed run compared with last successful run">
                      <div className="run-diff-heading">
                        <div>
                          <span>WHAT CHANGED</span>
                          <h3>Failed run vs last successful run</h3>
                        </div>
                        <span>RUN-{String(investigation.run_id).padStart(4, "0")} vs RUN-{String(investigation.comparison.last_successful_run.run_id).padStart(4, "0")}</span>
                      </div>
                      <div className="run-diff-table">
                        <div className="run-diff-row run-diff-labels"><span>Metric</span><span>Failed</span><span>Last success</span><span>Change</span></div>
                        {investigation.comparison.differences.map((difference) => (
                          <div className="run-diff-row" key={difference.metric}>
                            <strong>{difference.metric}</strong>
                            <span>{formatComparisonValue(difference, difference.current)}</span>
                            <span>{formatComparisonValue(difference, difference.baseline)}</span>
                            <em className={Number(difference.delta) < 0 ? "negative" : Number(difference.delta) > 0 ? "positive" : ""}>{formatDelta(difference)}</em>
                            {difference.supports?.length > 0 && (
                              <small>Supports: {difference.supports.join("; ")}</small>
                            )}
                          </div>
                        ))}
                      </div>
                      <div className="baseline-summary">
                        Historical successful baseline: {formatNumber(investigation.comparison.historical_baseline.average_actual_rows)} average rows, {investigation.comparison.historical_baseline.average_completeness_pct == null ? "unknown" : `${Number(investigation.comparison.historical_baseline.average_completeness_pct).toFixed(1)}%`} completeness across {investigation.comparison.historical_baseline.successful_runs} runs.
                      </div>
                      {investigation.comparison.new_or_changed_logs.length > 0 && (
                        <div className="log-diff-list">
                          <strong>New or changed in the failed run</strong>
                          {investigation.comparison.new_or_changed_logs.map((log) => (
                            <div key={log.log_id}><span>{log.level}</span><p>{log.message}</p><em>{log.reference}</em></div>
                          ))}
                        </div>
                      )}
                    </section>
                  )}

                  {investigation.comparison?.status === "unavailable" && (
                    <div className="comparison-unavailable"><GitBranch size={14} />{investigation.comparison.message}</div>
                  )}

                  <div className="decision-grid" aria-label="Evidence, candidates, and verification state">
                    <section className="decision-column observation-column">
                      <div className="decision-column-heading"><Database size={14} /><span>01 · Observed facts</span><em>{investigation.evidence?.length || 0}</em></div>
                      <div className="evidence-list">
                        {(investigation.evidence || []).map((item, index) => (
                          <div className="evidence-item" key={`${item.type}-${item.log_id ?? index}`}>
                            <div className={`evidence-marker ${item.type === "pipeline_log" ? "log-marker" : ""}`}>
                              {item.type === "pipeline_log" ? <Terminal size={14} /> : <Database size={14} />}
                            </div>
                            <div className="evidence-copy">
                              <em>OBSERVED FACT</em>
                              <p>{item.observation}</p>
                              <span>{item.source}{item.log_id != null ? ` · LOG-${item.log_id}` : item.run_id != null ? ` · RUN-${item.run_id}` : ""}{item.timestamp ? ` · ${item.timestamp}` : ""}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </section>

                    <section className="decision-column candidate-column">
                      <div className="decision-column-heading"><Sparkles size={14} /><span>02 · Candidate causes</span><em>{rootCauses?.candidates?.length || 0}</em></div>
                      {(rootCauses?.candidates || []).map((candidate, index) => (
                        <div className="candidate-card" key={`${candidate.cause}-${index}`}>
                          <div className="candidate-number">{String(index + 1).padStart(2, "0")}</div>
                          <div className="candidate-copy">
                            <strong>{candidate.cause}</strong>
                            <p>{candidate.next_action}</p>
                            <span>CANDIDATE · {candidate.status.replaceAll("_", " ")}</span>
                            <div className="candidate-evidence">
                              {(candidate.supporting_evidence || []).map((item) => <em key={item.reference}>{item.reference}</em>)}
                            </div>
                          </div>
                        </div>
                      ))}
                      {rootCauses?.resolution_status === "unresolved" && (
                        <div className="unresolved-state"><AlertTriangle size={15} /><strong>Unresolved</strong><p>{rootCauses.unresolved_reason}</p><span>No candidate was created from insufficient evidence.</span></div>
                      )}
                      {!rootCauses && <div className="column-placeholder">Candidate retrieval pending.</div>}
                    </section>

                    <section className="decision-column confirmation-column">
                      <div className="decision-column-heading"><ShieldCheck size={14} /><span>03 · Human confirmation</span></div>
                      <div className="verification-state">
                        <span>{confirmedRecord?.run_id === investigation.run_id ? "REVIEWER CONFIRMED IN EXASOL" : "NOT YET VERIFIED"}</span>
                        <strong>{confirmedRecord?.run_id === investigation.run_id ? confirmedRecord.confirmed_description : "No confirmed root cause"}</strong>
                        <p>{confirmedRecord?.run_id === investigation.run_id ? `Reviewed by ${confirmedRecord.confirmed_by} at ${confirmedRecord.confirmed_at}. New matches still require their own review.` : "The system does not promote a candidate or run a repair."}</p>
                      </div>
                      <div className="recommendation-card">
                        <div className="recommendation-icon"><Zap size={17} /></div>
                        <div><span>NEXT SAFE CHECK</span><p>{investigation.recommended_action}</p></div>
                      </div>
                    </section>
                  </div>

                  {investigation.llm_summary?.status === "generated" && (
                    <div className="llm-summary-card">
                      <div className="llm-summary-heading">
                        <span><Sparkles size={14} /> Optional LLM summary</span>
                        <span>NARRATIVE ONLY</span>
                      </div>
                      <div className="llm-claims">
                        {(investigation.llm_summary.claims || []).map((claim, index) => (
                          <div className="llm-claim" key={`${claim.statement}-${index}`}>
                            <p>{claim.statement}</p>
                            <div>{claim.evidence_refs.map((reference) => <span key={reference}>{reference}</span>)}</div>
                          </div>
                        ))}
                      </div>
                      {investigation.llm_summary.evidence_gaps?.length > 0 && (
                        <div className="llm-evidence-gaps">
                          <strong>Evidence still needed</strong>
                          <ul>
                            {investigation.llm_summary.evidence_gaps.map((gap, index) => (
                              <li key={`${gap}-${index}`}>{gap}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <div className="llm-safety-note">
                        <ShieldCheck size={14} />
                        <span>{investigation.llm_summary.safety_note}</span>
                      </div>
                    </div>
                  )}

                  {investigation.llm_summary && investigation.llm_summary.status !== "generated" && (
                    <div className="llm-fallback">
                      <Sparkles size={14} />
                      <span>Optional LLM {investigation.llm_summary.status}. The deterministic investigation remains available.</span>
                    </div>
                  )}

                  <div className="limitations-note"><ShieldCheck size={15} /><span>{investigation.limitations?.[0] || "Recommendations are diagnostic suggestions, not executed repairs."}</span></div>
                </>
              ) : (
                <div className="empty-state">{error || "Select a pipeline incident to start an investigation."}</div>
              )}
            </div>

            <aside className="panel side-insights">
              <div className="panel-heading"><div><div className="panel-kicker">DIAGNOSTIC CONTEXT</div><h2>Run intelligence</h2></div><FileSearch size={18} className="muted-icon" /></div>

              {investigation ? (
                <>
                  <div className="run-stat"><span>Pipeline status</span><strong className="danger-text"><span className="status-dot" /> {investigation.status}</strong></div>
                  <div className="run-stat"><span>Expected rows</span><strong>{formatNumber(investigation.expected_rows)}</strong></div>
                  <div className="run-stat"><span>Received rows</span><strong>{formatNumber(investigation.actual_rows)}</strong></div>
                  <div className="run-stat"><span>Missing rows</span><strong className={investigation.missing_rows > 0 ? "danger-text" : ""}>{formatNumber(investigation.missing_rows)}</strong></div>

                  <div className="row-comparison">
                    <div className="comparison-head"><span>Data completeness</span><strong>{completeness(investigation.expected_rows, investigation.actual_rows) == null ? "Unknown" : `${completeness(investigation.expected_rows, investigation.actual_rows)}%`}</strong></div>
                    <div className="large-progress"><span style={{ width: `${Math.min(100, completeness(investigation.expected_rows, investigation.actual_rows) ?? 0)}%` }} /></div>
                    <div className="comparison-legend"><span>Received</span><span>Expected</span></div>
                  </div>

                  {investigation.history?.length > 0 && (
                    <div className="history-block">
                      <div className="section-title"><span>Recent run timeline</span><span>EXASOL HISTORY</span></div>
                      <div className="history-list">
                        {investigation.history.map((run) => (
                          <div className="history-item" key={run.run_id}>
                            <span className={`history-dot ${run.status === "SUCCESS" ? "success" : "failed"}`} />
                            <div><strong>RUN-{String(run.run_id).padStart(4, "0")}</strong><span>{run.run_time}</span></div>
                            <small>{run.status} · {formatNumber(run.actual_rows)}/{formatNumber(run.expected_rows)}</small>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="context-card"><div className="context-icon"><Activity size={17} /></div><div><strong>Investigation limitations</strong><p>{investigation.limitations?.[1] || "Root cause remains unconfirmed."}</p></div></div>
                  <div className="context-card"><div className="context-icon violet"><ShieldCheck size={17} /></div><div><strong>Safe recommendations</strong><p>No automated repair was executed. Review the evidence before taking action.</p></div></div>

                  <div className="verification-card">
                    <div><ShieldCheck size={16} /><strong>Engineer review</strong></div>
                    <select
                      aria-label="Engineer review status"
                      value={reviewByRun[investigation.run_id] || "unreviewed"}
                      onChange={(event) => setReviewByRun((current) => ({
                        ...current,
                        [investigation.run_id]: event.target.value,
                      }))}
                    >
                      <option value="unreviewed">Not reviewed</option>
                      <option value="evidence-reviewed">Evidence reviewed</option>
                      <option value="needs-more-evidence">Needs more evidence</option>
                      <option value="candidate-rejected">Candidate rejected</option>
                    </select>
                    <p>Demo-session record only. This does not confirm a root cause.</p>
                  </div>
                </>
              ) : (
                <div className="empty-state">Investigation details will appear here.</div>
              )}
            </aside>
          </section>

          <VerifiedMemory api={API} investigation={investigation} onCountChange={setConfirmedCount} onRecordChange={setConfirmedRecord} />

          <footer className="app-footer">
            <div><span className={`status-dot ${health === "connected" ? "online" : ""}`} /> OpsIntel API · {health === "connected" ? "Connected" : health === "checking" ? "Connecting" : "Unavailable"}</div>
            <span>Evidence first. Root causes only when verified.</span>
            <span>OpsIntel AI · Hackathon build</span>
          </footer>
        </div>
      </main>
    </div>
  );
}

function MetricCard({ label, value, detail, icon: Icon, tone, trend }) {
  return (
    <div className="metric-card">
      <div className="metric-top"><span>{label}</span><div className={`metric-icon ${tone}`}><Icon size={18} /></div></div>
      <div className="metric-value">{value}</div>
      <div className="metric-detail">{detail}</div>
      <div className="metric-trend"><span className={`trend-symbol ${tone}`}><ArrowDownRight size={14} /></span>{trend}</div>
    </div>
  );
}

function ServiceRow({ name, status }) {
  return (
    <div className="service-row"><span>{name}</span><span className={`service-status ${status ? "good" : "waiting"}`}><i />{status ? "Operational" : "Checking"}</span></div>
  );
}

export default App;

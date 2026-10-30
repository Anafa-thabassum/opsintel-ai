import { useEffect, useState } from "react";
import { Activity, ArrowLeft, ArrowUpRight, Database, FileSearch, Filter, Search, ShieldCheck } from "lucide-react";
import "./PublicData.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function categoryName(value) {
  return value === "unclassified" ? "Unresolved" : value?.replaceAll("_", " ") || "Unknown";
}

function date(value) {
  return value ? String(value).slice(0, 10) : "Unknown";
}

export default function PublicData() {
  const [sources, setSources] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [records, setRecords] = useState([]);
  const [total, setTotal] = useState(0);
  const [source, setSource] = useState("");
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [selectedKey, setSelectedKey] = useState("");
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    Promise.all(["/public/sources", "/public/analytics", "/public/evaluation"].map(async (path) => {
      const response = await fetch(`${API}${path}`);
      if (!response.ok) throw new Error(`Public data API returned HTTP ${response.status}`);
      return response.json();
    })).then(([registry, activity, report]) => {
      if (!cancelled) {
        setSources(registry.sources || []);
        setAnalytics(activity);
        setEvaluation(report);
      }
    }).catch((err) => { if (!cancelled) setError(err.message); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setLoading(true);
      setError("");
      const params = new URLSearchParams({ limit: "20", offset: String(page * 20) });
      if (source) params.set("source", source);
      if (category) params.set("category", category);
      if (search.trim()) params.set("search", search.trim());
      try {
        const response = await fetch(`${API}/public/incidents?${params}`, { signal: controller.signal });
        if (!response.ok) throw new Error(`Public incident search returned HTTP ${response.status}`);
        const data = await response.json();
        setRecords(data.incidents || []);
        setTotal(data.total || 0);
        setSelectedKey((key) => data.incidents?.some((item) => item.source_key === key) ? key : data.incidents?.[0]?.source_key || "");
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message || "Unable to load public records.");
          setRecords([]);
          setTotal(0);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 220);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [source, category, search, page]);

  const selected = records.find((item) => item.source_key === selectedKey)
    || (selectedRecord?.source_key === selectedKey ? selectedRecord : null);
  useEffect(() => {
    if (!selected) { setSimilar([]); return; }
    const controller = new AbortController();
    const path = `${selected.source_repository}/${selected.issue_number}`;
    fetch(`${API}/public/similar/${path}`, { signal: controller.signal })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("Similarity unavailable")))
      .then((data) => setSimilar(data.matches || []))
      .catch((err) => { if (err.name !== "AbortError") setSimilar([]); });
    return () => controller.abort();
  }, [selected?.source_key]);

  const changeFilter = (setter) => (event) => { setter(event.target.value); setPage(0); setSelectedRecord(null); };
  const openSimilar = async (item) => {
    try {
      const [repository, number] = item.source_key.split("#");
      const response = await fetch(`${API}/public/incidents/${repository}/${number}`);
      if (!response.ok) throw new Error(`Public issue returned HTTP ${response.status}`);
      setSelectedRecord(await response.json());
      setSelectedKey(item.source_key);
    } catch (err) { setError(err.message || "Unable to load the similar record."); }
  };
  const categoryCounts = Object.entries((analytics?.groups || []).reduce((counts, item) => {
    counts[item.category] = (counts[item.category] || 0) + item.count;
    return counts;
  }, {})).sort((left, right) => right[1] - left[1]);

  return <div className="public-investigation-shell">
    <header className="public-data-header">
      <a href="#/home" className="public-data-brand"><Activity size={22} /><span>opsintel<strong>AI</strong></span></a>
      <nav aria-label="Public data navigation"><a href="#/dashboard"><ArrowLeft size={15} /> Synthetic workspace</a><a href="#/scorecard">Historical scorecard <ArrowUpRight size={14} /></a></nav>
    </header>
    <main className="public-data-main">
      <div className="public-data-eyebrow"><Database size={14} /> EXASOL · PUBLIC ISSUE RECORDS</div>
      <div className="public-data-intro"><div><h1>Public Data Investigation</h1><p>Trace actual Apache Airflow and dbt issue evidence through deterministic symptom classification. Source text remains unverified as a root cause.</p></div><span className="public-data-live"><span /> Locally cached in Exasol</span></div>
      {error && <div className="public-data-error" role="alert">{error}</div>}
      <div className="public-data-metrics" aria-label="Public data coverage">
        <div><span>Collected issues</span><strong>{analytics?.total ?? "—"}</strong><small>Verified source URLs</small></div>
        <div><span>Unresolved</span><strong>{analytics?.unresolved ?? "—"}</strong><small>Insufficient category evidence</small></div>
        <div><span>Project label matches</span><strong>{evaluation ? `${evaluation.exact_category_matches}/${evaluation.project_labelled}` : "—"}</strong><small>Not independent validation</small></div>
        <div><span>Source traceability</span><strong>{evaluation ? `${Math.round(evaluation.evidence_coverage * 100)}%` : "—"}</strong><small>Source and signal references</small></div>
      </div>
      <p className="public-data-caveat"><ShieldCheck size={16} /> Issue labels are project mappings. GitHub issue text has no separately established redistribution licence. Only short screened excerpts are cached locally; open the original issue for full context.</p>
      <section className="public-data-distribution" aria-label="Public classifier distribution"><div><span>CLASSIFICATION MIX</span><h2>Evidence coverage by category</h2><p>Current Exasol collection · {analytics?.total ?? "—"} issues</p></div><div className="public-data-bars">{categoryCounts.map(([name, count]) => <div className="public-data-bar-row" key={name}><span>{categoryName(name)}</span><div><i style={{ width: `${analytics?.total ? count / analytics.total * 100 : 0}%` }} /></div><strong>{count}</strong></div>)}</div></section>
      <div className="public-data-workspace">
        <section className="public-data-list" aria-label="Public issue list">
          <div className="public-data-section-head"><div><span>RECORD BROWSER</span><h2>Investigate source issues</h2></div><span>{total} records</span></div>
          <div className="public-data-filters"><label className="public-data-search"><Search size={16} /><input aria-label="Search public issues" value={search} onChange={changeFilter(setSearch)} placeholder="Search issue evidence" /></label><div><label><Filter size={14} /><select aria-label="Source" value={source} onChange={changeFilter(setSource)}><option value="">All sources</option>{sources.map((item) => <option key={item.repository} value={item.repository}>{item.name}</option>)}</select></label><select aria-label="Classifier category" value={category} onChange={changeFilter(setCategory)}><option value="">All categories</option>{["timeout", "schema_mismatch", "dependency_failure", "early_termination", "incomplete_data", "delayed_run", "duplicate_data", "unclassified"].map((item) => <option key={item} value={item}>{categoryName(item)}</option>)}</select></div></div>
          <div className="public-data-rows">{loading && <div className="public-data-empty">Loading public records…</div>}{!loading && !records.length && <div className="public-data-empty">No records match these filters. Try another source or term.</div>}{!loading && records.map((item) => <button key={item.source_key} className={`public-data-row ${selectedKey === item.source_key ? "selected" : ""}`} onClick={() => { setSelectedRecord(null); setSelectedKey(item.source_key); }}><span className="public-data-row-top"><small>{item.source_name} · #{item.issue_number}</small><small>{date(item.source_created_at)}</small></span><strong>{item.title}</strong><span className="public-data-row-bottom"><em className={item.classifier_category === "unclassified" ? "unresolved" : "supported"}>{categoryName(item.classifier_category)}</em><small>{item.source_state}</small></span></button>)}</div>
          {total > 20 && <div className="public-data-pager"><button disabled={page === 0} onClick={() => setPage((n) => n - 1)}>Previous</button><span>Page {page + 1} of {Math.ceil(total / 20)}</span><button disabled={(page + 1) * 20 >= total} onClick={() => setPage((n) => n + 1)}>Next</button></div>}
        </section>
        <section className="public-data-detail" aria-label="Public issue investigation">
          {!selected ? <div className="public-data-empty detail-empty"><FileSearch size={24} /><strong>Select a public issue</strong><span>Its source, evidence and classification will appear here.</span></div> : <>
            <div className="public-data-detail-head"><span>ISSUE INVESTIGATION · {selected.source_key}</span><a href={selected.source_url} target="_blank" rel="noreferrer">Open original <ArrowUpRight size={14} /></a></div>
            <h2>{selected.title}</h2><div className="public-data-meta"><span>Opened {date(selected.source_created_at)}</span><span>Updated {date(selected.source_updated_at)}</span><span>Collected {date(selected.collected_at)}</span></div>
            <div className="public-data-divider" />
            <div className="public-data-detail-section"><h3>Source evidence</h3><p className="public-data-evidence-ref">github:{selected.source_key}:{selected.excerpt_origin}</p><blockquote>{selected.excerpt}</blockquote><p className="public-data-subtext">A screened excerpt from the issue {selected.excerpt_origin.replaceAll("-", " ")}; its source body SHA-256 is {selected.body_sha256.slice(0, 14)}…</p></div>
            <div className="public-data-detail-section"><h3>Symptom assessment</h3><div className="public-data-assessment"><span className={selected.classification.status === "unresolved" ? "unresolved" : "supported"}>{selected.classification.status === "unresolved" ? "Unresolved" : "Supported symptom"}</span><strong>{categoryName(selected.classifier_category)}</strong></div><p>{selected.classification.unresolved_reason || "A symptom category is supported by the cited excerpt. The underlying cause is unconfirmed."}</p>{(selected.classification.signals || []).map((signal, index) => <div className="public-data-signal" key={`${signal.category}-${index}`}><span>{categoryName(signal.category)} · {signal.method}</span><small>{signal.evidence_refs?.join(", ") || "No source reference"}</small></div>)}<div className="public-data-cause">Confirmed root cause <strong>None — this issue has not been independently reviewed in OpsIntel.</strong></div></div>
            <div className="public-data-detail-section"><h3>Similar public records</h3><p>Textual neighbours only. Their descriptions are not verified explanations.</p>{similar.length ? similar.map((item) => <button className="public-data-similar" key={item.source_key} onClick={() => openSimilar(item)}><strong>{item.title}</strong><small>{item.source_key} · score {item.similarity_score.toFixed(2)} · shared {item.matching_tokens.slice(0, 3).join(", ")}</small></button>) : <p className="public-data-subtext">No sufficiently similar public excerpt in this collection.</p>}</div>
            <div className="public-data-detail-section public-data-provenance"><h3>Provenance and terms</h3><dl><dt>Repository</dt><dd>{selected.source_repository}</dd><dt>API source</dt><dd><a href={selected.source_url} target="_blank" rel="noreferrer">{selected.source_url}</a></dd><dt>Project label</dt><dd>{categoryName(selected.project_label)} · {selected.label_status.replaceAll("_", " ")}</dd><dt>Code licence</dt><dd><a href={selected.code_license_url} target="_blank" rel="noreferrer">{selected.code_license}</a></dd><dt>Issue text</dt><dd>{selected.issue_text_license_status}</dd></dl></div>
          </>}
        </section>
      </div>
      <footer className="public-data-footer">Public issue evidence · local Exasol cache · no automatic cause confirmation</footer>
    </main>
  </div>;
}

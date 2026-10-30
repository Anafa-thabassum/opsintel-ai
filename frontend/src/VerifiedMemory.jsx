import { useEffect, useState } from "react";

const LABEL = "Candidate based on verified historical incident — engineer verification required.";

export default function VerifiedMemory({ api, investigation, onCountChange, onRecordChange }) {
  const [token, setToken] = useState("");
  const [connected, setConnected] = useState(false);
  const [role, setRole] = useState("");
  const [records, setRecords] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [matches, setMatches] = useState(null);
  const [history, setHistory] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [category, setCategory] = useState("");
  const [cause, setCause] = useState("");
  const [selectedRefs, setSelectedRefs] = useState([]);
  const [causalRefs, setCausalRefs] = useState([]);
  const [sourceUri, setSourceUri] = useState("");
  const [sourceExcerpt, setSourceExcerpt] = useState("");
  const [reviewId, setReviewId] = useState("");
  const [reviewRationale, setReviewRationale] = useState("");
  const [unresolvedConflicts, setUnresolvedConflicts] = useState("");
  const [criteria, setCriteria] = useState([]);
  const [criteriaVersion, setCriteriaVersion] = useState("");

  const runId = investigation?.run_id;
  const existingRecord = records.find((item) => item.run_id === runId);
  const current = existingRecord?.status === "active" ? existingRecord : null;
  const pending = submissions.filter((item) => item.status === "pending");
  const selectedSubmission = submissions.find((item) => item.submission_id === reviewId);

  async function request(path, options = {}) {
    const response = await fetch(`${api}${path}`, {
      ...options,
      headers: { Authorization: `Bearer ${token}`, ...(options.body ? { "Content-Type": "application/json" } : {}) },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : `Memory API returned HTTP ${response.status}`);
    return data;
  }

  async function refresh() {
    if (!token) return;
    setBusy(true);
    setError("");
    try {
      const [memory, queue, stats] = await Promise.all([request("/memory/incidents"), request("/memory/submissions"), request("/memory/analytics")]);
      setRecords(memory.incidents || []);
      onCountChange((memory.incidents || []).filter((item) => item.status === "active").length);
      setSubmissions(queue.submissions || []);
      setRole(queue.role || "investigator");
      setAnalytics(stats);
      setConnected(true);
      if (runId != null) {
        const [similar, events] = await Promise.all([request(`/memory/similar/${runId}`), request(`/memory/history/${runId}`)]);
        setMatches(similar);
        setHistory(events.events || []);
      }
    } catch (err) {
      setError(err.message);
      setConnected(false);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    onRecordChange(current || null);
  }, [runId, records]);

  useEffect(() => {
    if (!connected || runId == null) return;
    let cancelled = false;
    Promise.all([request(`/memory/similar/${runId}`), request(`/memory/history/${runId}`)])
      .then(([similar, events]) => { if (!cancelled) { setMatches(similar); setHistory(events.events || []); } })
      .catch((err) => { if (!cancelled) setError(err.message); });
    return () => { cancelled = true; };
  }, [runId, connected]);

  useEffect(() => {
    setCategory(investigation?.classification?.symptom_category || "");
    setSelectedRefs([]);
    setCausalRefs([]);
    setCause("");
  }, [runId]);

  useEffect(() => {
    setUnresolvedConflicts("");
    setReviewRationale("");
    if (!selectedSubmission || !connected) { setCriteria([]); return; }
    request(`/memory/criteria/${selectedSubmission.category}`)
      .then((data) => { setCriteriaVersion(data.version); setCriteria((data.required || []).map((id) => ({ id, passed: false, method: "", result: "", evidence_refs: [] }))); })
      .catch((err) => setError(err.message));
  }, [reviewId, connected]);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const existing = (investigation?.evidence || []).filter((item) => selectedRefs.includes(item.reference))
      .map((item) => ({ reference: item.reference, excerpt: item.observation, kind: causalRefs.includes(item.reference) ? "causal" : "symptom" }));
    const external = sourceUri && sourceExcerpt ? [{ reference: sourceUri, source_uri: sourceUri, excerpt: sourceExcerpt, kind: "causal" }] : [];
    try {
      await request("/memory/submissions", { method: "POST", body: JSON.stringify({
        run_id: runId, category, cause_description: cause, evidence: [...existing, ...external],
        kind: existingRecord ? "correction" : "new", source_incident_id: existingRecord?.incident_id || null,
      }) });
      setCause("");
      setSourceUri("");
      setSourceExcerpt("");
      await refresh();
    } catch (err) { setError(err.message); setBusy(false); }
  }

  async function review(decision) {
    if (decision === "approve" && !window.confirm("Approve this cause after independently checking every cited source and criterion?")) return;
    setBusy(true);
    setError("");
    try {
      await request(`/memory/submissions/${reviewId}/review`, { method: "POST", body: JSON.stringify({
        decision, rationale: reviewRationale,
        checklist: { version: criteriaVersion, criteria,
          unresolved_conflicts: unresolvedConflicts.split("\n").map((item) => item.trim()).filter(Boolean) },
      }) });
      setReviewId("");
      setReviewRationale("");
      setUnresolvedConflicts("");
      await refresh();
    } catch (err) { setError(err.message); setBusy(false); }
  }

  async function revoke() {
    const rationale = window.prompt("Why is this confirmation being revoked? This is recorded in the audit history.");
    if (!rationale || !window.confirm("Revoke this confirmed incident and exclude it from future matching?")) return;
    setBusy(true);
    try {
      await request(`/memory/incidents/${current.incident_id}/revoke`, { method: "POST", body: JSON.stringify({ rationale }) });
      await refresh();
    } catch (err) { setError(err.message); setBusy(false); }
  }

  async function rejectMatch(matchId) {
    if (!window.confirm("Reject this historical candidate for this investigation?")) return;
    setBusy(true);
    try {
      await request(`/memory/matches/${matchId}/reject`, { method: "POST" });
      await refresh();
    } catch (err) { setError(err.message); setBusy(false); }
  }

  const reviewerPanel = (
    <div className="memory-section">
      <h3>Reviewer queue ({pending.length})</h3>
      <label className="memory-form">Pending submission
        <select value={reviewId} onChange={(event) => setReviewId(event.target.value)}>
          <option value="">Select a submission</option>
          {pending.map((item) => <option key={item.submission_id} value={item.submission_id}>
            Run {item.run_id} · {item.category} · {item.submitted_by}
          </option>)}
        </select>
      </label>
      {selectedSubmission && <div className="memory-review">
        <p><strong>{selectedSubmission.cause_description}</strong></p>
        <p>Submitted by {selectedSubmission.submitted_by}. Inspect the source records before approving.</p>
        <div className="memory-event">
          <strong>Submitted evidence assessment</strong><br />
          Status: {selectedSubmission.submitted_classification?.status || "unknown"} · category: {selectedSubmission.submitted_classification?.symptom_category || "unresolved"}<br />
          {selectedSubmission.submitted_classification?.unresolved_reason || "No unresolved explanation recorded."}
          {(selectedSubmission.submitted_classification?.conflicts || []).map((conflict, index) =>
            <p key={index}>Conflict: {conflict.reason || conflict.scope || JSON.stringify(conflict)}</p>)}
        </div>
        {selectedSubmission.evidence.map((item) => <p key={item.reference} className="memory-event">
          <strong>{item.kind || "evidence"}</strong> · {item.reference} · {item.excerpt}
          {item.source_uri && <> · <a href={item.source_uri} target="_blank" rel="noreferrer">Open source</a></>}
        </p>)}
        {criteria.map((item, index) => <fieldset key={item.id}>
          <legend>{item.id.replaceAll("_", " ")}</legend>
          <label><input type="checkbox" checked={item.passed}
            onChange={(event) => setCriteria((rows) => rows.map((row, i) => i === index ? { ...row, passed: event.target.checked } : row))} /> Evidence requirement passed</label>
          <input placeholder="Verification method" value={item.method}
            onChange={(event) => setCriteria((rows) => rows.map((row, i) => i === index ? { ...row, method: event.target.value } : row))} />
          <input placeholder="Observed result" value={item.result}
            onChange={(event) => setCriteria((rows) => rows.map((row, i) => i === index ? { ...row, result: event.target.value } : row))} />
          <select value={item.evidence_refs[0] || ""}
            onChange={(event) => setCriteria((rows) => rows.map((row, i) => i === index ? { ...row, evidence_refs: event.target.value ? [event.target.value] : [] } : row))}>
            <option value="">Supporting source reference</option>
            {selectedSubmission.evidence.map((source) => <option key={source.reference} value={source.reference}>{source.reference}</option>)}
          </select>
        </fieldset>)}
        <label>Material conflicts that remain unresolved
          <textarea value={unresolvedConflicts} onChange={(event) => setUnresolvedConflicts(event.target.value)}
            placeholder="List each unresolved contradiction on a separate line. Approval is disabled until resolved." />
        </label>
        <label>Reviewer decision rationale
          <textarea value={reviewRationale} onChange={(event) => setReviewRationale(event.target.value)}
            placeholder="Record why this decision follows from the evidence" />
        </label>
        <div className="memory-actions">
          <button className="primary-button" disabled={busy || reviewRationale.length < 12 || unresolvedConflicts.trim().length > 0} onClick={() => review("approve")}>Approve verified cause</button>
          <button className="secondary-button" disabled={busy || reviewRationale.length < 12} onClick={() => review("needs_more_evidence")}>Needs evidence</button>
          <button className="text-button" disabled={busy || reviewRationale.length < 12} onClick={() => review("reject")}>Reject</button>
        </div>
      </div>}
      {submissions.length > 0 && <div className="memory-event">
        <strong>Recent submission outcomes</strong>
        {submissions.slice(0, 10).map((item) => <p key={item.submission_id}>
          Run {item.run_id} · {item.category} · {item.status}{item.review_rationale ? ` — ${item.review_rationale}` : ""}
        </p>)}
      </div>}
    </div>
  );

  return <section className="panel memory-panel" id="verified-memory">
    <div className="panel-heading"><div><div className="panel-kicker">EXASOL VERIFIED INCIDENT MEMORY</div><h2>Historical knowledge, human verified</h2><p className="panel-description">Only an authorized reviewer can confirm a submitted cause. Similar incidents remain candidates.</p></div><span className="subtle-pill">{connected ? `${records.filter((item) => item.status === "active").length} active records` : "Access required"}</span></div>
    <div className="memory-access"><label htmlFor="memory-token">Engineer access token</label><input id="memory-token" type="password" autoComplete="off" value={token} onChange={(event) => { setToken(event.target.value); setConnected(false); setRole(""); setRecords([]); setSubmissions([]); onCountChange(null); onRecordChange(null); }} placeholder="Enter a configured investigator or reviewer token" /><button className="secondary-button" disabled={!token || busy} onClick={refresh}>{busy ? "Working…" : "Connect memory"}</button></div>
    <p className="memory-note">The demo email gate does not authorize memory changes. Tokens are held only in this page state and are not stored in the browser.</p>
    {error && <div className="error-banner" role="alert">{error}</div>}
    {connected && <div className="memory-grid">
      <div className="memory-section"><h3>Similar verified incidents</h3>{matches?.matches?.length ? matches.matches.map((match) => <article key={match.match_id} className="memory-item"><strong>{match.historical_confirmed_cause}</strong><p>{LABEL}</p><small>Record {match.matched_incident_id} · run {match.historical_run_id} · confirmed {match.confirmed_at} by {match.reviewed_by} · status {match.memory_status} · retrieval score {match.similarity_score.toFixed(2)}</small><p>Matching: {match.matching_features.join(", ") || match.matching_tokens.join(", ") || "text signals"} · Differing: {match.differing_features.join(", ") || "none recorded"}</p>{(match.historical_evidence || []).map((item) => <p className="memory-event" key={item.reference}><strong>{item.reference}</strong> · {item.excerpt}{item.source_uri && <> · <a href={item.source_uri} target="_blank" rel="noreferrer">Open source</a></>}</p>)}<button className="text-button" onClick={() => rejectMatch(match.match_id)}>Reject candidate</button></article>) : <p className="memory-empty">{matches?.reason || "Select an investigation to search verified memory."}</p>}<small>Similarity is a retrieval score, not a probability of diagnosis.</small></div>
      <div className="memory-section"><h3>Current confirmation</h3>{current ? <article className="memory-item"><strong>{current.confirmed_description}</strong><p>{current.confirmed_category} · reviewed by {current.confirmed_by} · {current.confirmed_at}</p><small>Revision {current.revision} · fingerprint {current.fingerprint_version}</small><div className="memory-actions"><button className="text-button" onClick={revoke}>Revoke</button></div></article> : <p className="memory-empty">No reviewer-confirmed cause for this run.</p>}<h3>Review history</h3>{history.length ? history.map((event) => <p key={event.audit_id} className="memory-event"><strong>{event.action}</strong> · {event.actor_id} · {event.created_at}<br />{event.rationale}</p>) : <p className="memory-empty">No reviewed decisions yet.</p>}</div>
      <div className="memory-section"><h3>{current ? "Submit a correction" : existingRecord ? "Submit a replacement for revoked record" : "Submit a cause hypothesis"}</h3><p className="memory-note">A submission is unconfirmed until a different authorized reviewer verifies cause-specific evidence.</p><form onSubmit={submit} className="memory-form"><label>Symptom category<select value={category} onChange={(event) => setCategory(event.target.value)} required><option value="">Choose a supported category</option>{["delayed_run", "duplicate_data", "timeout", "schema_mismatch", "dependency_failure", "early_termination", "incomplete_data"].map((item) => <option key={item} value={item}>{item.replaceAll("_", " ")}</option>)}</select></label><label>Specific causal hypothesis<textarea value={cause} onChange={(event) => setCause(event.target.value)} minLength={12} required placeholder="Describe the mechanism to verify, not just the symptom" /></label><div className="memory-evidence-options"><strong>Incident evidence</strong>{(investigation?.evidence || []).map((item) => <div key={item.reference + item.observation}><label><input type="checkbox" checked={selectedRefs.includes(item.reference)} onChange={(event) => setSelectedRefs((refs) => event.target.checked ? [...refs, item.reference] : refs.filter((ref) => ref !== item.reference))} /> {item.reference}: {item.observation}</label>{selectedRefs.includes(item.reference) && <label><input type="checkbox" checked={causalRefs.includes(item.reference)} onChange={(event) => setCausalRefs((refs) => event.target.checked ? [...refs, item.reference] : refs.filter((ref) => ref !== item.reference))} /> This record also documents a causal mechanism</label>}</div>)}</div><label>Additional HTTPS source URL<input type="url" value={sourceUri} onChange={(event) => setSourceUri(event.target.value)} placeholder="https://..." /></label><label>Source excerpt<textarea value={sourceExcerpt} onChange={(event) => setSourceExcerpt(event.target.value)} placeholder="Relevant source record text" /></label><button className="primary-button" disabled={busy || !runId || (!selectedRefs.length && !(sourceUri && sourceExcerpt))}>Submit for independent review</button></form></div>
      {role === "reviewer" && reviewerPanel}
      {submissions.length > 0 && <div className="memory-section"><h3>My submission status</h3>{submissions.slice(0, 10).map((item) => <p key={item.submission_id} className="memory-event"><strong>{item.status.replaceAll("_", " ")}</strong> · Run {item.run_id} · {item.category}{item.review_rationale ? ` — ${item.review_rationale}` : ""}</p>)}</div>}
      <div className="memory-section"><h3>Memory analytics</h3><p className="memory-note">Operational counts calculated in Exasol. Accuracy, false-match rate, and time saved require independently labelled cases or human measurements.</p>{Object.entries(analytics?.active_by_category || {}).map(([name, count]) => <p className="memory-event" key={name}><strong>{name.replaceAll("_", " ")}</strong> · {count} active confirmed incident{count === 1 ? "" : "s"}</p>)}{!Object.keys(analytics?.active_by_category || {}).length && <p className="memory-empty">No active verified incidents yet.</p>}<p className="memory-note">Match decisions: {Object.entries(analytics?.match_status_counts || {}).map(([name, count]) => `${name} ${count}`).join(" · ") || "none"}</p><a href="#/scorecard">Open public classifier scorecard</a></div>
    </div>}
  </section>;
}

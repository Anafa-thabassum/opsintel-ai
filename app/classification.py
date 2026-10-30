"""Small, deterministic evidence normalizer and symptom classifier."""

import re
from datetime import datetime


CATEGORY_ORDER = (
    "delayed_run",
    "duplicate_data",
    "timeout",
    "schema_mismatch",
    "dependency_failure",
    "early_termination",
    "incomplete_data",
)

_COUNT_PATTERNS = (
    re.compile(
        r"expected\s+(?P<expected>\d+)\s+(?:rows?|records?)?"
        r"[^.;]{0,80}?(?:received|processed|found|wrote|written)\s+"
        r"(?P<actual>\d+)", re.I,
    ),
    re.compile(
        r"(?P<actual>\d+)\s+of\s+(?P<expected>\d+)\s+"
        r"(?:expected\s+)?(?:rows?|records?)", re.I,
    ),
    re.compile(
        r"expects?\s+(?P<expected>\d+)\s+(?:rows?|records?)?"
        r"[^.;]{0,80}?(?:finds?|found|processed|received)\s+"
        r"(?P<actual>\d+)", re.I,
    ),
)
_ACTUAL_COUNT = re.compile(
    r"(?P<actual>\d+)\s+(?:rows?|records?)?\s*(?:written|processed|received|found)",
    re.I,
)
_TERMINAL = re.compile(
    r"\b(completed successfully|finished successfully|(?:pipeline|run) status\s*(?:is|[:=])?\s*success)\b"
    r"|\b((?:pipeline|run) status\s*(?:is|[:=])?\s*failed|pipeline failed|run failed|"
    r"job failed|task failed)\b", re.I,
)
_TIME_TEXT = re.compile(
    r"(?:scheduled|configured)\s+(?:to\s+)?start\s+(?:at\s+)?"
    r"(?P<scheduled>\d{1,2}:\d{2})[^.;]{0,60}?"
    r"(?:started|began|commenced)\s+(?:at\s+)?(?P<started>\d{1,2}:\d{2})",
    re.I,
)
_NEGATORS = re.compile(
    r"\b(?:no|not|never|without|didn't|did\s+not|doesn't|does\s+not|"
    r"wasn't|was\s+not|isn't|is\s+not|hasn't|has\s+not)\b", re.I,
)
_CLAUSE_BREAK = re.compile(r"[.;!?]|\bbut\b|\bhowever\b", re.I)

_TEXT_RULES = {
    "delayed_run": (
        re.compile(r"\b(?:started|began|commenced)\s+(?:significantly\s+)?late\b", re.I),
        re.compile(r"\bmissed\s+(?:its\s+)?(?:sla|scheduled\s+start|start\s+time)\b", re.I),
        re.compile(r"\bschedule\s+(?:start\s+)?delay\b", re.I),
    ),
    "duplicate_data": (
        re.compile(r"\bduplicat(?:e|ed)\s+(?:business\s+)?(?:rows?|records?|keys?|entries|features?)\b", re.I),
        re.compile(r"\b(?:same|duplicate)\s+(?:business\s+)?keys?\b", re.I),
        re.compile(r"\bduplicate[_ ]count\s*[:=]\s*[1-9]\d*\b", re.I),
    ),
    "timeout": (
        re.compile(r"\b(?:pipeline|query|statement|execution)\s+timeout\s*[:=]", re.I),
        re.compile(r"\b(?:timed?\s+out|timeout\s+(?:occurred|reached|hit|event|cancellation)|deadline\s+exceeded)\b", re.I),
        re.compile(r"\b(?:query|statement|execution)\s+(?:exceeded|reached|hit)\b.{0,60}\b(?:timeout|time\s+limit|deadline|limit)\b", re.I),
        re.compile(r"\b(?:cancelled|canceled)\b.{0,60}\b(?:configured\s+)?(?:statement\s+)?timeout\b", re.I),
    ),
    "schema_mismatch": (
        re.compile(r"\b(?:schema|type|format)\s+(?:mismatch|incompatib\w*|does\s+not\s+match|differs?\s+from)\b", re.I),
        re.compile(r"\b(?:invalid\s+cast|type\s+conversion\s+failed|validator\s+reject\w*)\b", re.I),
        re.compile(r"\b(?:string|varchar|text)\b.{0,60}\b(?:integer|numeric|decimal|timestamp|date)\b.{0,60}\b(?:column|field|destination|schema|insert)\b", re.I),
        re.compile(r"\b(?:value|timestamp|date)\b.{0,60}\b(?:does\s+not\s+match|fails?\s+the)\b.{0,60}\b(?:format|pattern|schema)\b", re.I),
    ),
    "dependency_failure": (
        re.compile(r"\b(?:required\s+)?(?:upstream|dependency|prerequisite)\b.{0,80}\b(?:failed|failure|unavailable|not\s+produced|missing|does\s+not\s+exist|connection\s+(?:error|failed|refused))\b", re.I),
        re.compile(r"\b(?:upstream\s+)?(?:table|relation|artifact)\b.{0,50}\b(?:unavailable|missing|does\s+not\s+exist|not\s+produced)\b", re.I),
        re.compile(r"\b(?:connection\s+(?:error|failed|refused))\b.{0,60}\b(?:upstream|dependency|service)\b", re.I),
    ),
    "early_termination": (
        re.compile(r"\b(?:terminated|aborted|stopped|killed|exited)\b.{0,90}\b(?:before|without|prior\s+to)\b.{0,50}\b(?:complete|completion|commit(?:ted)?|checkpoint|final\s+output|marker|finished)\b", re.I),
        re.compile(r"\bended\s+before\s+all\s+expected\s+(?:rows?|records?)\s+were\s+processed\b", re.I),
        re.compile(r"\bexit\s+code\s*[:=]?\s*[1-9]\d*\b", re.I),
        re.compile(r"\b(?:processing|run|pipeline|worker)\s+(?:stopped|ended|terminated|aborted)\s+early\b", re.I),
    ),
    "incomplete_data": (
        re.compile(r"\b(?:fewer|less)\s+(?:than\s+)?(?:the\s+)?expected\s+(?:rows?|records?)\b", re.I),
        re.compile(r"\bmissing\s+[1-9]\d*\s+(?:rows?|records?)\b", re.I),
        re.compile(r"\b(?:completeness|reconciliation)\s+(?:check|validation)\b.{0,50}\b(?:failed|shortfall|incomplete)\b", re.I),
        re.compile(r"\b(?:incomplete|shortfall)\s+(?:data|rows?|records?)\b", re.I),
    ),
}


def _safe_int(value, *, nonnegative=False):
    if value is None or isinstance(value, bool):
        return None, False
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        return None, True
    if nonnegative and parsed < 0:
        return None, True
    return parsed, False


def _reference(item):
    if isinstance(item.get("reference"), str) and item["reference"].strip():
        return item["reference"].strip()
    source = item.get("source")
    if source and item.get("log_id") is not None:
        return f"{source} · LOG-{item['log_id']}"
    if source and item.get("run_id") is not None:
        return f"{source} · RUN-{item['run_id']}"
    return None


def normalize_evidence(evidence_items):
    """Preserve input facts while exposing validated fields for extraction."""
    normalized = []
    errors = []
    for index, original in enumerate(evidence_items or []):
        item = {"observation": original} if isinstance(original, str) else dict(original or {})
        raw_text = next((
            item.get(key) for key in ("observation", "message", "text", "log_message")
            if isinstance(item.get(key), str)
        ), "")
        fields = dict(item.get("fields") or {}) if isinstance(item.get("fields"), dict) else {}
        for key in (
            "expected_rows", "actual_rows", "missing_rows", "duplicate_count",
            "exit_code", "required", "dependency_status", "dependency_name",
            "scheduled_at", "started_at", "lateness_threshold_seconds",
            "sla_seconds", "expected_type", "actual_type", "completed",
            "run_id", "pipeline_name", "source", "type", "kind",
        ):
            if key in item and key not in fields:
                fields[key] = item[key]

        parsed_fields = {}
        malformed = []
        for key in ("expected_rows", "actual_rows", "missing_rows", "duplicate_count"):
            if key in fields:
                parsed_fields[key], invalid = _safe_int(fields[key], nonnegative=True)
                if invalid:
                    malformed.append(key)
        if "exit_code" in fields:
            parsed_fields["exit_code"], invalid = _safe_int(fields["exit_code"])
            if invalid:
                malformed.append("exit_code")
        for key in ("required", "completed"):
            if key in fields and not isinstance(fields[key], bool):
                malformed.append(key)
            elif key in fields:
                parsed_fields[key] = fields[key]

        timestamp = next((item.get(key) for key in (
            "timestamp", "observed_at", "log_time", "time",
        ) if item.get(key) is not None), None)
        timestamp_iso = None
        timestamp_error = False
        if timestamp is not None:
            try:
                timestamp_iso = datetime.fromisoformat(
                    str(timestamp).replace("Z", "+00:00")
                ).isoformat()
            except ValueError:
                timestamp_error = True
                errors.append({"index": index, "field": "timestamp", "reason": "invalid timestamp preserved as raw input"})
        if malformed:
            errors.append({"index": index, "field": ",".join(malformed), "reason": "malformed structured value preserved; not used for classification"})

        normalized.append({
            "reference": _reference(item),
            "source": item.get("source"),
            "kind": fields.get("type") or fields.get("kind"),
            "run_id": fields.get("run_id"),
            "timestamp": timestamp,
            "timestamp_iso": timestamp_iso,
            "timestamp_error": timestamp_error,
            "raw_observation": raw_text,
            "normalized_observation": " ".join(raw_text.split()).casefold(),
            "fields": {**fields, **parsed_fields},
            "malformed_fields": malformed,
            "original": item,
        })
    return normalized, errors


def _local_negation(text, start):
    clause_start = max((match.end() for match in _CLAUSE_BREAK.finditer(text, 0, start)), default=0)
    prefix = text[clause_start:start]
    return bool(_NEGATORS.search(prefix[-80:]))


def _signal(category, item, *, method, value=None, polarity="supports", strength="strong", explanation=None):
    return {
        "category": category,
        "value": value,
        "polarity": polarity,
        "method": method,
        "strength": strength,
        "evidence_refs": [item["reference"]] if item["reference"] else [],
        "traceable": bool(item["reference"]),
        "source": item["source"],
        "timestamp": item["timestamp_iso"] or item["timestamp"],
        "explanation": explanation,
    }


def _parse_counts(text):
    for pattern in _COUNT_PATTERNS:
        match = pattern.search(text)
        if match:
            return int(match.group("expected")), int(match.group("actual"))
    return None


def _signals_for_item(item):
    signals = []
    fields = item["fields"]
    text = item["normalized_observation"]

    expected = fields.get("expected_rows")
    actual = fields.get("actual_rows")
    missing = fields.get("missing_rows")
    duplicate_count = fields.get("duplicate_count")
    if expected is None or actual is None:
        parsed_counts = _parse_counts(text)
        if parsed_counts:
            expected, actual = parsed_counts
            method = "parsed_count_pair"
        else:
            method = "structured_fields"
    else:
        method = "structured_fields"
    if expected is not None and actual is not None:
        if actual < expected:
            signals.append(_signal(
                "incomplete_data", item, method=method,
                value={"expected_rows": expected, "actual_rows": actual,
                       "missing_rows": expected - actual},
                explanation="Comparable expected and actual counts show a shortfall.",
            ))
        elif actual > expected:
            signals.append(_signal(
                "excess_rows", item, method=method,
                value={"expected_rows": expected, "actual_rows": actual,
                       "excess_rows": actual - expected},
                strength="supporting",
                explanation="Counts show excess rows; this alone does not establish duplicate data.",
            ))
    if missing is not None and missing > 0 and not any(
        signal["category"] == "incomplete_data" for signal in signals
    ):
        signals.append(_signal(
            "incomplete_data", item, method="structured_fields",
            value={"missing_rows": missing},
            explanation="Source metadata reports missing rows.",
        ))
    if duplicate_count is not None and duplicate_count > 0:
        signals.append(_signal(
            "duplicate_data", item, method="structured_fields",
            value={"duplicate_count": duplicate_count},
            explanation="Source metadata reports duplicate records.",
        ))

    expected_type = fields.get("expected_type")
    actual_type = fields.get("actual_type")
    if (
        isinstance(expected_type, str)
        and isinstance(actual_type, str)
        and expected_type.strip().casefold() != actual_type.strip().casefold()
    ):
        signals.append(_signal(
            "schema_mismatch", item, method="structured_fields",
            value={"expected_type": expected_type, "actual_type": actual_type},
            explanation="Source and target field types differ.",
        ))

    required = fields.get("required")
    dependency_status = str(fields.get("dependency_status", "")).casefold()
    if required is True and dependency_status in {
        "failed", "failure", "unavailable", "missing", "not_produced",
    }:
        signals.append(_signal(
            "dependency_failure", item, method="structured_fields",
            value={"dependency": fields.get("dependency_name"),
                   "status": dependency_status},
            explanation="A required dependency is reported unavailable or failed.",
        ))

    exit_code = fields.get("exit_code")
    if exit_code not in (None, 0) and fields.get("completed") is False:
        signals.append(_signal(
            "early_termination", item, method="structured_fields",
            value={"exit_code": exit_code, "completed": False},
            explanation="A non-zero process exit is paired with an incomplete run state.",
        ))

    scheduled = fields.get("scheduled_at")
    started = fields.get("started_at")
    threshold = fields.get("lateness_threshold_seconds", fields.get("sla_seconds"))
    if scheduled is not None and started is not None and threshold is not None:
        try:
            scheduled_dt = datetime.fromisoformat(str(scheduled).replace("Z", "+00:00"))
            started_dt = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
            threshold_seconds = float(threshold)
            if scheduled_dt.tzinfo != started_dt.tzinfo:
                raise ValueError("timezone mismatch")
            delta = (started_dt - scheduled_dt).total_seconds()
            if delta > threshold_seconds:
                signals.append(_signal(
                    "delayed_run", item, method="structured_timestamps",
                    value={"scheduled_at": scheduled_dt.isoformat(),
                           "started_at": started_dt.isoformat(),
                           "delay_seconds": delta,
                           "threshold_seconds": threshold_seconds},
                    explanation="Comparable start times exceed the declared lateness threshold.",
                ))
        except (TypeError, ValueError, OverflowError):
            pass

    for category, patterns in _TEXT_RULES.items():
        for pattern in patterns:
            match = pattern.search(text)
            if not match:
                continue
            polarity = "negates" if _local_negation(text, match.start()) else "supports"
            if category == "timeout" and re.search(
                r"\b(?:timeout\s+(?:setting|threshold|limit)\s+(?:is\s+)?configured|configured\s+timeout\s+(?:is\s+)?\d+)\b",
                text,
            ) and not re.search(r"\b(?:exceeded|reached|hit|cancelled|canceled|timed?\s*out)\b", text):
                continue
            signals.append(_signal(
                category, item, method="text_pattern",
                value=match.group(0), polarity=polarity,
                explanation="Explicit text signal; treated as symptom evidence, not a cause.",
            ))
            break

    if not any(signal["category"] == "incomplete_data" for signal in signals):
        missing_match = re.search(r"\bmissing\s+(?P<count>[1-9]\d*)\s+(?:rows?|records?)\b", text)
        if missing_match:
            signals.append(_signal(
                "incomplete_data", item, method="parsed_count",
                value={"missing_rows": int(missing_match.group("count"))},
            ))

    time_match = _TIME_TEXT.search(text)
    if time_match:
        try:
            scheduled = datetime.strptime(time_match.group("scheduled"), "%H:%M")
            started = datetime.strptime(time_match.group("started"), "%H:%M")
            delay_seconds = (started - scheduled).total_seconds()
            if delay_seconds > 0:
                signals.append(_signal(
                    "delayed_run", item, method="parsed_schedule_times",
                    value={"scheduled_time": time_match.group("scheduled"),
                           "started_time": time_match.group("started"),
                           "delay_seconds": delay_seconds},
                    explanation="Explicit scheduled and actual start times differ; cause is unknown.",
                ))
        except ValueError:
            pass

    # Counts reported by separate sources can conflict only when they share a
    # run scope (or belong to one legacy single-incident input).
    actual_match = _ACTUAL_COUNT.search(text)
    if actual_match:
        signals.append({
            "category": "reported_actual_count",
            "value": int(actual_match.group("actual")),
            "metric": "actual_rows",
            "polarity": "supports",
            "method": "parsed_count",
            "strength": "supporting",
            "evidence_refs": [item["reference"]] if item["reference"] else [],
            "traceable": bool(item["reference"]),
            "source": item["source"],
            "timestamp": item["timestamp_iso"] or item["timestamp"],
            "run_id": item["run_id"],
        })

    return signals


def _scope_key(item):
    return item["run_id"] if item["run_id"] is not None else "current-incident"


def _find_conflicts(evidence, signals):
    conflicts = []
    terminal_by_scope = {}
    count_by_scope = {}
    explicit_conflict_phrases = (
        "different failure reasons", "sources disagree", "conflicting reports",
        "reports different", "contradictory evidence",
    )
    for item in evidence:
        text = item["normalized_observation"]
        terminal = _TERMINAL.search(text)
        if terminal:
            state = "success" if terminal.group(1) else "failed"
            scope = _scope_key(item)
            previous = terminal_by_scope.setdefault(scope, {"success": [], "failed": []})
            previous[state].append(item["reference"])
        if any(phrase in text for phrase in explicit_conflict_phrases):
            conflicts.append({
                "type": "source_claim_conflict",
                "evidence_refs": [item["reference"]] if item["reference"] else [],
                "reason": "Source explicitly reports incompatible or disagreeing claims.",
            })
    for scope, states in terminal_by_scope.items():
        if states["success"] and states["failed"]:
            refs = list(dict.fromkeys(states["success"] + states["failed"]))
            conflicts.append({
                "type": "terminal_state_conflict",
                "evidence_refs": refs,
                "reason": "Success and failure terminal states are reported for the same incident scope.",
            })
    for signal in signals:
        if signal.get("metric") == "actual_rows":
            scope = signal.get("run_id") if signal.get("run_id") is not None else "current-incident"
            count_by_scope.setdefault(scope, {}).setdefault(signal["value"], []).extend(signal["evidence_refs"])
    for scope, values in count_by_scope.items():
        if len(values) > 1:
            refs = list(dict.fromkeys(ref for group in values.values() for ref in group))
            conflicts.append({
                "type": "row_count_conflict",
                "evidence_refs": refs,
                "values": sorted(values),
                "reason": "Different actual row counts are reported for the same incident scope.",
            })
    return conflicts


def _classify_normalized(evidence, normalization_errors=None):
    signals = [signal for item in evidence for signal in _signals_for_item(item)]
    conflicts = _find_conflicts(evidence, signals)
    positive = {}
    negative = {}
    for signal in signals:
        category = signal["category"]
        if category not in CATEGORY_ORDER:
            continue
        target = positive if signal["polarity"] == "supports" else negative
        target.setdefault(category, []).append(signal)

    # Opposing evidence for the same signal in one incident is a conflict,
    # not a winner-takes-all match.
    for category in positive.keys() & negative.keys():
        refs = list(dict.fromkeys(
            ref for signal in positive[category] + negative[category]
            for ref in signal["evidence_refs"]
        ))
        conflicts.append({
            "type": "signal_polarity_conflict",
            "category": category,
            "evidence_refs": refs,
            "reason": f"Evidence both supports and negates {category}.",
        })

    def category_rank(category):
        values = positive[category]
        strength = 2 if any(item["strength"] == "strong" for item in values) else 1
        refs = len({ref for item in values for ref in item["evidence_refs"]})
        return strength, refs, -CATEGORY_ORDER.index(category)

    ordered = sorted(positive, key=category_rank, reverse=True)
    blocking_conflict = bool(conflicts)
    selected = ordered[0] if ordered else None
    if blocking_conflict:
        category = "conflicting_evidence"
        hypothesis = "The evidence contains incompatible claims; the incident symptom cannot be resolved from these sources alone."
        action = "Reconcile the cited source records, run scope, and timestamps before selecting a category."
        reason = "Conflicting claims block a reliable category decision."
        confidence = "low"
    elif selected is None:
        category = "unclassified"
        hypothesis = "The available evidence does not support a specific failure category."
        action = "Collect run-scoped logs, counts, schema validation, and dependency state before classifying."
        reason = "No supported classifier signal matched."
        confidence = "low"
    else:
        category = selected
        hypotheses = {
            "delayed_run": ("Evidence supports a late pipeline start; the reason is not confirmed.", "Compare scheduled and actual start times and inspect queue and dependency timing."),
            "duplicate_data": ("Evidence supports repeated records or rows; the duplication mechanism is not confirmed.", "Compare the affected keys and record scope, then inspect source and retry lineage."),
            "timeout": ("Evidence supports an execution timeout; the reason is not confirmed.", "Verify the configured limit, run duration, and cancellation event before investigating query or resource causes."),
            "schema_mismatch": ("Evidence supports an input/target schema or format incompatibility; the producer-side change is not confirmed.", "Compare the source contract and target schema for the cited field and run."),
            "dependency_failure": ("Evidence supports a required dependency being unavailable or failed; its underlying cause is not confirmed.", "Verify dependency identity, required status, run timing, and upstream state."),
            "early_termination": ("Evidence supports termination before expected completion; the termination cause is not confirmed.", "Inspect the run state, terminal event, exit code, and completion marker."),
            "incomplete_data": ("Evidence supports a scoped row or record shortfall; the reason is not confirmed.", "Reconcile expected and actual counts for the same scope and cutoff."),
        }
        hypothesis, action = hypotheses[selected]
        reason = (
            f"Selected {selected} by evidence strength; ties use documented precedence order and other symptoms are retained."
            if len(ordered) > 1
            else f"Only {selected} had positive, non-negated evidence."
        )
        confidence = "low" if len(ordered) > 1 else "medium"

    status = "supported" if selected is not None and not blocking_conflict else "unresolved"
    resolution = "candidate_only" if status == "supported" else "unresolved"
    relevant_signals = [
        signal for signal in signals
        if signal["category"] in CATEGORY_ORDER
    ]
    all_categories = ordered if not blocking_conflict else list(ordered)
    classification = {
        "version": "deterministic-signals-v2",
        "symptom_category": selected,
        "secondary_categories": ordered[1:] if selected else [],
        "status": status,
        "resolution_status": resolution,
        "evidence_strength": (
            "strong" if selected and any(
                item["strength"] == "strong" for item in positive[selected]
            ) else "supporting" if selected else "insufficient"
        ),
        "signals": relevant_signals,
        "conflicts": conflicts,
        "normalization_errors": normalization_errors or [],
        "unresolved_reason": reason if status == "unresolved" else None,
        "confirmed_root_cause": None,
    }
    evidence_assessment = {
        "status": "conflicting" if conflicts else "sufficient" if selected else "insufficient",
        "conflicts": conflicts,
        "evidence_refs": list(dict.fromkeys(
            ref for item in evidence for ref in [item["reference"]] if ref
        )),
        "untraceable_evidence_count": sum(not item["reference"] for item in evidence),
        "normalization_errors": normalization_errors or [],
    }
    return {
        "result": (category, hypothesis, action),
        "confidence": confidence,
        "matched_categories": all_categories if not blocking_conflict else ["conflicting_evidence", *all_categories],
        "tie_break_reason": reason,
        "classification": classification,
        "evidence_assessment": evidence_assessment,
        "signals": signals,
        "conflicts": conflicts,
    }


def classify_incident(evidence_items, context=None):
    """Classify structured incident evidence without promoting a cause."""
    items = list(evidence_items or [])
    context = dict(context or {})
    if any(context.get(key) is not None for key in (
        "expected_rows", "actual_rows", "missing_rows", "scheduled_at",
        "started_at", "lateness_threshold_seconds", "sla_seconds",
    )):
        items.append({
            "source": context.get("source", "incident_metadata"),
            "run_id": context.get("run_id"),
            "reference": context.get("reference"),
            "type": "incident_metadata",
            "fields": context,
            "observation": "",
        })
    normalized, errors = normalize_evidence(items)
    return _classify_normalized(normalized, errors)


def classify_log_messages(log_messages, missing_rows=None, expected_rows=None, actual_rows=None):
    """Compatibility adapter for the original positional classifier API."""
    evidence = [
        {"type": "pipeline_log", "observation": message}
        for message in (log_messages or [])
    ]
    result = classify_incident(evidence, {
        "missing_rows": missing_rows,
        "expected_rows": expected_rows,
        "actual_rows": actual_rows,
    })
    return result

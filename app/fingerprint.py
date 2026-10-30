"""Deterministic, explainable fingerprints for verified incident retrieval."""

import re


FINGERPRINT_VERSION = "word-pairs-v1"

_TIMESTAMP = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?\b", re.I)
_UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
_PATH = re.compile(r"(?<!\w)(?:/[^\s,;]+|[A-Za-z]:\\[^\s,;]+)")
_VARIABLE_ID = re.compile(r"\b(?:run|request|execution|job|trace|task)[-_ ]?(?:id[-_ ]?)?\d+\b", re.I)
_ERROR_CODE = re.compile(r"\b(?:SQLSTATE\s*[:=]?\s*[0-9A-Z]{5}|ORA-\d{4,5}|[A-Z]{2,8}-\d{2,6})\b", re.I)
_WORD = re.compile(r"[a-z][a-z0-9_]*")
_STOPWORDS = {"a", "an", "and", "at", "by", "for", "from", "in", "is", "of", "on", "or", "the", "to", "was", "with"}


def normalize_log(message):
    """Remove volatile run identifiers while retaining error codes and field names."""
    text = str(message or "").lower()
    codes = {match.group().lower().replace(" ", "") for match in _ERROR_CODE.finditer(str(message or ""))}
    text = _ERROR_CODE.sub(" ", text)
    for pattern in (_TIMESTAMP, _UUID, _PATH, _VARIABLE_ID):
        text = pattern.sub(" ", text)
    text = re.sub(r"\b\d+(?:\.\d+)?\b", " ", text)
    words = [word for word in _WORD.findall(text) if word not in _STOPWORDS]
    return " ".join([*sorted(codes), *words])


def token_ngrams(normalized_text):
    words = normalized_text.split()
    return set(words) | {f"{a} {b}" for a, b in zip(words, words[1:])}


def incident_features(incident):
    """Use only observed or classified features, never a presumed cause."""
    features = {}
    category = incident.get("classification", {}).get("symptom_category") or incident.get("category")
    if category and category not in {"unclassified", "conflicting_evidence"}:
        features["symptom_category"] = str(category)
    expected, actual = incident.get("expected_rows"), incident.get("actual_rows")
    if expected is not None and actual is not None:
        try:
            ratio = float(actual) / float(expected) if float(expected) > 0 else None
            if ratio is not None:
                features["completeness_band"] = "low" if ratio < 0.8 else "partial" if ratio < 1 else "complete" if ratio == 1 else "excess"
        except (TypeError, ValueError, ZeroDivisionError):
            pass
    for item in incident.get("evidence", []):
        fields = item.get("fields") or {}
        state = fields.get("dependency_state") or fields.get("upstream_status")
        if state is not None:
            features["upstream_status"] = str(state).lower()
    codes = sorted({match.group().upper().replace(" ", "") for item in incident.get("evidence", []) for match in _ERROR_CODE.finditer(str(item.get("observation", "")))})
    if codes:
        features["error_codes"] = ",".join(codes)
    return features


def fingerprint_incident(incident):
    messages = [item.get("observation", "") for item in incident.get("evidence", []) if item.get("type") == "pipeline_log"]
    normalized = " ".join(filter(None, (normalize_log(message) for message in messages)))
    return {"version": FINGERPRINT_VERSION, "normalized_text": normalized, "tokens": sorted(token_ngrams(normalized)), "features": incident_features(incident)}


def compare_fingerprints(current, historical):
    """Return a retrieval score and its reasons; score is not a probability."""
    if current.get("version") != historical.get("version"):
        return {"score": 0.0, "matching_features": [], "differing_features": ["fingerprint_version"], "eligible": False}
    left, right = set(current.get("tokens") or []), set(historical.get("tokens") or [])
    overlap = left & right
    text_score = len(overlap) / len(left | right) if left | right else 0.0
    current_features, old_features = current.get("features") or {}, historical.get("features") or {}
    shared = set(current_features) & set(old_features)
    matching = sorted(key for key in shared if current_features[key] == old_features[key])
    differing = sorted(key for key in shared if current_features[key] != old_features[key])
    feature_score = len(matching) / len(shared) if shared else 0.0
    penalty = sum(0.35 if key == "symptom_category" else 0.2 if key == "error_codes" else 0.12 for key in differing)
    score = max(0.0, min(1.0, 0.7 * text_score + 0.3 * feature_score - penalty))
    eligible = bool(overlap or matching) and "symptom_category" not in differing
    return {"score": round(score, 4), "matching_features": matching, "differing_features": differing, "matching_tokens": sorted(overlap)[:20], "eligible": eligible}

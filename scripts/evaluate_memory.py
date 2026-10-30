"""Leakage-checked chronological evaluation for independently prepared cases."""

import argparse
import json
from datetime import datetime
from pathlib import Path

from app.classification import classify_incident
from app.fingerprint import compare_fingerprints, fingerprint_incident
from app.memory import min_similarity_threshold


def _timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("Timestamp must include a timezone")
        return parsed
    except (AttributeError, ValueError) as exc:
        raise ValueError("Every event needs an ISO timestamp") from exc


def load_events(path):
    events = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    ids = [event.get("event_id") for event in events]
    if not ids or len(set(ids)) != len(ids) or None in ids:
        raise ValueError("Evaluation requires unique event IDs and at least one event")
    for event in events:
        if event.get("event_type") not in {"confirmation", "query"}:
            raise ValueError("Unknown evaluation event type")
        if not isinstance(event.get("incident"), dict) or not isinstance(event["incident"].get("evidence"), list):
            raise ValueError("Each event requires a source-backed incident")
        if any(not isinstance(item, dict) or not item.get("reference") or not item.get("observation")
               for item in event["incident"]["evidence"]):
            raise ValueError("Each evaluation evidence item requires a reference and observed excerpt")
        if event.get("run_id") != event["incident"].get("run_id"):
            raise ValueError("Event run ID must match its incident")
        _timestamp(event.get("timestamp"))
    return sorted(events, key=lambda event: (_timestamp(event["timestamp"]), event["event_id"]))


def _rate(numerator, denominator):
    return round(numerator / denominator, 4) if denominator else None


def _wilson(successes, sample_size):
    """Wilson 95% interval for an observed binary rate; None for empty samples."""
    if not sample_size:
        return None
    z = 1.96
    rate = successes / sample_size
    scale = 1 + z * z / sample_size
    center = (rate + z * z / (2 * sample_size)) / scale
    margin = z * ((rate * (1 - rate) / sample_size + z * z / (4 * sample_size**2)) ** 0.5) / scale
    return [round(max(0.0, center - margin), 4), round(min(1.0, center + margin), 4)]


def evaluate(events):
    """Confirmations enter memory only after their timestamp; queries never train."""
    threshold = min_similarity_threshold()
    memory = []
    results = []
    seen_runs = set()
    for event in events:
        run_id = event["run_id"]
        if event["event_type"] == "confirmation":
            if not event.get("cause_id") or run_id in seen_runs:
                raise ValueError("Confirmed events require a cause ID and a unique run")
            seen_runs.add(run_id)
            memory.append({"run_id": run_id, "cause_id": event["cause_id"],
                           "timestamp": event["timestamp"], "fingerprint": fingerprint_incident(event["incident"])})
            continue

        incident = event["incident"]
        current = fingerprint_incident(incident)
        ranked = []
        for prior in memory:
            if prior["run_id"] == run_id or _timestamp(prior["timestamp"]) >= _timestamp(event["timestamp"]):
                continue
            comparison = compare_fingerprints(current, prior["fingerprint"])
            if comparison["eligible"]:
                ranked.append((comparison["score"], prior["cause_id"], prior["run_id"]))
        ranked.sort(key=lambda item: (-item[0], item[2]))
        forced = ranked[0] if ranked else None
        selective = forced if forced and forced[0] >= threshold else None
        predicted = classify_incident(incident["evidence"], {"run_id": run_id})["result"][0]
        expected = event.get("expected_category")
        truth = event.get("expected_cause_id")
        results.append({
            "event_id": event["event_id"], "run_id": run_id, "timestamp": event["timestamp"],
            "memory_size": len(memory), "expected_category": expected,
            "classifier_category": predicted, "classifier_correct": predicted == expected if expected is not None else None,
            "expected_cause_id": truth,
            "forced_match_cause_id": forced[1] if forced else None,
            "selective_match_cause_id": selective[1] if selective else None,
            "top3_cause_ids": [item[1] for item in ranked[:3]],
            "top_score": forced[0] if forced else None,
            "matched_prior_run_id": selective[2] if selective else None,
            "abstained": selective is None,
        })

    labelled = [item for item in results if item["expected_category"] is not None]
    positives = [item for item in results if item["expected_cause_id"] is not None]
    selected = [item for item in results if not item["abstained"]]
    errors = [item for item in selected if item["selective_match_cause_id"] != item["expected_cause_id"]]
    categories = sorted({item["expected_category"] for item in labelled}
                        | {item["classifier_category"] for item in labelled})
    confusion = {expected: {predicted: 0 for predicted in categories} for expected in categories}
    for item in labelled:
        confusion[item["expected_category"]][item["classifier_category"]] += 1
    per_category = {}
    for category in categories:
        rows = [item for item in labelled if item["expected_category"] == category]
        true_positive = confusion.get(category, {}).get(category, 0)
        predicted_count = sum(confusion[expected].get(category, 0) for expected in categories)
        per_category[category] = {
            "total": len(rows), "correct": true_positive,
            "precision": _rate(true_positive, predicted_count),
            "precision_ci95": _wilson(true_positive, predicted_count),
            "recall": _rate(true_positive, len(rows)),
            "recall_ci95": _wilson(true_positive, len(rows)),
        }
    learning_curve = []
    for size in sorted({item["memory_size"] for item in results}):
        rows = [item for item in results if item["memory_size"] == size]
        positives_at_size = [item for item in rows if item["expected_cause_id"] is not None]
        selected_at_size = [item for item in rows if not item["abstained"]]
        correct_at_size = sum(item["selective_match_cause_id"] == item["expected_cause_id"]
                              and item["expected_cause_id"] is not None for item in rows)
        false_at_size = sum(item["selective_match_cause_id"] != item["expected_cause_id"]
                            for item in selected_at_size)
        learning_curve.append({
            "confirmed_records_available": size, "queries": len(rows),
            "eligible_positive_queries": len(positives_at_size),
            "selected_queries": len(selected_at_size), "false_matches": false_at_size,
            "retrieval_success_rate": _rate(correct_at_size, len(positives_at_size)),
            "retrieval_success_ci95": _wilson(correct_at_size, len(positives_at_size)),
            "false_match_rate": _rate(false_at_size, len(selected_at_size)),
            "coverage": _rate(len(selected_at_size), len(rows)),
        })
    return {
        "method": "chronological_prequential_v1", "query_count": len(results),
        "similarity_threshold": threshold,
        "classifier_alone": {"labelled": len(labelled), "top1_category_accuracy": _rate(sum(item["classifier_correct"] for item in labelled), len(labelled)),
                             "top1_category_accuracy_ci95": _wilson(sum(item["classifier_correct"] for item in labelled), len(labelled)),
                             "per_category": per_category, "confusion_matrix": confusion},
        "classifier_plus_memory": {"top1_cause_accuracy": _rate(sum(item["forced_match_cause_id"] == item["expected_cause_id"] for item in positives), len(positives)),
                                   "top1_cause_accuracy_ci95": _wilson(sum(item["forced_match_cause_id"] == item["expected_cause_id"] for item in positives), len(positives)),
                                   "top3_cause_recall": _rate(sum(item["expected_cause_id"] in item["top3_cause_ids"] for item in positives), len(positives)),
                                   "top3_cause_recall_ci95": _wilson(sum(item["expected_cause_id"] in item["top3_cause_ids"] for item in positives), len(positives))},
        "classifier_memory_abstention": {"top1_cause_accuracy": _rate(sum(item["selective_match_cause_id"] == item["expected_cause_id"] for item in positives), len(positives)),
                                          "false_match_rate": _rate(len(errors), len(selected)),
                                          "false_match_rate_ci95": _wilson(len(errors), len(selected)),
                                          "abstention_rate": _rate(sum(item["abstained"] for item in results), len(results)),
                                          "coverage": _rate(len(selected), len(results)),
                                          "selective_accuracy": _rate(len(selected) - len(errors), len(selected)),
                                          "selective_accuracy_ci95": _wilson(len(selected) - len(errors), len(selected)),
                                          "selected_queries": len(selected), "labelled_cause_queries": len(positives),
                                          "retrieval_success": _rate(sum(item["selective_match_cause_id"] == item["expected_cause_id"] for item in positives), len(positives))},
        "learning_curve": learning_curve, "results": results,
        "limitations": ["Cause IDs and expected categories must come from independently adjudicated records.",
                        "A similarity score is not a probability of causal correctness.",
                        "No time-savings metric is inferred from classifier or retrieval performance."],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("events", type=Path, help="chronological confirmation/query JSONL; never use the frozen reviewer holdout for tuning")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = evaluate(load_events(args.events))
    output = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(output + "\n")
    else:
        print(output)


if __name__ == "__main__":
    main()

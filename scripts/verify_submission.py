"""Verify committed submission artifacts and cross-file numerical claims."""

import argparse
import json
import re
import struct
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "README.md",
    "reports/evaluation.md",
    "reports/database-comparison.json",
    "reports/exasol-benchmark.json",
    "reports/frozen-holdout-v1.json",
    "submission/opsintel-ai-pitch-deck.pptx",
    "submission/opsintel-ai-pitch-deck.pdf",
    "submission/opsintel-ai-demo.mp4",
    "submission/video-narration.txt",
}


def _git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def mp4_duration_seconds(path):
    data = Path(path).read_bytes()
    offset = data.find(b"mvhd")
    if offset < 0:
        raise ValueError("MP4 movie header not found")
    version = data[offset + 4]
    if version == 0:
        timescale, duration = struct.unpack(">II", data[offset + 16:offset + 24])
    elif version == 1:
        timescale = struct.unpack(">I", data[offset + 24:offset + 28])[0]
        duration = struct.unpack(">Q", data[offset + 28:offset + 36])[0]
    else:
        raise ValueError(f"Unsupported MP4 movie-header version: {version}")
    if not timescale:
        raise ValueError("MP4 timescale is zero")
    return duration / timescale


def pptx_text_and_slide_count(path):
    with zipfile.ZipFile(path) as package:
        slides = sorted(
            name for name in package.namelist()
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        )
        charts = sorted(
            name for name in package.namelist()
            if re.fullmatch(r"ppt/(?:slides/)?charts/chart\d+\.xml", name)
        )
        text = " ".join(
            re.sub(r"<[^>]+>", " ", package.read(name).decode("utf-8"))
            for name in slides + charts
        )
    return re.sub(r"\s+", " ", text), len(slides)


def verify(allow_dirty=False):
    failures = []
    tracked = set(_git("ls-tree", "-r", "--name-only", "HEAD").splitlines())
    missing = sorted(REQUIRED - tracked)
    if missing:
        failures.append(f"Latest commit is missing: {', '.join(missing)}")
    if not allow_dirty and _git("status", "--porcelain").strip():
        failures.append("Working tree is not clean")

    video_seconds = mp4_duration_seconds(ROOT / "submission/opsintel-ai-demo.mp4")
    if video_seconds >= 180:
        failures.append(f"Demo video is {video_seconds:.1f}s; maximum is 180s")

    deck_text, slide_count = pptx_text_and_slide_count(
        ROOT / "submission/opsintel-ai-pitch-deck.pptx"
    )
    if not 10 <= slide_count <= 11:
        failures.append(f"Pitch deck has {slide_count} slides; expected 10 or 11")

    pdf_pages = len(re.findall(
        rb"/Type\s*/Page\b",
        (ROOT / "submission/opsintel-ai-pitch-deck.pdf").read_bytes(),
    ))
    if pdf_pages != slide_count:
        failures.append(
            f"PDF has {pdf_pages} pages but PowerPoint has {slide_count} slides"
        )

    holdout = json.loads((ROOT / "reports/frozen-holdout-v1.json").read_text())
    benchmark = json.loads((ROOT / "reports/exasol-benchmark.json").read_text())
    comparison = json.loads(
        (ROOT / "reports/database-comparison.json").read_text()
    )
    evaluation = (ROOT / "reports/evaluation.md").read_text()
    readme = (ROOT / "README.md").read_text()
    narration = (ROOT / "submission/video-narration.txt").read_text().lower()
    total = holdout["total"]
    correct = holdout["correct"]
    median = benchmark["query_latency_ms"]["median"]
    p95 = benchmark["query_latency_ms"]["p95_nearest_rank"]
    largest_workload = max(comparison["row_counts"])
    comparison_results = {
        item["engine"]: item
        for item in comparison["results"]
        if item["rows"] == largest_workload
    }
    exasol_median = comparison_results["Exasol Personal"]["query_latency_ms"]["median"]
    duckdb_median = comparison_results["DuckDB"]["query_latency_ms"]["median"]
    speed_ratio = round(exasol_median / duckdb_median, 1)

    for claim in (f"{correct}/{total}",):
        if claim not in evaluation or claim not in readme:
            failures.append(f"Claim {claim!r} is inconsistent between the report and README")
    for claim in (f"{exasol_median:,.3f}", f"{duckdb_median:,.3f}"):
        if claim not in evaluation or claim not in readme:
            failures.append(
                f"Controlled benchmark {claim!r} is inconsistent between the report and README"
            )
    if not re.search(rf"{correct}\s*/\s*{total}", deck_text):
        failures.append("Holdout result is inconsistent in the deck")
    for value, label in (
        (exasol_median, "Exasol 10M median"),
        (duckdb_median, "DuckDB 10M median"),
    ):
        if str(value) not in deck_text:
            failures.append(f"Rounded {label} is inconsistent in the deck")
    if str(speed_ratio) not in deck_text:
        failures.append("Controlled benchmark ratio is inconsistent in the deck")
    for artifact_name, content in (
        ("README", readme),
        ("evaluation report", evaluation),
        ("deck", deck_text),
    ):
        if "80" not in content:
            failures.append(f"Current 80-test result is missing from the {artifact_name}")
    if "eighty" not in narration:
        failures.append("Narration does not state the current eighty-test result")

    return {
        "commit": _git("rev-parse", "HEAD").strip(),
        "video_seconds": round(video_seconds, 3),
        "slides": slide_count,
        "pdf_pages": pdf_pages,
        "failures": failures,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()
    result = verify(args.allow_dirty)
    print(json.dumps(result, indent=2))
    if result["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

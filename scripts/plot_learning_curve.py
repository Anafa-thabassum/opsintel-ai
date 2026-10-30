"""Render the measured prequential memory curve as a dependency-free SVG."""

import argparse
import html
import json
from pathlib import Path


WIDTH, HEIGHT = 820, 440
LEFT, TOP, PLOT_W, PLOT_H = 74, 42, 700, 290
SERIES = (("retrieval_success_rate", "Retrieval success", "#65c9bd"),
          ("false_match_rate", "False match rate", "#e48a92"),
          ("coverage", "Coverage", "#82aef2"))


def render_svg(report):
    points = report.get("learning_curve") or []
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">',
             '<title id="title">Verified memory prequential learning curve</title>',
             '<desc id="desc">Measured retrieval success, false match rate and coverage by previously confirmed memory size.</desc>',
             '<rect width="100%" height="100%" fill="#101722"/>',
             '<text x="28" y="25" fill="#edf3fa" font-family="sans-serif" font-size="16">Verified memory · chronological prequential results</text>']
    if not points:
        parts.append('<text x="410" y="220" text-anchor="middle" fill="#aab7ca" font-family="sans-serif" font-size="14">No measured query points available</text>')
        return "".join(parts) + "</svg>\n"

    n = len(points)
    x = lambda index: LEFT + (PLOT_W * index / max(n - 1, 1))
    y = lambda rate: TOP + PLOT_H * (1 - max(0, min(1, rate)))
    for pct in range(0, 101, 20):
        yy = y(pct / 100)
        parts.append(f'<line x1="{LEFT}" y1="{yy:.1f}" x2="{LEFT + PLOT_W}" y2="{yy:.1f}" stroke="#2a3749"/>')
        parts.append(f'<text x="{LEFT - 12}" y="{yy + 4:.1f}" text-anchor="end" fill="#9baac0" font-family="sans-serif" font-size="10">{pct}%</text>')
    for name, label, color in SERIES:
        valid = [(index, float(point[name])) for index, point in enumerate(points) if point.get(name) is not None]
        if valid:
            coords = " ".join(f"{x(index):.1f},{y(rate):.1f}" for index, rate in valid)
            parts.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2"/>')
            for index, rate in valid:
                parts.append(f'<circle cx="{x(index):.1f}" cy="{y(rate):.1f}" r="4" fill="{color}"/>')
        legend_x = LEFT + 180 * SERIES.index((name, label, color))
        parts.append(f'<circle cx="{legend_x}" cy="{HEIGHT - 74}" r="4" fill="{color}"/><text x="{legend_x + 10}" y="{HEIGHT - 70}" fill="#c8d3e1" font-family="sans-serif" font-size="11">{html.escape(label)}</text>')
    for index, point in enumerate(points):
        label = f"{point['confirmed_records_available']} verified · {point['queries']} queries · {point.get('eligible_positive_queries', 0)} labelled"
        parts.append(f'<text x="{x(index):.1f}" y="{TOP + PLOT_H + 22}" text-anchor="middle" fill="#aab7ca" font-family="sans-serif" font-size="9">{html.escape(label)}</text>')
    parts.append(f'<text x="{LEFT + PLOT_W / 2}" y="{HEIGHT - 32}" text-anchor="middle" fill="#9baac0" font-family="sans-serif" font-size="11">Previously confirmed incidents available</text>')
    parts.append("</svg>\n")
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path, help="JSON output from scripts.evaluate_memory")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    args.output.write_text(render_svg(report), encoding="utf-8")
    print(f"Wrote measured memory learning curve to {args.output}")


if __name__ == "__main__":
    main()

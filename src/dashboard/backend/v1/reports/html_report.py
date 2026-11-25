"""Self-contained HTML rendering for one-page session reports."""

from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Any

from src.version import __version__

CLASS_COLORS = {
    "glass": "#2a7f45",
    "metal": "#66778a",
    "paper": "#2457c5",
    "plastic": "#f2c230",
    "trash": "#3a3a3a",
}
CLASS_NAMES = tuple(CLASS_COLORS)


def _escaped(value: object | None, fallback: str = "Not recorded") -> str:
    if value is None or value == "":
        value = fallback
    return html.escape(str(value), quote=True)


def _confidence_label(value: float | None) -> str:
    return "Not available" if value is None else f"{value * 100:.1f}%"


def _duration_label(duration_seconds: float) -> str:
    seconds = max(0, round(duration_seconds))
    if seconds < 60:
        unit = "second" if seconds == 1 else "seconds"
        return f"{seconds} {unit}"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        if seconds:
            return f"{minutes} min {seconds} sec"
        return f"{minutes} min"
    hours, minutes = divmod(minutes, 60)
    if minutes:
        return f"{hours} h {minutes} min"
    return f"{hours} h"


def _class_chart(class_stats: dict[str, dict[str, Any]]) -> str:
    x_bar, max_bar_width = 120, 430
    rows = []
    max_count = max((int(class_stats[name]["count"]) for name in CLASS_NAMES), default=0)
    for index, class_name in enumerate(CLASS_NAMES):
        y = 22 + index * 32
        count = int(class_stats[class_name]["count"])
        width = max_bar_width * count / max_count if max_count else 0
        rows.append(
            f'<text class="chart-label" x="0" y="{y + 13}">{html.escape(class_name)}</text>'
            f'<rect x="{x_bar}" y="{y}" width="{width:.2f}" height="18" rx="5" '
            f'fill="{CLASS_COLORS[class_name]}" />'
            f'<text class="chart-value" x="{x_bar + width + 9:.2f}" y="{y + 13}">{count}</text>'
        )
    return (
        '<svg data-chart="class-counts" role="img" aria-labelledby="class-chart-title" '
        'viewBox="0 0 600 190" preserveAspectRatio="xMinYMin meet">'
        '<title id="class-chart-title">Detection counts by waste class</title>'
        '<line x1="120" y1="12" x2="120" y2="184" stroke="#e3e3e3" />'
        f"{''.join(rows)}</svg>"
    )


def _time_chart(aggregates: dict[str, Any]) -> str:
    counts = aggregates["time_buckets"]
    width, height = 600, 170
    left, right, top, bottom = 38, 16, 12, 34
    plot_width, plot_height = width - left - right, height - top - bottom
    max_count = max(counts, default=0)
    slots = max(1, len(counts))
    slot_width = plot_width / slots
    bar_width = max(2.0, slot_width * 0.68)
    bars = []
    for index, count in enumerate(counts):
        bar_height = plot_height * count / max_count if max_count else 0
        x = left + index * slot_width + (slot_width - bar_width) / 2
        y = top + plot_height - bar_height
        bars.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{bar_height:.2f}" rx="2" fill="#5173c5" />'
        )
    duration = float(aggregates["duration_seconds"])
    duration_label = _duration_label(duration)
    empty_label = (
        '<text class="chart-empty" x="300" y="78" text-anchor="middle">No detections recorded</text>'
        if max_count == 0
        else ""
    )
    return (
        '<svg data-chart="detections-over-time" role="img" aria-labelledby="time-chart-title" '
        'viewBox="0 0 600 170" preserveAspectRatio="xMinYMin meet">'
        '<title id="time-chart-title">Detections over time</title>'
        f'<line x1="{left}" y1="{top + plot_height}" x2="{width - right}" '
        f'y2="{top + plot_height}" stroke="#b7b7b7" />'
        f"{''.join(bars)}{empty_label}"
        f'<text class="axis-label" x="{left}" y="{height - 8}">0 sec</text>'
        f'<text class="axis-label" x="{width - right}" y="{height - 8}" text-anchor="end">'
        f"{html.escape(duration_label)}</text></svg>"
    )


def _class_table(class_stats: dict[str, dict[str, Any]], total: int) -> str:
    rows = []
    for class_name in CLASS_NAMES:
        stats = class_stats[class_name]
        count = int(stats["count"])
        share = f"{count / total * 100:.1f}%" if total else "0.0%"
        avg_confidence = _confidence_label(stats["avg_confidence"])
        rows.append(
            "<tr>"
            f'<th scope="row"><span class="swatch" style="background:{CLASS_COLORS[class_name]}" '
            f'aria-hidden="true"></span>{html.escape(class_name)}</th>'
            f"<td>{count}</td><td>{share}</td><td>{avg_confidence}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_report(session: dict[str, Any], aggregates: dict[str, Any]) -> str:
    """Render a safe, dependency-free report with two inline SVG charts."""
    name = _escaped(session["name"])
    model_name = _escaped(session["model_name"])
    source = _escaped(session["source"])
    status = _escaped(str(session["status"]).capitalize())
    started_at = _escaped(session["started_at"])
    date_label = html.escape(str(session["started_at"] or "Not recorded")[:10])
    total = int(session["total_detections"])
    duration = _duration_label(float(session["duration_seconds"]))
    avg_confidence = _confidence_label(session["avg_confidence"])
    notes = session["notes"]
    notes_block = f'<section class="notes"><h2>Notes</h2><p>{_escaped(notes, "")}</p></section>' if notes else ""
    class_stats = aggregates["class_stats"]
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    version = html.escape(__version__)
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MIRA session report: {name}</title>
  <style>
    :root {{ color-scheme: light; font-family: "Plus Jakarta Sans", system-ui, sans-serif; color: #1f1f1f; background: #f5f5f5; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 24px; background: #f5f5f5; font-size: 13px; line-height: 1.4; }}
    .page {{ max-width: 960px; min-height: 1120px; margin: 0 auto; padding: 30px; background: #fefefe; border: 1px solid #e3e3e3; border-radius: 14px; }}
    header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; padding-bottom: 18px; border-bottom: 1px solid #e3e3e3; }}
    .eyebrow {{ margin: 0 0 5px; color: #535253; font-size: 11px; font-weight: 650; letter-spacing: .08em; text-transform: uppercase; }}
    h1 {{ max-width: 650px; margin: 0; color: #1f1f1f; font-size: 25px; line-height: 1.2; overflow: hidden; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; overflow-wrap: anywhere; }}
    .status {{ flex: 0 0 auto; padding: 6px 10px; border: 1px solid #d6dfef; border-radius: 999px; color: #395cb8; background: #eef0f5; font-size: 11px; font-weight: 650; }}
    .meta {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 17px 0; }}
    .meta-item, .metric {{ min-width: 0; padding: 11px 13px; border: 1px solid #e3e3e3; border-radius: 10px; background: #fff; }}
    .label {{ display: block; margin-bottom: 4px; color: #7c7c7c; font-size: 10px; font-weight: 650; letter-spacing: .05em; text-transform: uppercase; }}
    .value {{ display: block; overflow: hidden; color: #1f1f1f; font-size: 13px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }}
    .metrics {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-bottom: 18px; }}
    .metric strong {{ display: block; color: #1f1f1f; font-size: 23px; line-height: 1.1; font-weight: 650; }}
    .metric .label {{ margin-bottom: 7px; }}
    .charts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 0 0 16px; }}
    .chart-card {{ min-width: 0; padding: 13px; border: 1px solid #e3e3e3; border-radius: 10px; background: #fff; }}
    h2 {{ margin: 0 0 8px; font-size: 14px; line-height: 1.3; font-weight: 650; }}
    svg {{ display: block; width: 100%; height: auto; overflow: visible; }}
    .chart-label, .chart-value, .axis-label, .chart-empty {{ fill: #535253; font-family: "Plus Jakarta Sans", system-ui, sans-serif; font-size: 11px; }}
    .chart-value {{ fill: #1f1f1f; font-weight: 650; }}
    .chart-empty {{ fill: #7c7c7c; }}
    .axis-label {{ font-size: 10px; }}
    .table-wrap {{ border: 1px solid #e3e3e3; border-radius: 10px; overflow: hidden; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
    th, td {{ padding: 7px 10px; text-align: right; border-bottom: 1px solid #e3e3e3; }}
    thead th {{ color: #535253; background: #f5f5f5; font-size: 9px; letter-spacing: .04em; text-transform: uppercase; }}
    th:first-child, td:first-child {{ text-align: left; }}
    tbody tr:last-child th, tbody tr:last-child td {{ border-bottom: 0; }}
    tbody th {{ font-weight: 600; }}
    .swatch {{ display: inline-block; width: 8px; height: 8px; margin-right: 7px; border-radius: 50%; }}
    .notes {{ margin-top: 13px; padding: 11px 13px; border-left: 3px solid #5173c5; border-radius: 4px; background: #f5f5f5; }}
    .notes h2 {{ margin-bottom: 4px; }}
    .notes p {{ display: -webkit-box; max-height: 4.2em; margin: 0; overflow: hidden; -webkit-box-orient: vertical; -webkit-line-clamp: 3; overflow-wrap: anywhere; white-space: pre-wrap; }}
    .accuracy-note {{ margin: 13px 0 0; color: #535253; font-size: 10px; }}
    footer {{ display: flex; justify-content: space-between; gap: 12px; margin-top: 14px; padding-top: 9px; border-top: 1px solid #e3e3e3; color: #7c7c7c; font-size: 9px; }}
    @media (max-width: 700px) {{ body {{ padding: 10px; }} .page {{ min-height: 0; padding: 18px; }} .meta {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} .charts {{ grid-template-columns: 1fr; }} }}
    @page {{ size: A4; margin: 12mm }}
    @media print {{
      :root, body {{ background: #fff; }}
      body {{ padding: 0; font-size: 9px; line-height: 1.25; }}
      .page {{ width: auto; max-width: none; min-height: 0; margin: 0; padding: 0; border: 0; border-radius: 0; }}
      header {{ gap: 10px; padding-bottom: 8px; }}
      h1 {{ font-size: 18px; -webkit-line-clamp: 2; }}
      .meta {{ gap: 6px; margin: 8px 0; }}
      .meta-item, .metric {{ padding: 6px 8px; border-radius: 6px; }}
      .label {{ margin-bottom: 2px; font-size: 8px; }}
      .value {{ font-size: 10px; }}
      .metrics {{ gap: 6px; margin-bottom: 8px; }}
      .metric strong {{ font-size: 16px; }}
      .metric .label {{ margin-bottom: 3px; }}
      .charts {{ grid-template-columns: 1fr 1fr; gap: 7px; margin-bottom: 8px; }}
      .chart-card {{ padding: 7px; border-radius: 6px; }}
      h2 {{ margin-bottom: 4px; font-size: 10px; }}
      .chart-card svg {{ height: 32mm; }}
      th, td {{ padding: 4px 7px; }}
      thead th {{ font-size: 7px; }}
      .notes {{ max-height: 17mm; margin-top: 7px; padding: 6px 8px; }}
      .notes h2 {{ margin-bottom: 2px; }}
      .notes p {{ max-height: 2.5em; -webkit-line-clamp: 2; }}
      .accuracy-note {{ margin-top: 7px; font-size: 8px; }}
      footer {{ margin-top: 7px; padding-top: 5px; font-size: 7px; }}
      header, .meta, .metrics, .charts, .table-wrap, .notes, footer {{ break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <header>
      <div><p class="eyebrow">MIRA session report</p><h1 class="session-name" title="{name}">{name}</h1></div>
      <span class="status">{status}</span>
    </header>
    <section class="meta" aria-label="Session details">
      <div class="meta-item"><span class="label">Date</span><span class="value" title="{started_at}">{date_label} UTC</span></div>
      <div class="meta-item"><span class="label">Duration</span><span class="value">{duration}</span></div>
      <div class="meta-item"><span class="label">Model</span><span class="value" title="{model_name}">{model_name}</span></div>
      <div class="meta-item"><span class="label">Source</span><span class="value">{source}</span></div>
    </section>
    <section class="metrics" aria-label="Session totals">
      <div class="metric"><span class="label">Total detections</span><strong>{total}</strong></div>
      <div class="metric"><span class="label">Average confidence</span><strong>{avg_confidence}</strong></div>
      <div class="metric"><span class="label">Session state</span><strong>{status}</strong></div>
    </section>
    <section class="charts" aria-label="Detection charts">
      <div class="chart-card"><h2>Detections by class</h2>{_class_chart(class_stats)}</div>
      <div class="chart-card"><h2>Detections over time</h2>{_time_chart(aggregates)}</div>
    </section>
    <section aria-labelledby="class-table-title">
      <h2 id="class-table-title">Class summary</h2>
      <div class="table-wrap"><table>
        <thead><tr><th scope="col">Class</th><th scope="col">Count</th><th scope="col">Share</th><th scope="col">Average confidence</th></tr></thead>
        <tbody>{_class_table(class_stats, total)}</tbody>
      </table></div>
    </section>
    {notes_block}
    <p class="accuracy-note">Session counts describe this run only and are not real-world sorting accuracy.</p>
    <footer><span>MIRA {version}</span><span>Generated {generated_at}</span></footer>
  </main>
</body>
</html>'''

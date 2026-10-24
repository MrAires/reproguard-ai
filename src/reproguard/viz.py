from __future__ import annotations

import re

from .models import AuditReport


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def evidence_graph_dot(report: AuditReport, max_nodes: int = 30) -> str:
    node_ids = {node.id for node in report.evidence_nodes[:max_nodes]}
    lines = [
        "digraph ReproGuard {",
        'rankdir="LR";',
        'bgcolor="transparent";',
        'graph [pad="0.35", nodesep="0.45", ranksep="0.75", splines="spline"];',
        'node [shape="box", style="rounded,filled", fontname="Arial", fontsize="10", color="#36506f", fontcolor="#e9f4ff", fillcolor="#0d1a2d", penwidth="1.1", margin="0.12,0.08"];',
        'edge [color="#4b6d91", fontcolor="#8fa6c3", fontname="Arial", fontsize="8", arrowsize="0.72", penwidth="1.0"];',
    ]
    for node in report.evidence_nodes[:max_nodes]:
        label = _escape(re.sub(r"\s+", " ", node.label)[:72])
        shape = "oval" if node.kind == "paper" else "box"
        fill = "#10283b" if node.kind == "paper" else "#0d1a2d"
        color = "#58d9f4" if node.kind == "paper" else "#36506f"
        lines.append(
            f'"{_escape(node.id)}" [label="{label}", shape="{shape}", fillcolor="{fill}", color="{color}"];'
        )
    for edge in report.evidence_edges:
        if edge.source in node_ids and edge.target in node_ids:
            lines.append(
                f'"{_escape(edge.source)}" -> "{_escape(edge.target)}" [label="{_escape(edge.label)}"];'
            )
    lines.append("}")
    return "\n".join(lines)

"""Benchmark result visualization and export.

Provides ASCII charts and JSON export for benchmark results.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class BenchmarkResult:
    """Single benchmark result."""
    name: str
    min_ms: float
    max_ms: float
    mean_ms: float
    stddev_ms: float
    ops_per_sec: float
    rounds: int


@dataclass
class BenchmarkSuite:
    """Complete benchmark suite results."""
    timestamp: str
    version: str
    results: List[BenchmarkResult]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Export to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def export_to_file(self, path: Path) -> None:
        """Export to JSON file."""
        path.write_text(self.to_json())


def render_ascii_bar(
    value: float,
    max_value: float,
    width: int = 40,
    char: str = "█"
) -> str:
    """Render an ASCII bar for visualization."""
    if max_value == 0:
        filled = 0
    else:
        filled = int((value / max_value) * width)
    filled = min(filled, width)
    empty = width - filled
    return char * filled + "░" * empty


def render_ascii_chart(
    results: List[BenchmarkResult],
    metric: str = "mean_ms",
    title: str = "Benchmark Results"
) -> str:
    """Render ASCII chart of benchmark results."""
    lines = []
    lines.append(f"╔{'═' * 68}╗")
    lines.append(f"║ {title:<66} ║")
    lines.append(f"╠{'═' * 68}╣")
    lines.append(f"║ {'Benchmark':<30} │ {'Time (ms)':>12} │ {'Ops/sec':>10} │ Bar{'':>7} ║")
    lines.append(f"╠{'─' * 68}╣")
    
    max_val = max(getattr(r, metric) for r in results) if results else 0
    
    for result in results:
        name = result.name[:28]
        val = getattr(result, metric)
        bar = render_ascii_bar(val, max_val, width=20)
        lines.append(
            f"║ {name:<30} │ {val:>12.3f} │ "
            f"{result.ops_per_sec:>10.1f} │ {bar} ║"
        )
    
    lines.append(f"╚{'═' * 68}╝")
    return "\n".join(lines)


def render_comparison_chart(
    baseline: Dict[str, Any],
    current: Dict[str, Any],
    threshold_pct: float = 10.0
) -> str:
    """Render ASCII comparison chart between baseline and current."""
    lines = []
    lines.append(f"╔{'═' * 78}╗")
    lines.append(f"║ {'Benchmark Comparison':<76} ║")
    lines.append(f"╠{'═' * 78}╣")
    lines.append(f"║ {'Benchmark':<25} │ {'Baseline':>10} │ {'Current':>10} │ {'Change':>10} │ Status ║")
    lines.append(f"╠{'─' * 78}╣")
    
    baseline_results = {r["name"]: r for r in baseline.get("results", [])}
    current_results = current.get("results", [])
    
    for curr in current_results:
        name = curr["name"][:23]
        curr_ms = curr["mean_ms"]
        
        if name in baseline_results:
            base_ms = baseline_results[name]["mean_ms"]
            if base_ms == 0:
                change_pct = 0.0
            else:
                change_pct = ((curr_ms - base_ms) / base_ms) * 100
            
            if abs(change_pct) < threshold_pct:
                status = "✓ OK"
            elif change_pct > 0:
                status = "⚠ SLOWER"
            else:
                status = "↑ FASTER"
            
            lines.append(
                f"║ {name:<25} │ {base_ms:>10.3f} │ {curr_ms:>10.3f} │ "
                f"{change_pct:>+9.1f}% │ {status:<6} ║"
            )
        else:
            lines.append(
                f"║ {name:<25} │ {'NEW':>10} │ {curr_ms:>10.3f} │ {'':>10} │ NEW    ║"
            )
    
    lines.append(f"╚{'═' * 78}╝")
    return "\n".join(lines)


def export_results_to_json(
    results: List[BenchmarkResult],
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Export benchmark results to JSON file."""
    import datetime
    
    data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "version": "0.1.0",
        "metadata": metadata or {},
        "results": [asdict(r) for r in results]
    }
    
    output_path.write_text(json.dumps(data, indent=2))


def load_results_from_json(path: Path) -> Dict[str, Any]:
    """Load benchmark results from JSON file."""
    return json.loads(path.read_text())


def detect_regression(
    baseline: Dict[str, Any],
    current: Dict[str, Any],
    threshold_pct: float = 10.0
) -> Dict[str, Any]:
    """Detect performance regressions between baseline and current."""
    regressions = []
    improvements = []
    
    baseline_results = {r["name"]: r for r in baseline.get("results", [])}
    
    for curr in current.get("results", []):
        name = curr["name"]
        if name not in baseline_results:
            continue
            
        base = baseline_results[name]
        base_ms = base["mean_ms"]
        curr_ms = curr["mean_ms"]
        
        if base_ms == 0:
            continue
            
        change_pct = ((curr_ms - base_ms) / base_ms) * 100
        
        if change_pct > threshold_pct:
            regressions.append({
                "name": name,
                "baseline_ms": base_ms,
                "current_ms": curr_ms,
                "change_pct": round(change_pct, 2)
            })
        elif change_pct < -threshold_pct:
            improvements.append({
                "name": name,
                "baseline_ms": base_ms,
                "current_ms": curr_ms,
                "change_pct": round(change_pct, 2)
            })
    
    return {
        "regressions": regressions,
        "improvements": improvements,
        "regression_count": len(regressions),
        "improvement_count": len(improvements),
        "has_regression": len(regressions) > 0,
        "threshold_pct": threshold_pct
    }

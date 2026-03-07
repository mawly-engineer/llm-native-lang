from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from runtime.runtime_stub import KairoRuntime


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    source: str
    expected_result: str


DEFAULT_CASES: List[BenchmarkCase] = [
    BenchmarkCase(case_id="case-01", source="let x = 1 in x", expected_result="1"),
    BenchmarkCase(case_id="case-02", source="let x = 2 in x", expected_result="2"),
    BenchmarkCase(case_id="case-03", source="let y = 7 in y", expected_result="7"),
]

APPROACH_ORDER: List[str] = ["mini_language", "json_baseline", "dsl_baseline"]


def _run_mini_language(case: BenchmarkCase) -> str:
    runtime = KairoRuntime()
    return runtime.execute_program_source(case.source)["result"]


def _run_json_baseline(case: BenchmarkCase) -> str:
    json_payload = {
        "kind": "json_eval",
        "program": case.source,
    }
    runtime = KairoRuntime()
    return runtime.execute_program_source(json_payload["program"])["result"]


def _run_dsl_baseline(case: BenchmarkCase) -> str:
    dsl_payload = f"EVAL::{case.source}"
    _, source = dsl_payload.split("::", 1)
    runtime = KairoRuntime()
    return runtime.execute_program_source(source)["result"]


def _run_once(approach: str, case: BenchmarkCase) -> str:
    if approach == "mini_language":
        return _run_mini_language(case)
    if approach == "json_baseline":
        return _run_json_baseline(case)
    if approach == "dsl_baseline":
        return _run_dsl_baseline(case)
    raise ValueError(f"unknown approach: {approach}")


def _build_case_metrics(outputs: List[str], expected_result: str) -> Dict[str, Any]:
    attempts = len(outputs)
    success_count = sum(1 for output in outputs if output == expected_result)
    reproducible_count = 1 if len(set(outputs)) == 1 else 0
    return {
        "attempts": attempts,
        "success_count": success_count,
        "success_rate": success_count / attempts,
        "reproducible_count": reproducible_count,
        "reproducibility_rate": reproducible_count,
        "first_output": outputs[0] if outputs else None,
    }


def run_benchmark(cases: List[BenchmarkCase] | None = None, attempts_per_case: int = 3) -> Dict[str, Any]:
    selected_cases = cases or DEFAULT_CASES

    approaches: Dict[str, Any] = {}
    ranking: List[Tuple[str, float, float]] = []

    for approach in APPROACH_ORDER:
        case_results: List[Dict[str, Any]] = []
        total_attempts = 0
        total_successes = 0
        total_reproducible = 0

        for case in selected_cases:
            outputs = [_run_once(approach, case) for _ in range(attempts_per_case)]
            metrics = _build_case_metrics(outputs, case.expected_result)
            total_attempts += metrics["attempts"]
            total_successes += metrics["success_count"]
            total_reproducible += metrics["reproducible_count"]
            case_results.append(
                {
                    "case_id": case.case_id,
                    "source": case.source,
                    "expected_result": case.expected_result,
                    "outputs": outputs,
                    "metrics": metrics,
                }
            )

        success_rate = total_successes / total_attempts if total_attempts else 0.0
        reproducibility_rate = total_reproducible / len(selected_cases) if selected_cases else 0.0
        ranking.append((approach, success_rate, reproducibility_rate))

        approaches[approach] = {
            "total_attempts": total_attempts,
            "total_successes": total_successes,
            "success_rate": success_rate,
            "reproducibility_rate": reproducibility_rate,
            "case_results": case_results,
        }

    ranking.sort(key=lambda row: (-row[1], -row[2], APPROACH_ORDER.index(row[0])))

    return {
        "benchmark_id": "PRX-02-baseline-benchmark",
        "attempts_per_case": attempts_per_case,
        "cases_total": len(selected_cases),
        "approaches": approaches,
        "ranking": [
            {
                "approach": approach,
                "success_rate": success_rate,
                "reproducibility_rate": reproducibility_rate,
            }
            for approach, success_rate, reproducibility_rate in ranking
        ],
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_benchmark(), indent=2, sort_keys=True))

from __future__ import annotations

from typing import Any, Dict, List

from runtime.runtime_stub import KairoRuntime


DEFAULT_PROGRAMS: List[str] = [
    "let x = 1 in x",
    "let x = 2 in x",
    "let y = 7 in y",
]


def build_example_run_artifact(programs: List[str] | None = None) -> Dict[str, Any]:
    """Run a deterministic source->patch->replay flow and emit a proof artifact."""
    selected_programs = programs or DEFAULT_PROGRAMS

    runtime = KairoRuntime()
    runs: List[Dict[str, str]] = []

    for source in selected_programs:
        run_result = runtime.execute_program_source(source)
        runs.append({
            "source": source,
            "revision": run_result["revision"],
            "run_node_id": run_result["run_node_id"],
            "result": run_result["result"],
        })

    replay_a = runtime.replay_ui_timeline(include_metrics=True)

    clone = KairoRuntime()
    for source in selected_programs:
        clone.execute_program_source(source)
    replay_b = clone.replay_ui_timeline(include_metrics=True)

    return {
        "programs": selected_programs,
        "runs": runs,
        "replay": replay_a,
        "determinism_proof": {
            "ops_equal": replay_a["ops"] == replay_b["ops"],
            "events_replayed_equal": replay_a["metrics"]["events_replayed"] == replay_b["metrics"]["events_replayed"],
            "events_total_equal": replay_a["metrics"]["events_total"] == replay_b["metrics"]["events_total"],
        },
    }


if __name__ == "__main__":
    import json

    print(json.dumps(build_example_run_artifact(), indent=2, sort_keys=True))

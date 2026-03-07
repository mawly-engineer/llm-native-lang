from typing import Any, Dict, List

from runtime.runtime_stub import KairoRuntime


RECIPE_PACK: List[Dict[str, Any]] = [
    {
        "id": "RECIPE-01-ARITHMETIC-CHAIN",
        "task": "Compute a deterministic arithmetic rollup",
        "source": "let subtotal = 19 in let tax = 6 in add(subtotal,tax)",
        "expected_result": "25",
        "run_node_id": "recipe.arithmetic.chain",
    },
    {
        "id": "RECIPE-02-BOOLEAN-GATE",
        "task": "Check deterministic boolean guard behavior",
        "source": "if true and true then true else false",
        "expected_result": "true",
        "run_node_id": "recipe.boolean.gate",
    },
    {
        "id": "RECIPE-03-INVOICE-TOTAL",
        "task": "Compute invoice total using lexical bindings",
        "source": "let base = 120 in let shipping = 15 in add(base,shipping)",
        "expected_result": "135",
        "run_node_id": "recipe.invoice.total",
    },
]


def run_cookbook_recipe_pack() -> Dict[str, Any]:
    runtime = KairoRuntime()
    runs: List[Dict[str, Any]] = []

    for index, recipe in enumerate(RECIPE_PACK, start=1):
        patch_id = f"p-cookbook-{index:02d}"
        result = runtime.execute_program_source(
            source=recipe["source"],
            env={"add": lambda a, b: a + b},
            run_node_id=recipe["run_node_id"],
            patch_id=patch_id,
        )
        runs.append(
            {
                "recipe_id": recipe["id"],
                "task": recipe["task"],
                "source": recipe["source"],
                "expected_result": recipe["expected_result"],
                "actual_result": result["result"],
                "revision": result["revision"],
                "run_node_id": result["run_node_id"],
                "pass": result["result"] == recipe["expected_result"],
            }
        )

    replay = runtime.replay_ui_timeline(include_metrics=True)
    return {
        "recipe_count": len(RECIPE_PACK),
        "runs": runs,
        "replay": replay,
        "all_passed": all(run["pass"] for run in runs),
    }


def deterministic_recipe_acceptance() -> Dict[str, Any]:
    first = run_cookbook_recipe_pack()
    second = run_cookbook_recipe_pack()

    first_results = [run["actual_result"] for run in first["runs"]]
    second_results = [run["actual_result"] for run in second["runs"]]

    return {
        "first": first,
        "second": second,
        "deterministic_results": first_results == second_results,
        "deterministic_replay_ops": first["replay"]["ops"] == second["replay"]["ops"],
        "deterministic_replay_events": (
            first["replay"]["metrics"]["events_replayed"]
            == second["replay"]["metrics"]["events_replayed"]
        ),
    }

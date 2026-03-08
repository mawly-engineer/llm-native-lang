import json
import unittest

from runtime.grammar_contract import parse_expr
from runtime.interpreter_runtime import eval_expr
from runtime.runtime_stub import KairoRuntime


class DeterminismRegressionSuite(unittest.TestCase):
    def _capture_language_run_artifact(self, source: str) -> str:
        runtime = KairoRuntime()
        result = runtime.execute_program_source(
            source=source,
            env={"inc": lambda x: x + 1, "add": lambda a, b: a + b},
            run_node_id="language.run",
            patch_id="p-language-run",
        )

        replay = runtime.replay_ui_timeline(include_metrics=True)
        head_revision = runtime.state.revisions[runtime.state.head]

        artifact = {
            "source": source,
            "execution_result": result,
            "head_revision": head_revision.id,
            "graph": head_revision.graph,
            "ui_revision": head_revision.ui_revision,
            "ui_replay": replay,
        }
        return json.dumps(artifact, sort_keys=True, separators=(",", ":"))

    def test_parser_and_evaluator_produce_byte_identical_outputs(self) -> None:
        source = "let x = add(inc(1),2) in if true then x else 0"
        ast = parse_expr(source)

        first = {
            "ast": ast,
            "result": eval_expr(ast, env={"inc": lambda x: x + 1, "add": lambda a, b: a + b}),
        }
        second = {
            "ast": parse_expr(source),
            "result": eval_expr(parse_expr(source), env={"inc": lambda x: x + 1, "add": lambda a, b: a + b}),
        }

        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )

    def test_runtime_language_run_artifacts_are_byte_identical_across_repeated_runs(self) -> None:
        source = "let total = add(inc(1), add(2,3)) in total"

        first = self._capture_language_run_artifact(source)
        second = self._capture_language_run_artifact(source)
        third = self._capture_language_run_artifact(source)

        self.assertEqual(first, second)
        self.assertEqual(second, third)

    def test_runtime_error_artifacts_are_byte_identical_across_repeated_runs(self) -> None:
        source = "let x = [1,2] in x[9]"

        def capture_error() -> str:
            runtime = KairoRuntime()
            try:
                runtime.execute_program_source(source=source)
            except Exception as exc:  # PatchError expected; keep payload stable
                payload = {
                    "type": type(exc).__name__,
                    "message": str(exc),
                }
                return json.dumps(payload, sort_keys=True, separators=(",", ":"))
            self.fail("expected runtime error artifact")

        first = capture_error()
        second = capture_error()

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()

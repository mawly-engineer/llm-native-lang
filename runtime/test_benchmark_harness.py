import unittest

from runtime.benchmark_harness import run_benchmark


class BenchmarkHarnessTest(unittest.TestCase):
    def test_benchmark_produces_acceptance_metrics_for_all_approaches(self) -> None:
        artifact = run_benchmark(attempts_per_case=3)

        self.assertEqual(artifact["benchmark_id"], "PRX-02-baseline-benchmark")
        self.assertEqual(artifact["attempts_per_case"], 3)
        self.assertEqual(artifact["cases_total"], 3)

        for approach in ("mini_language", "json_baseline", "dsl_baseline"):
            self.assertIn(approach, artifact["approaches"])
            metrics = artifact["approaches"][approach]
            self.assertEqual(metrics["success_rate"], 1.0)
            self.assertEqual(metrics["reproducibility_rate"], 1.0)
            self.assertEqual(len(metrics["case_results"]), artifact["cases_total"])

    def test_benchmark_artifact_is_deterministic_for_same_inputs(self) -> None:
        first = run_benchmark(attempts_per_case=3)
        second = run_benchmark(attempts_per_case=3)

        self.assertEqual(first, second)
        self.assertEqual(first["ranking"][0]["approach"], "mini_language")


if __name__ == "__main__":
    unittest.main()

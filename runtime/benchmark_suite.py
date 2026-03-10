"""Performance benchmarking suite for llm-native-lang interpreter.

Measures parse/eval performance for common expression patterns.
Tracks performance regression across commits.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from runtime.grammar_contract import parse_expr
from runtime.interpreter_runtime import eval_expr


@dataclass(frozen=True)
class BenchmarkWorkload:
    """Single benchmark workload definition."""
    workload_id: str
    category: str
    description: str
    source: str
    expected_result: Any
    tags: List[str] = field(default_factory=list)


@dataclass
class BenchmarkMetrics:
    """Metrics collected for a single benchmark execution."""
    workload_id: str
    parse_time_ms: float
    eval_time_ms: float
    total_time_ms: float
    fuel_consumed: Optional[int]
    success: bool
    error: Optional[str] = None


@dataclass
class BenchmarkResult:
    """Complete result for a benchmark workload."""
    workload: BenchmarkWorkload
    metrics: BenchmarkMetrics
    iterations: int
    avg_parse_time_ms: float
    avg_eval_time_ms: float
    avg_total_time_ms: float
    std_parse_ms: float
    std_eval_ms: float


# Representative benchmark workloads
BENCHMARK_WORKLOADS: List[BenchmarkWorkload] = [
    # Parser performance workloads
    BenchmarkWorkload(
        workload_id="parser-001",
        category="parser",
        description="Simple literal",
        source="42",
        expected_result=42,
        tags=["parser", "literal", "int"],
    ),
    BenchmarkWorkload(
        workload_id="parser-002",
        category="parser",
        description="Nested arithmetic",
        source="1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10",
        expected_result=55,
        tags=["parser", "arithmetic", "deep"],
    ),
    BenchmarkWorkload(
        workload_id="parser-003",
        category="parser",
        description="Deeply nested expression",
        source="((((((((((42))))))))))",
        expected_result=42,
        tags=["parser", "nesting", "parens"],
    ),
    BenchmarkWorkload(
        workload_id="parser-004",
        category="parser",
        description="Large object literal",
        source='{"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7, "h": 8, "i": 9, "j": 10}',
        expected_result={"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7, "h": 8, "i": 9, "j": 10},
        tags=["parser", "object", "large-literal"],
    ),
    BenchmarkWorkload(
        workload_id="parser-005",
        category="parser",
        description="Large list literal",
        source="[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]",
        expected_result=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        tags=["parser", "list", "large-literal"],
    ),
    
    # Evaluator performance workloads
    BenchmarkWorkload(
        workload_id="eval-001",
        category="evaluator",
        description="Simple let binding",
        source="let x = 42 in x",
        expected_result=42,
        tags=["evaluator", "let", "simple"],
    ),
    BenchmarkWorkload(
        workload_id="eval-002",
        category="evaluator",
        description="Recursive factorial (n=10)",
        source="""let rec fact = fn(n) =>
            if n == 0 then 1 else n * fact(n - 1)
        in fact(10)""",
        expected_result=3628800,
        tags=["evaluator", "recursive", "factorial"],
    ),
    BenchmarkWorkload(
        workload_id="eval-003",
        category="evaluator",
        description="Deep function nesting",
        source="""let f = fn(x) => x + 1 in
        let g = fn(x) => f(f(x)) in
        let h = fn(x) => g(g(x)) in
        h(h(h(h(0))))""",
        expected_result=16,
        tags=["evaluator", "functions", "nesting"],
    ),
    BenchmarkWorkload(
        workload_id="eval-004",
        category="evaluator",
        description="List operations",
        source="""let xs = [1, 2, 3, 4, 5] in
        let sum = fn(xs) =>
            if xs == [] then 0 else xs[0] + sum(xs[1:])
        in sum(xs)""",
        expected_result=15,
        tags=["evaluator", "list", "recursion"],
    ),
    BenchmarkWorkload(
        workload_id="eval-005",
        category="evaluator",
        description="Object member access",
        source='let person = {"name": "Alice", "age": 30, "city": "NYC"} in person.name',
        expected_result="Alice",
        tags=["evaluator", "object", "member-access"],
    ),
    BenchmarkWorkload(
        workload_id="eval-006",
        category="evaluator",
        description="String concatenation",
        source='let greet = fn(name) => "Hello, " + name in greet("World")',
        expected_result="Hello, World",
        tags=["evaluator", "string", "concat"],
    ),
    BenchmarkWorkload(
        workload_id="eval-007",
        category="evaluator",
        description="Range generation",
        source="range(1, 100, 1)",
        expected_result=list(range(1, 100)),
        tags=["evaluator", "range", "list"],
    ),
    BenchmarkWorkload(
        workload_id="eval-008",
        category="evaluator",
        description="List slicing",
        source="[1, 2, 3, 4, 5, 6, 7, 8, 9, 10][2:8:2]",
        expected_result=[3, 5, 7],
        tags=["evaluator", "list", "slice"],
    ),
    
    # Memory/closure workloads
    BenchmarkWorkload(
        workload_id="mem-001",
        category="memory",
        description="Closure capture",
        source="""let makeAdder = fn(x) => fn(y) => x + y in
        let add5 = makeAdder(5) in
        add5(10)""",
        expected_result=15,
        tags=["memory", "closure", "capture"],
    ),
    BenchmarkWorkload(
        workload_id="mem-002",
        category="memory",
        description="Multiple closures",
        source="""let makeCounter = fn() =>
            let count = 0 in
            fn() => count + 1
        in makeCounter()()""",
        expected_result=1,
        tags=["memory", "closure", "counter"],
    ),
]


def run_single_benchmark(
    workload: BenchmarkWorkload,
    iterations: int = 5,
    fuel_limit: Optional[int] = 100000,
) -> BenchmarkResult:
    """Execute a benchmark workload multiple times and collect metrics."""
    parse_times = []
    eval_times = []
    total_times = []
    fuel_consumed = None
    success = False
    error = None
    
    for _ in range(iterations):
        try:
            # Parse phase timing
            parse_start = time.perf_counter()
            ast = parse_expr(workload.source)
            parse_end = time.perf_counter()
            parse_time_ms = (parse_end - parse_start) * 1000
            
            # Eval phase timing
            eval_start = time.perf_counter()
            result = eval_expr(ast, fuel_limit=fuel_limit)
            eval_end = time.perf_counter()
            eval_time_ms = (eval_end - eval_start) * 1000
            
            total_time_ms = parse_time_ms + eval_time_ms
            
            # Verify result correctness
            if result == workload.expected_result:
                parse_times.append(parse_time_ms)
                eval_times.append(eval_time_ms)
                total_times.append(total_time_ms)
                success = True
            else:
                error = f"Result mismatch: got {result}, expected {workload.expected_result}"
                
        except Exception as e:
            error = str(e)
            break
    
    # Calculate statistics
    if parse_times:
        avg_parse = sum(parse_times) / len(parse_times)
        avg_eval = sum(eval_times) / len(eval_times)
        avg_total = sum(total_times) / len(total_times)
        
        # Standard deviation
        if len(parse_times) > 1:
            variance_parse = sum((t - avg_parse) ** 2 for t in parse_times) / (len(parse_times) - 1)
            variance_eval = sum((t - avg_eval) ** 2 for t in eval_times) / (len(eval_times) - 1)
            std_parse = variance_parse ** 0.5
            std_eval = variance_eval ** 0.5
        else:
            std_parse = 0.0
            std_eval = 0.0
    else:
        avg_parse = avg_eval = avg_total = 0.0
        std_parse = std_eval = 0.0
    
    metrics = BenchmarkMetrics(
        workload_id=workload.workload_id,
        parse_time_ms=avg_parse,
        eval_time_ms=avg_eval,
        total_time_ms=avg_total,
        fuel_consumed=fuel_consumed,
        success=success,
        error=error,
    )
    
    return BenchmarkResult(
        workload=workload,
        metrics=metrics,
        iterations=len(parse_times),
        avg_parse_time_ms=avg_parse,
        avg_eval_time_ms=avg_eval,
        avg_total_time_ms=avg_total,
        std_parse_ms=std_parse,
        std_eval_ms=std_eval,
    )


def run_benchmark_suite(
    workloads: Optional[List[BenchmarkWorkload]] = None,
    iterations: int = 5,
    fuel_limit: Optional[int] = 100000,
) -> Dict[str, Any]:
    """Run the complete benchmark suite and return structured results."""
    selected_workloads = workloads or BENCHMARK_WORKLOADS
    
    results: List[BenchmarkResult] = []
    category_stats: Dict[str, Dict[str, float]] = {}
    
    for workload in selected_workloads:
        result = run_single_benchmark(workload, iterations, fuel_limit)
        results.append(result)
        
        # Aggregate category stats
        cat = workload.category
        if cat not in category_stats:
            category_stats[cat] = {"total_time_ms": 0.0, "count": 0, "success": 0}
        category_stats[cat]["total_time_ms"] += result.avg_total_time_ms
        category_stats[cat]["count"] += 1
        if result.metrics.success:
            category_stats[cat]["success"] += 1
    
    # Build summary
    total_time = sum(r.avg_total_time_ms for r in results)
    success_count = sum(1 for r in results if r.metrics.success)
    
    summary = {
        "benchmark_id": "LNG-BENCH-001",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "iterations_per_workload": iterations,
        "fuel_limit": fuel_limit,
        "total_workloads": len(results),
        "successful_workloads": success_count,
        "failed_workloads": len(results) - success_count,
        "total_time_ms": round(total_time, 3),
        "category_summary": {
            cat: {
                "workloads": stats["count"],
                "total_time_ms": round(stats["total_time_ms"], 3),
                "avg_time_per_workload_ms": round(stats["total_time_ms"] / stats["count"], 3) if stats["count"] else 0,
                "success_rate": stats["success"] / stats["count"] if stats["count"] else 0,
            }
            for cat, stats in category_stats.items()
        },
    }
    
    # Build detailed results
    detailed_results = []
    for r in results:
        detailed_results.append({
            "workload_id": r.workload.workload_id,
            "category": r.workload.category,
            "description": r.workload.description,
            "source": r.workload.source,
            "iterations": r.iterations,
            "avg_parse_time_ms": round(r.avg_parse_time_ms, 3),
            "avg_eval_time_ms": round(r.avg_eval_time_ms, 3),
            "avg_total_time_ms": round(r.avg_total_time_ms, 3),
            "std_parse_ms": round(r.std_parse_ms, 3),
            "std_eval_ms": round(r.std_eval_ms, 3),
            "success": r.metrics.success,
            "error": r.metrics.error,
        })
    
    return {
        "summary": summary,
        "results": detailed_results,
    }


def export_results(results: Dict[str, Any], filepath: str) -> None:
    """Export benchmark results to JSON file."""
    with open(filepath, "w") as f:
        json.dump(results, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    results = run_benchmark_suite()
    print(json.dumps(results, indent=2))

"""Pytest configuration and fixtures for benchmarks."""

from __future__ import annotations

import json
import random
import string
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime.grammar_contract import parse_expr
from runtime.interpreter_runtime import eval_expr


# ASCII visualization for benchmark reports
BENCHMARK_ASCII_ART = """
╔══════════════════════════════════════════════════════════════╗
║     llm-native-lang Performance Benchmark Suite              ║
╚══════════════════════════════════════════════════════════════╝
"""


def pytest_benchmark_scale_unit(unit: str) -> str:
    """Custom scale unit formatter."""
    if unit == "seconds":
        return "ms"
    return unit


@pytest.fixture(scope="session")
def sample_lnd_content() -> str:
    """Generate sample LND content for parsing benchmarks."""
    return '''@lnd 0.2
kind: work_item
id: TEST-ITEM-001
status: active
updated_at_utc: 2026-03-11T20:22:00Z

title: "Sample work item for benchmarking"
objective: language_core_capability
priority: p0

stage: create
bucket: language

description: |
  This is a sample work item used for benchmarking
  the LND parser performance across multiple iterations.

next_id: 2
'''


@pytest.fixture(scope="session")
def large_lnd_content() -> str:
    """Generate large LND content for scaling tests."""
    items = []
    for i in range(100):
        items.append(f"""
  - id: ITEM-{i:04d}
    title: "Test item {i}"
    status: open
    priority: p1""")
    
    return f'''@lnd 0.2
kind: work_items
id: BENCH-LARGE-001
status: active
updated_at_utc: 2026-03-11T20:22:00Z

backlog:
{''.join(items)}

next_id: 100
'''


@pytest.fixture(scope="session")
def sample_lnc_contract() -> Dict[str, Any]:
    """Sample LNC contract for execution benchmarks."""
    return {
        "version": "0.1",
        "kind": "task",
        "id": "BENCH-TASK-001",
        "title": "Benchmark task",
        "description": "Simple arithmetic for benchmarking",
        "input": {"x": 10, "y": 20},
        "operation": "add"
    }


@pytest.fixture
def temp_lnd_file(tmp_path: Path, sample_lnd_content: str) -> Path:
    """Create a temporary LND file."""
    file_path = tmp_path / "test_item.lnd"
    file_path.write_text(sample_lnd_content)
    return file_path


@pytest.fixture
def temp_lnd_directory(tmp_path: Path, sample_lnd_content: str) -> Path:
    """Create a temporary directory with multiple LND files."""
    dir_path = tmp_path / "lnd_files"
    dir_path.mkdir()
    
    # Create 50 LND files
    for i in range(50):
        file_path = dir_path / f"item_{i:03d}.lnd"
        content = sample_lnd_content.replace("TEST-ITEM-001", f"BENCH-ITEM-{i:04d}")
        file_path.write_text(content)
    
    return dir_path


@pytest.fixture
def benchmark_data_dir() -> Path:
    """Return the benchmark data directory."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


class BenchmarkConfig:
    """Configuration for benchmark thresholds."""
    
    # Minimum performance requirements
    LND_PARSE_MIN_FILES_PER_SEC = 100
    LNC_EXEC_MIN_OPS_PER_SEC = 1000
    
    # Regression threshold (10% slowdown fails)
    REGRESSION_THRESHOLD_PERCENT = 10.0
    
    # Memory thresholds (MB)
    MAX_MEMORY_MB_LARGE_FILE = 100
    
    # Benchmark iterations
    DEFAULT_ITERATIONS = 5
    WARMUP_ITERATIONS = 2


@pytest.fixture(scope="session")
def config() -> BenchmarkConfig:
    """Return benchmark configuration."""
    return BenchmarkConfig()


@pytest.fixture(scope="session", autouse=True)
def print_banner():
    """Print benchmark banner at session start."""
    print(BENCHMARK_ASCII_ART)

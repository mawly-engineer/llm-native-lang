"""Benchmark tests for LND file parsing performance.

Validates:
- Parse speed: minimum 100 files/sec
- Memory efficiency for large files
- Scaling behavior across file sizes
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import List

import pytest

from scripts.lnd_validate import validate_lnd_file, parse_lnd_file


class TestLNDParseBenchmarks:
    """Performance benchmarks for LND file parsing."""
    
    def test_single_lnd_file_parse(self, sample_lnd_content: str, benchmark) -> None:
        """Benchmark parsing a single LND file."""
        def parse():
            return parse_lnd_file(sample_lnd_content, "test.lnd")
        
        result = benchmark(parse)
        assert result is not None
        assert result.get("kind") == "work_item"
    
    def test_lnd_file_validation(self, temp_lnd_file: Path, benchmark) -> None:
        """Benchmark LND file validation."""
        def validate():
            return validate_lnd_file(temp_lnd_file)
        
        is_valid, errors = benchmark(validate)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_large_lnd_parse(self, large_lnd_content: str, benchmark) -> None:
        """Benchmark parsing large LND content (100 items)."""
        def parse_large():
            return parse_lnd_file(large_lnd_content, "large.lnd")
        
        result = benchmark(parse_large)
        assert result is not None
        assert result.get("kind") == "work_items"
    
    def test_batch_validation_scaling(self, temp_lnd_directory: Path, config) -> None:
        """Test batch validation meets 100 files/sec minimum.
        
        This is a throughput test, not a microbenchmark.
        """
        import os
        
        files = list(temp_lnd_directory.glob("*.lnd"))
        assert len(files) == 50, f"Expected 50 files, got {len(files)}"
        
        # Time the batch validation
        start = time.perf_counter()
        
        for file_path in files:
            is_valid, _ = validate_lnd_file(file_path)
            assert is_valid, f"Failed validation: {file_path}"
        
        elapsed = time.perf_counter() - start
        files_per_sec = len(files) / elapsed
        
        # Assert meets minimum requirement (100 files/sec)
        assert files_per_sec >= config.LND_PARSE_MIN_FILES_PER_SEC, (
            f"Parse rate {files_per_sec:.1f} files/sec below minimum "
            f"{config.LND_PARSE_MIN_FILES_PER_SEC} files/sec"
        )
    
    @pytest.mark.parametrize("file_size_kb", [1, 10, 100])
    def test_parse_scaling_by_size(self, tmp_path: Path, file_size_kb: int, config) -> None:
        """Test parse performance scales reasonably with file size."""
        # Generate LND content of specified size
        num_items = file_size_kb * 10  # Approximate
        items = []
        for i in range(num_items):
            items.append(f"  - id: ITEM-{i:04d}\n    title: \"Item {i}\"\n    status: open")
        
        content = f"""@lnd 0.2
kind: work_items
id: SCALE-TEST-{file_size_kb}KB
status: active
updated_at_utc: 2026-03-11T20:22:00Z

backlog:
{chr(10).join(items)}

next_id: {num_items}
"""
        
        # Time single parse
        start = time.perf_counter()
        result = parse_lnd_file(content, f"scale_{file_size_kb}kb.lnd")
        elapsed = time.perf_counter() - start
        
        assert result is not None
        # Should parse 100KB file in under 100ms
        assert elapsed < 0.1, f"Parse took {elapsed*1000:.1f}ms for {file_size_kb}KB"


class TestLNDMemoryBenchmarks:
    """Memory usage benchmarks for LND operations."""
    
    def test_memory_usage_large_parse(self, large_lnd_content: str) -> None:
        """Test memory usage stays bounded for large files."""
        import gc
        import psutil
        
        gc.collect()
        process = psutil.Process()
        mem_before = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Parse large file 10 times
        for _ in range(10):
            result = parse_lnd_file(large_lnd_content, "large.lnd")
            del result
        
        gc.collect()
        mem_after = process.memory_info().rss / (1024 * 1024)  # MB
        
        mem_increase = mem_after - mem_before
        # Should not use more than 50MB for this workload
        assert mem_increase < 50, f"Memory increased by {mem_increase:.1f}MB"

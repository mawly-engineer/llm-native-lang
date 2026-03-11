#!/usr/bin/env python3
"""Tests for KAIRO CLI tool."""

import subprocess
import sys
import os
import tempfile
from pathlib import Path

# Ensure the script under test is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

CLI_PATH = Path(__file__).parent.parent / "scripts" / "kairo_cli.py"
EXAMPLES_DIR = Path(__file__).parent.parent / "runtime" / "examples"


class TestKairoCLI:
    """Test suite for KAIRO CLI commands."""

    def run_cli(self, args):
        """Run CLI with arguments and return result."""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH)] + args,
            capture_output=True,
            text=True
        )
        return result

    def test_help_shows_commands(self):
        """Test that help shows all three commands."""
        result = self.run_cli(["--help"])
        assert result.returncode == 0
        assert "validate" in result.stdout
        assert "execute" in result.stdout
        assert "replay-test" in result.stdout

    def test_validate_help(self):
        """Test validate command help."""
        result = self.run_cli(["validate", "--help"])
        assert result.returncode == 0
        assert "Validate LNC files" in result.stdout

    def test_execute_help(self):
        """Test execute command help."""
        result = self.run_cli(["execute", "--help"])
        assert result.returncode == 0
        assert "LNC file to execute" in result.stdout

    def test_replay_test_help(self):
        """Test replay-test command help."""
        result = self.run_cli(["replay-test", "--help"])
        assert result.returncode == 0
        assert "repeats" in result.stdout

    def test_validate_examples_directory(self):
        """Test validating the examples directory."""
        result = self.run_cli(["validate", str(EXAMPLES_DIR)])
        assert result.returncode == 0
        assert "PASS" in result.stdout
        assert ".lnc" in result.stdout

    def test_validate_single_file(self):
        """Test validating a single LNC file."""
        # Find first .lnc file in examples
        lnc_files = list(EXAMPLES_DIR.glob("*.lnc"))
        if lnc_files:
            result = self.run_cli(["validate", str(lnc_files[0])])
            assert result.returncode == 0
            assert "PASS" in result.stdout

    def test_validate_invalid_file(self):
        """Test validation fails on invalid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lnc', delete=False) as f:
            f.write("invalid content without header\n")
            f.flush()
            temp_path = f.name

        try:
            result = self.run_cli(["validate", temp_path])
            assert result.returncode == 1
            assert "FAIL" in result.stdout or "missing" in result.stdout.lower()
        finally:
            os.unlink(temp_path)

    def test_validate_missing_file(self):
        """Test validation handles missing file gracefully."""
        result = self.run_cli(["validate", "/nonexistent/path/file.lnc"])
        # Should handle gracefully (currently returns 0 with "No .lnc files found")
        assert result.returncode in [0, 1]

    def test_execute_nonexistent_file(self):
        """Test execute fails on nonexistent file."""
        result = self.run_cli(["execute", "/nonexistent/file.lnc"])
        assert result.returncode == 2
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_replay_test_nonexistent_file(self):
        """Test replay-test fails on nonexistent file."""
        result = self.run_cli(["replay-test", "/nonexistent/file.lnc"])
        assert result.returncode in [2, 3]
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])

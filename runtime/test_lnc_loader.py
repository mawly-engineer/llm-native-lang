#!/usr/bin/env python3
"""Tests for LNC Contract Loader - runtime replay integration."""
import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/home/node/.openclaw/workspace/llm-native-lang')

from runtime.lnc_contract_loader import LNCContract, LNCContractExecutor, LNCContractReplayHarness


class TestLNCContractParsing(unittest.TestCase):
    """Test LNC contract parsing without external yaml dependency."""
    
    def test_load_counter_contract(self):
        """Test loading a canonical LNC contract."""
        path = Path('/home/node/.openclaw/workspace/llm-native-lang/runtime/examples/canonical_counter.lnc')
        contract = LNCContract.from_file(path)
        self.assertEqual(contract.id, 'EXAMPLE-CANONICAL-COUNTER-01')
        self.assertIn('stable_replay', contract.deterministic_flags)
        self.assertIn('stable_parse', contract.deterministic_flags)
        self.assertIn('stable_eval', contract.deterministic_flags)
        self.assertEqual(contract.source_lang, 'minilang')
        self.assertEqual(contract.entry, 'main')
    
    def test_parse_yaml_lite_handles_multiline(self):
        """Test the lightweight YAML parser handles multiline values."""
        yaml_content = """
source: let seed = 2; let value = seed * (3 + 4); value == 14
deterministic_flags:
  - stable_parse
  - stable_eval
  - stable_replay
"""
        from runtime.lnc_contract_loader import parse_yaml_lite
        result = parse_yaml_lite(yaml_content)
        self.assertEqual(result['source'], 'let seed = 2; let value = seed * (3 + 4); value == 14')
        self.assertEqual(result['deterministic_flags'], ['stable_parse', 'stable_eval', 'stable_replay'])


class TestLNCContractExecutor(unittest.TestCase):
    """Test LNC contract execution with replay conformance."""
    
    def test_load_contract_into_executor(self):
        """Test loading a contract into the executor."""
        executor = LNCContractExecutor()
        path = Path('/home/node/.openclaw/workspace/llm-native-lang/runtime/examples/canonical_counter.lnc')
        contract = executor.load_contract(path)
        self.assertEqual(contract.id, 'EXAMPLE-CANONICAL-COUNTER-01')
        self.assertIn(contract.id, executor.contracts)
    
    def test_load_directory_contracts(self):
        """Test loading all contracts from a directory."""
        executor = LNCContractExecutor()
        dir_path = Path('/home/node/.openclaw/workspace/llm-native-lang/runtime/examples')
        contracts = executor.load_contracts_from_dir(dir_path)
        self.assertGreaterEqual(len(contracts), 3)  # At least 3 example LNC files
    
    def test_replay_check_flags(self):
        """Test replay contract returns appropriate flags check."""
        executor = LNCContractExecutor()
        path = Path('/home/node/.openclaw/workspace/llm-native-lang/runtime/examples/canonical_counter.lnc')
        contract = executor.load_contract(path)
        
        # Check all required deterministic flags are present
        self.assertIn('stable_parse', contract.deterministic_flags)
        self.assertIn('stable_eval', contract.deterministic_flags)
        self.assertIn('stable_replay', contract.deterministic_flags)


class TestLNCContractReplayHarness(unittest.TestCase):
    """Test the high-level replay conformance harness."""
    
    def test_harness_init(self):
        """Test harness initialization."""
        harness = LNCContractReplayHarness()
        self.assertIsNotNone(harness.executor)
        self.assertEqual(len(harness.results), 0)
    
    def test_get_summary_empty(self):
        """Test summary with no results."""
        harness = LNCContractReplayHarness()
        summary = harness.get_summary()
        self.assertEqual(summary['total_contracts'], 0)
        self.assertEqual(summary['deterministic'], 0)


class TestLNCIntegration(unittest.TestCase):
    """Integration tests for LNC with replay system."""
    
    def test_contract_structure_integrity(self):
        """Verify contract structure matches expected format."""
        path = Path('/home/node/.openclaw/workspace/llm-native-lang/runtime/examples/canonical_counter.lnc')
        contract = LNCContract.from_file(path)
        
        # Verify all required fields
        self.assertIsNotNone(contract.lnc_version)
        self.assertIsNotNone(contract.kind)
        self.assertIsNotNone(contract.id)
        self.assertIsNotNone(contract.module)
        self.assertIsNotNone(contract.source)
        self.assertIsNotNone(contract.ir_version)
        
        # Verify deterministic flags claim replay conformance
        self.assertTrue(any(f in contract.deterministic_flags for f in 
                           ['stable_replay', 'stable_eval', 'stable_parse']))


if __name__ == '__main__':
    unittest.main()
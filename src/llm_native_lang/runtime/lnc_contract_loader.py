#!/usr/bin/env python3
"""LNC Contract Loader - Bridges LNC contracts with runtime replay for deterministic execution tracing."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from runtime.interpreter_runtime import InterpreterRuntime
from runtime.replay_harness import TraceCapture, ExecutionTrace, ReplayValidator


def parse_yaml_lite(content):
    """Lightweight YAML parser for LNC structure validation."""
    data = {}
    lines = content.split('\n')
    
    def get_indent(line):
        if not line.strip():
            return -1
        return len(line) - len(line.lstrip())
    
    def parse_value(val_str):
        val = val_str.strip()
        if val.startswith('"') and val.endswith('"') and len(val) > 1:
            return val[1:-1]
        if val.startswith("'") and val.endswith("'") and len(val) > 1:
            return val[1:-1]
        if val.lower() == 'true':
            return True
        if val.lower() == 'false':
            return False
        if val.lower() == 'null' or val == '':
            return None
        if re.match(r'^-?\d+$', val):
            return int(val)
        return val
    
    def parse_block(start_idx, base_indent):
        result = {}
        current_list = None
        current_list_key = None
        i = start_idx
        
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            
            if not stripped or stripped.startswith('#'):
                i += 1
                continue
            
            indent = get_indent(line)
            
            if indent < base_indent:
                if current_list is not None and current_list_key:
                    result[current_list_key] = current_list
                return result, i
            
            if indent == base_indent and stripped.startswith('- '):
                item_text = stripped[2:].strip()
                
                if ': ' in item_text or item_text.endswith(':'):
                    if current_list is None:
                        current_list = []
                    
                    if ': ' in item_text:
                        key, val = item_text.split(': ', 1)
                        key = key.strip()
                        val = val.strip()
                        
                        if val == '' or val.startswith('#'):
                            i += 1
                            nested, i = parse_block(i, indent + 2)
                            current_list.append({key: nested if nested else None})
                        else:
                            current_list.append({key: parse_value(val)})
                    else:
                        key = item_text.rstrip(':').strip()
                        i += 1
                        nested, i = parse_block(i, indent + 2)
                        current_list.append({key: nested})
                    continue
                else:
                    if current_list is None:
                        current_list = []
                    current_list.append(parse_value(item_text))
                i += 1
                continue
            
            if indent == base_indent and (': ' in stripped or stripped.endswith(':')):
                if current_list is not None and current_list_key:
                    result[current_list_key] = current_list
                    current_list = None
                    current_list_key = None
                
                if ': ' in stripped:
                    key, val = stripped.split(': ', 1)
                    key = key.rstrip(':').strip()
                    val = val.strip()
                    
                    if ' #' in val:
                        val = val.split(' #')[0].strip()
                    
                    if val == '' or val.startswith('#'):
                        result[key] = None
                    elif val == '[]':
                        result[key] = []
                    elif val == '{}':
                        result[key] = {}
                    elif val.startswith('[') and val.endswith(']'):
                        items = []
                        inner = val[1:-1]
                        if inner.strip():
                            for item in inner.split(','):
                                items.append(parse_value(item))
                        result[key] = items
                    elif val in ['|', '>']:
                        i += 1
                        lines_content = []
                        while i < len(lines):
                            next_line = lines[i]
                            if not next_line.strip():
                                i += 1
                                continue
                            next_indent = get_indent(next_line)
                            if next_indent <= base_indent and lines[i].strip():
                                break
                            lines_content.append(next_line[base_indent + 2:])
                            i += 1
                        result[key] = '\n'.join(lines_content)
                        continue
                    else:
                        result[key] = parse_value(val)
                else:
                    key = stripped.rstrip(':').strip()
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        if next_line.strip() and get_indent(next_line) > base_indent:
                            if next_line.strip().startswith('- '):
                                current_list = []
                                current_list_key = key
                            else:
                                i += 1
                                nested, i = parse_block(i, indent + 2)
                                result[key] = nested
                                continue
                        else:
                            result[key] = {}
                i += 1
                continue
            
            if indent > base_indent:
                i += 1
                continue
            
            i += 1
        
        if current_list is not None and current_list_key:
            result[current_list_key] = current_list
        
        return result, i
    
    result, _ = parse_block(0, 0)
    return result


@dataclass
class LNCContract:
    """Represents a parsed LNC contract."""
    lnc_version: str
    kind: str
    id: str
    module: str
    entry: str
    source_lang: str
    source: str
    ir_version: str
    deterministic_flags: List[str]
    tests: List[str]
    refs: List[str]
    raw: Dict[str, Any] = field(repr=False)

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> 'LNCContract':
        """Parse an LNC file into a contract object."""
        path = Path(path)
        with open(path, 'r') as f:
            content = f.read()
        
        # Parse header line: @lnc X.Y
        lines = content.split('\n')
        header_match = re.match(r'@lnc\s+(\d+\.\d+)', lines[0].strip())
        if not header_match:
            raise ValueError(f"Invalid LNC header in {path}")
        lnc_version = header_match.group(1)
        
        # Parse YAML body (skip header)
        yaml_content = '\n'.join(lines[1:])
        data = parse_yaml_lite(yaml_content)
        
        return cls(
            lnc_version=lnc_version,
            kind=data.get('kind', 'unknown'),
            id=data.get('id', 'unknown'),
            module=data.get('module', ''),
            entry=data.get('entry', 'main'),
            source_lang=data.get('source_lang', 'minilang'),
            source=data.get('source', ''),
            ir_version=data.get('ir_version', 'v1'),
            deterministic_flags=data.get('deterministic_flags', []),
            tests=data.get('tests', []),
            refs=data.get('refs', []),
            raw=data
        )


class LNCContractExecutor:
    """Executes LNC contracts with trace capture for replay conformance."""
    
    def __init__(self, interpreter: Optional[InterpreterRuntime] = None, 
                 trace_capture: Optional[TraceCapture] = None):
        self.interpreter = interpreter or InterpreterRuntime()
        self.trace_capture = trace_capture or TraceCapture()
        self.validator = ReplayValidator()
        self.contracts: Dict[str, LNCContract] = {}
        self.execution_traces: Dict[str, ExecutionTrace] = {}
    
    def load_contract(self, path: Union[str, Path]) -> LNCContract:
        """Load an LNC contract from file."""
        contract = LNCContract.from_file(path)
        self.contracts[contract.id] = contract
        return contract
    
    def load_contracts_from_dir(self, dir_path: Union[str, Path]) -> List[LNCContract]:
        """Load all LNC contracts from a directory."""
        dir_path = Path(dir_path)
        contracts = []
        for lnc_file in dir_path.rglob('*.lnc'):
            try:
                contract = self.load_contract(lnc_file)
                contracts.append(contract)
            except Exception as e:
                print(f"Warning: Failed to load {lnc_file}: {e}")
        return contracts
    
    def execute_contract(self, contract_id: str, capture_trace: bool = True) -> Dict[str, Any]:
        """Execute an LNC contract with optional trace capture."""
        if contract_id not in self.contracts:
            raise ValueError(f"Contract {contract_id} not loaded")
        
        contract = self.contracts[contract_id]
        
        # Start trace capture if enabled
        if capture_trace:
            self.trace_capture.start_capture(
                trace_id=f"lnc-{contract.id}",
                input_args=[contract.source, contract.source_lang]
            )
            self.trace_capture.record_operation('contract_load', {
                'contract_id': contract.id,
                'module': contract.module,
                'entry': contract.entry,
                'source_lang': contract.source_lang
            })
        
        try:
            # Execute the contract source through the interpreter
            result = self._execute_source(contract.source, contract.source_lang)
            
            if capture_trace:
                self.trace_capture.record_output(result)
                self.trace_capture.current_trace.timestamp_end = __import__('time').time()
                self.execution_traces[contract_id] = self.trace_capture.current_trace
            
            return {
                'contract_id': contract_id,
                'success': True,
                'result': result,
                'trace_id': f"lnc-{contract.id}" if capture_trace else None
            }
            
        except Exception as e:
            if capture_trace:
                self.trace_capture.record_exception(e)
                self.trace_capture.current_trace.timestamp_end = __import__('time').time()
                self.execution_traces[contract_id] = self.trace_capture.current_trace
            
            return {
                'contract_id': contract_id,
                'success': False,
                'error': str(e),
                'trace_id': f"lnc-{contract.id}" if capture_trace else None
            }
    
    def _execute_source(self, source: str, source_lang: str) -> Any:
        """Execute source code through the interpreter."""
        if source_lang == 'minilang':
            return self.interpreter.execute(source)
        else:
            raise ValueError(f"Unsupported source language: {source_lang}")
    
    def replay_contract(self, contract_id: str, iterations: int = 3) -> Dict[str, Any]:
        """Replay a contract execution multiple times to verify determinism."""
        if contract_id not in self.contracts:
            raise ValueError(f"Contract {contract_id} not loaded")
        
        contract = self.contracts[contract_id]
        
        # Check if contract claims determinism
        if 'stable_replay' not in contract.deterministic_flags:
            return {
                'contract_id': contract_id,
                'deterministic': None,
                'message': 'Contract does not claim stable_replay flag'
            }
        
        # Execute multiple times
        traces = []
        results = []
        
        for i in range(iterations):
            exec_result = self.execute_contract(contract_id, capture_trace=True)
            results.append(exec_result.get('result'))
            if contract_id in self.execution_traces:
                traces.append(self.execution_traces[contract_id])
        
        # Validate determinism
        is_deterministic = self._validate_results_consistency(results)
        
        return {
            'contract_id': contract_id,
            'deterministic': is_deterministic,
            'iterations': iterations,
            'results': results,
            'traces': [t.trace_id for t in traces],
            'flags_matched': all(f in contract.deterministic_flags for f in 
                               ['stable_parse', 'stable_eval', 'stable_replay'])
        }
    
    def _validate_results_consistency(self, results: List[Any]) -> bool:
        """Check if all execution results are consistent."""
        if not results:
            return True
        first = results[0]
        return all(r == first for r in results[1:])
    
    def save_trace(self, contract_id: str, output_path: Union[str, Path]) -> Path:
        """Save execution trace to JSON file."""
        import json
        
        if contract_id not in self.execution_traces:
            raise ValueError(f"No trace found for contract {contract_id}")
        
        output_path = Path(output_path)
        trace = self.execution_traces[contract_id]
        
        with open(output_path, 'w') as f:
            json.dump(trace.to_dict(), f, indent=2)
        
        return output_path


class LNCContractReplayHarness:
    """High-level harness for LNC contract replay conformance testing."""
    
    def __init__(self, interpreter: Optional[InterpreterRuntime] = None):
        self.executor = LNCContractExecutor(interpreter)
        self.results: Dict[str, Dict[str, Any]] = {}
    
    def load_and_test_contract(self, lnc_path: Union[str, Path], 
                               iterations: int = 3) -> Dict[str, Any]:
        """Load an LNC contract and run replay conformance tests."""
        contract = self.executor.load_contract(lnc_path)
        
        # Run replay test
        replay_result = self.executor.replay_contract(contract.id, iterations)
        
        # Store result
        self.results[contract.id] = replay_result
        
        return replay_result
    
    def load_and_test_directory(self, dir_path: Union[str, Path],
                                iterations: int = 3) -> List[Dict[str, Any]]:
        """Load and test all LNC contracts in a directory."""
        contracts = self.executor.load_contracts_from_dir(dir_path)
        results = []
        
        for contract in contracts:
            replay_result = self.executor.replay_contract(contract.id, iterations)
            self.results[contract.id] = replay_result
            results.append(replay_result)
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all test results."""
        total = len(self.results)
        deterministic = sum(1 for r in self.results.values() if r.get('deterministic') is True)
        non_deterministic = sum(1 for r in self.results.values() if r.get('deterministic') is False)
        skipped = sum(1 for r in self.results.values() if r.get('deterministic') is None)
        
        return {
            'total_contracts': total,
            'deterministic': deterministic,
            'non_deterministic': non_deterministic,
            'skipped_no_claim': skipped,
            'results': self.results
        }


# Convenience functions for direct use
def load_and_execute_lnc(lnc_path: str) -> Dict[str, Any]:
    """Load and execute a single LNC contract."""
    harness = LNCContractReplayHarness()
    return harness.load_and_test_contract(lnc_path)


def load_and_execute_directory(dir_path: str) -> List[Dict[str, Any]]:
    """Load and execute all LNC contracts in a directory."""
    harness = LNCContractReplayHarness()
    return harness.load_and_test_directory(dir_path)
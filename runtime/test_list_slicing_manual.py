"""Manual tests for list slicing operator [start:end:step]."""

import sys
sys.path.insert(0, '/home/node/.openclaw/workspace/llm-native-lang')

from runtime.ast_contract import AST_SCHEMA, validate_ast
from runtime.interpreter_runtime import eval_expr, EvalError


def make_slice_node(target_items, start=None, end=None, step=None):
    """Helper to create a slice AST node."""
    node = {
        "kind": "slice",
        "span": {"start": 0, "end": 10},
        "target": {"kind": "list", "span": {"start": 0, "end": 10}, "items": target_items},
        "start": start,
        "end": end,
        "step": step,
    }
    return node


def make_number(value):
    return {"kind": "number", "span": {"start": 0, "end": 1}, "value": value}


def run_tests():
    passed = 0
    failed = 0
    
    print("=" * 60)
    print("LIST SLICING TEST SUITE")
    print("=" * 60)
    
    # Test 1: Basic slice with positive indices
    print("\n[Test 1] Basic slice [1:3]...")
    try:
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    make_number(10),
                    make_number(20),
                    make_number(30),
                    make_number(40),
                ],
            },
            "start": make_number(1),
            "end": make_number(3),
            "step": None,
        }
        result = eval_expr(node)
        assert result == [20, 30], f"Expected [20, 30], got {result}"
        print("  PASSED")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1
    
    # Test 2: Negative start index [-2:]
    print("\n[Test 2] Negative start [-2:]...")
    try:
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    make_number(1),
                    make_number(2),
                    make_number(3),
                    make_number(4),
                ],
            },
            "start": make_number(-2),
            "end": None,
            "step": None,
        }
        result = eval_expr(node)
        assert result == [3, 4], f"Expected [3, 4], got {result}"
        print("  PASSED")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1
    
    # Test 3: Negative end index [:-1]
    print("\n[Test 3] Negative end [:-1]...")
    try:
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    make_number(1),
                    make_number(2),
                    make_number(3),
                ],
            },
            "start": None,
            "end": make_number(-1),
            "step": None,
        }
        result = eval_expr(node)
        assert result == [1, 2], f"Expected [1, 2], got {result}"
        print("  PASSED")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1
    
    # Test 4: With step [::2]
    print("\n[Test 4] With step [::2]...")
    try:
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    make_number(0),
                    make_number(1),
                    make_number(2),
                    make_number(3),
                    make_number(4),
                ],
            },
            "start": None,
            "end": None,
            "step": make_number(2),
        }
        result = eval_expr(node)
        assert result == [0, 2, 4], f"Expected [0, 2, 4], got {result}"
        print("  PASSED")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1
    
    # Test 5: Reverse with negative step [::-1]
    print("\n[Test 5] Reverse with step [::-1]...")
    try:
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    make_number(1),
                    make_number(2),
                    make_number(3),
                ],
            },
            "start": None,
            "end": None,
            "step": make_number(-1),
        }
        result = eval_expr(node)
        assert result == [3, 2, 1], f"Expected [3, 2, 1], got {result}"
        print("  PASSED")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1
    
    # Test 6: Empty slice [2:2]
    print("\n[Test 6] Empty slice [2:2]...")
    try:
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    make_number(1),
                    make_number(2),
                    make_number(3),
                ],
            },
            "start": make_number(2),
            "end": make_number(2),
            "step": None,
        }
        result = eval_expr(node)
        assert result == [], f"Expected [], got {result}"
        print("  PASSED")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1
    
    # Test 7: Out of bounds clamping
    print("\n[Test 7] Out of bounds clamping...")
    try:
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    make_number(1),
                    make_number(2),
                ],
            },
            "start": make_number(0),
            "end": make_number(100),
            "step": None,
        }
        result = eval_expr(node)
        assert result == [1, 2], f"Expected [1, 2], got {result}"
        print("  PASSED")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1
    
    # Test 8: Zero step error
    print("\n[Test 8] Zero step error...")
    try:
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    make_number(1),
                    make_number(2),
                ],
            },
            "start": None,
            "end": None,
            "step": make_number(0),
        }
        eval_expr(node)
        print(f"  FAILED: Expected EvalError for zero step")
        failed += 1
    except EvalError as e:
        if "step" in str(e).lower() or "zero" in str(e).lower():
            print("  PASSED")
            passed += 1
        else:
            print(f"  FAILED: Wrong error message: {e}")
            failed += 1
    
    # Test 9: Non-list target error
    print("\n[Test 9] Non-list target error...")
    try:
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {"kind": "number", "span": {"start": 0, "end": 1}, "value": 42},
            "start": make_number(0),
            "end": make_number(1),
            "step": None,
        }
        eval_expr(node)
        print(f"  FAILED: Expected EvalError for non-list target")
        failed += 1
    except EvalError as e:
        if "list" in str(e).lower():
            print("  PASSED")
            passed += 1
        else:
            print(f"  FAILED: Wrong error message: {e}")
            failed += 1
    
    # Test 10: Non-int bound error
    print("\n[Test 10] Non-int bound error...")
    try:
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [make_number(1)],
            },
            "start": {"kind": "string", "span": {"start": 0, "end": 1}, "value": "hello"},
            "end": None,
            "step": None,
        }
        eval_expr(node)
        print(f"  FAILED: Expected EvalError for non-int bound")
        failed += 1
    except EvalError as e:
        if "int" in str(e).lower():
            print("  PASSED")
            passed += 1
        else:
            print(f"  FAILED: Wrong error message: {e}")
            failed += 1
    
    # Test 11: Full copy [:]
    print("\n[Test 11] Full copy [:]...")
    try:
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    make_number(1),
                    make_number(2),
                ],
            },
            "start": None,
            "end": None,
            "step": None,
        }
        result = eval_expr(node)
        assert result == [1, 2], f"Expected [1, 2], got {result}"
        print("  PASSED")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1
    
    # Test 12: Both negative indices [-3:-1]
    print("\n[Test 12] Both negative indices [-3:-1]...")
    try:
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    make_number(0),
                    make_number(1),
                    make_number(2),
                    make_number(3),
                    make_number(4),
                ],
            },
            "start": make_number(-3),
            "end": make_number(-1),
            "step": None,
        }
        result = eval_expr(node)
        assert result == [2, 3], f"Expected [2, 3], got {result}"
        print("  PASSED")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1
    
    # Test 13: Start > end with positive step (empty)
    print("\n[Test 13] Start > end with positive step (empty)...")
    try:
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    make_number(0),
                    make_number(1),
                    make_number(2),
                    make_number(3),
                ],
            },
            "start": make_number(3),
            "end": make_number(1),
            "step": None,
        }
        result = eval_expr(node)
        assert result == [], f"Expected [], got {result}"
        print("  PASSED")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)

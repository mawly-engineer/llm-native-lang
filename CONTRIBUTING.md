# Contributing to llm-native-lang

Thanks for helping improve deterministic language/runtime contracts.

## Ground rules

- Keep scope deterministic and machine-checkable.
- Prefer small, single-purpose PRs.
- Align changes with `docs/SPEC.md`, `docs/RUNTIME.md`, and `docs/RUNTIME_CONTRACT.md`.
- Keep backlog/state docs consistent when cycle-planned work is completed.

## Development setup

```bash
python3 -m unittest runtime.test_grammar_contract runtime.test_ast_contract runtime.test_type_contract runtime.test_interpreter_runtime runtime.test_runtime_stub
```

## Issue workflow

- Use the issue template.
- Tie the request to a concrete contract gap or reproducibility need.
- Provide objective acceptance criteria and target tests.

## Pull request workflow

- Use the PR template checklist.
- Reference backlog item id and next-step id when applicable.
- Include focused test command(s) and results.

## Definition of Done (DoD) gates

A PR is done only when all applicable gates pass:

1. **Spec/contract alignment gate**
   - Any grammar/runtime/invariant behavior changes are reflected in docs contracts.
2. **Validation gate**
   - Focused tests covering the change are added/updated and passing.
3. **Benchmark/repro gate (when practical-value touched)**
   - Include reproducibility evidence or benchmark delta relevant to the changed behavior.
4. **Backlog/state gate (when coordinator docs touched)**
   - `LANGUAGE_BACKLOG`, `NEXT_STEPS`, and `CYCLE_LOG` reflect the performed cycle outcome.
5. **Determinism gate**
   - No added nondeterministic ordering, unstable serialization, or time-dependent assertions.

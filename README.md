# llm-native-lang

Deterministic mini-language + deterministic runtime/replay prototype.

## Core idea

- `.lnd` = documentation/contracts (source of truth)
- `.lnc` = executable/code artifacts
- deterministic behavior over convenience

## Minimal project structure

- `docs/LND_FORMAT.lnd` — doc format spec
- `docs/LNC_PROFILE.lnd` — code artifact profile spec
- `docs/MIGRATION_TO_LND_LNC.lnd` — migration status/plan
- `docs/*.(lnd)` — contracts, backlog, state, cycle log
- `runtime/` — parser, AST/type/interpreter/runtime + tests
- `runtime/examples/*.lnc` — canonical executable artifacts
- `scripts/lnd_validate.py` — validate `.lnd`
- `scripts/lnc_validate.py` — validate `.lnc`

## Quickstart

```bash
python3 -m unittest runtime.test_grammar_contract runtime.test_ast_contract runtime.test_type_contract runtime.test_interpreter_runtime runtime.test_runtime_stub runtime.test_format_validators
python3 scripts/lnd_validate.py docs
python3 scripts/lnc_validate.py runtime
```

## Project policy

- Keep the repo small.
- Add new files only when they are source-of-truth or executable artifacts.
- Prefer updating existing `.lnd` contracts over creating new docs.
- Legacy files are moved to `archive/legacy/`.

# llm-native-lang

Deterministic language/runtime contracts for LLM-native execution and replay.

## What this is

- A compact language contract surface (`.lnd`) for syntax, types, and runtime behavior.
- A deterministic runtime with replay-oriented semantics.
- Validator-backed formats for contracts (`.lnd`) and runtime examples (`.lnc`).

## What this is not

- A general-purpose production language.
- A probabilistic execution engine.
- A replacement for full compiler toolchains.

## Quickstart

```bash
git clone https://github.com/mawly-engineer/llm-native-lang.git
cd llm-native-lang
python3 scripts/lnd_validate.py evolution
python3 scripts/lnd_validate.py contracts
python3 scripts/lnc_validate.py runtime
```

## Determinism guarantees

- Stable parse/type/runtime contracts are source-of-truth in `contracts/` and `formats/`.
- Validation tooling enforces machine-readable structure for `.lnd` and `.lnc` files.
- Runtime tests assert replay and determinism invariants.

## Release notes

See `.github/release-notes/` for versioned release-note templates.

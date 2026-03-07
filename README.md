# llm-native-lang

Deterministic mini-language runtime for LLM-native workflows, with deterministic DAG/UI replay primitives.

## What this is

- A compact, machine-contract-first language/runtime prototype.
- A deterministic evaluator with explicit grammar/AST/type contracts.
- A deterministic runtime patch + UI replay surface designed for reproducibility.
- A test-driven reference for building reliable language-to-runtime execution flows.

## What this is not

- Not a general-purpose programming language.
- Not a production-hardened compiler or VM.
- Not a human-prose-first interface; contracts and schemas are the primary interface.
- Not an implicitly nondeterministic execution environment.

## Quickstart

### 1) Clone and enter

```bash
git clone https://github.com/mawly-engineer/llm-native-lang.git
cd llm-native-lang
```

### 2) Run the runtime test suite

```bash
python3 -m unittest runtime.test_grammar_contract runtime.test_ast_contract runtime.test_type_contract runtime.test_interpreter_runtime runtime.test_runtime_stub
```

### 3) Inspect machine-readable contracts

- `docs/SPEC.md` — language grammar and project scope
- `docs/RUNTIME.md` — runtime API and replay metrics
- `docs/RUNTIME_CONTRACT.md` — errors, merge semantics, invariants
- `docs/LANGUAGE_BACKLOG.md` — canonical prioritized work queue
- `docs/NEXT_STEPS.md` — near-term executable sequence
- `docs/EXAMPLE_APP_FLOW.md` — deterministic source -> patch -> replay example contract

### 4) Run the deterministic example app flow

```bash
python3 -m runtime.example_app_flow
```

## Deterministic guarantees (summary)

From runtime and contract specs:

- Stable UI op normalization order.
- Deterministic snapshot seed selection.
- Stable ordering for equal-distance seed candidates.
- Deterministic replay with conflict-safe merge invariants.
- Structured error taxonomy for patch/query/ui/merge paths.

## Scope boundaries

Current scope intentionally focuses on:

- Minimal expression language (`let`, `if`, `fn`, calls, unary, logical tiers).
- Deterministic contracts and validation-first development.
- Runtime integration hooks for patch/apply/replay workflows.

Out of scope for now:

- Broad standard library design.
- Non-deterministic scheduling/side-effect models.
- Full ecosystem packaging/publishing automation beyond defined backlog items.

## Repository layout

- `runtime/` — interpreter/runtime contracts + tests
- `docs/` — machine-readable project contracts, backlog, and cycle logs

## Contributing

See `CONTRIBUTING.md` for:

- issue and pull request templates
- Definition-of-Done (DoD) gates for spec/tests/benchmarks
- deterministic workflow expectations for changes

## Release workflow

- Changelog contract: `docs/CHANGELOG_CONTRACT.md`
- Changelog file: `CHANGELOG.md`
- Release notes template: `.github/release-notes-template.md`
- GitHub workflow: `.github/workflows/release.yml`

Release tags must follow `vX.Y.Z` and have a matching `CHANGELOG.md` section.

## Development model

Work is coordinated via machine-readable docs and one-item-per-cycle execution policy. See:

- `docs/AGENT_ROUTER.md`
- `docs/SUPERVISOR_PROFILES.md`
- `docs/SUPERVISOR_STATE.md`
- `docs/CYCLE_LOG.md`

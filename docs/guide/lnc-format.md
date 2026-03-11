# LNC Format Specification

LNC (LLM-Native Contract) is a YAML-based format for defining executable contracts and tasks.

## Format Version

Current version: **0.2**

## Header

Every LNC file must start with a version header:

```yaml
@lnc 0.2
```

## Core Fields

| Field | Required | Description |
|-------|----------|-------------|
| `kind` | Yes | Type of contract (`task`, `decision`, `note`, `code_unit`) |
| `id` | Yes | Unique identifier for this contract |
| `status` | Yes | Current status |

## Task Kinds

### Task

Tasks track work items with acceptance criteria:

```yaml
@lnc 0.2
kind: task
id: TASK-EXAMPLE-001
status: open
priority: p1

objective: |
  Implement feature X with full test coverage.

acceptance_criteria:
  - Unit tests pass
  - Integration tests pass
  - Documentation updated
```

Task status values:
- `open` - Not started
- `in_progress` - Currently being worked on
- `done` - Completed
- `cancelled` - Cancelled

Task priority values:
- `p0` - Critical
- `p1` - High
- `p2` - Medium
- `p3` - Low

### Decision

Decisions record choices made during development:

```yaml
@lnc 0.2
kind: decision
id: DECISION-001
status: decided

title: Use YAML for LNC format

context: |
  We needed a human-readable, LLM-friendly format.

options:
  - id: opt1
    description: Use JSON
  - id: opt2
    description: Use YAML
  - id: opt3
    description: Use TOML

selected: opt2

rationale: |
  YAML provides better readability for multi-line strings
  and supports comments, unlike JSON.
```

### Note

Notes capture information:

```yaml
@lnc 0.2
kind: note
id: NOTE-001
status: active
tags: [architecture, design]

content: |
  Design decision: Keep contracts simple and focused.
  Each contract should represent one logical unit.
```

### Code Unit

Code units define executable code blocks:

```yaml
@lnc 0.2
kind: code_unit
id: CODE-001
status: active
language: python

inputs:
  - name: data
    type: dict

outputs:
  - name: result
    type: dict

code: |
  def process(data):
      return {"processed": True, "data": data}
  result = process(data)
```

## Validation

Validate LNC files:

```bash
lnc-validate path/to/file.lnc
lnc-validate runtime/examples/  # Validate all .lnc files in directory
```

## Validation Rules

1. **Version header must be first line** - `@lnc 0.2`
2. **Required fields must be present** - `kind`, `id`, `status`
3. **Task-specific validation**:
   - Status must be: `open`, `in_progress`, `done`, `cancelled`
   - Priority must be: `p0`, `p1`, `p2`, `p3`
4. **Decision-specific validation**:
   - Options must have at least 2 items
   - Selected must match one option ID
5. **Valid YAML syntax** - No tabs, proper indentation

## Execution

Execute LNC contracts:

```bash
kairo execute runtime/examples/sample.lnc
```

This will:
1. Load and validate the contract
2. Execute the contract logic
3. Capture execution trace
4. Report results

## File Organization

```
project/
├── tasks/          # Task contracts
├── decisions/      # Decision records
├── notes/          # Information notes
└── code/           # Code units
```

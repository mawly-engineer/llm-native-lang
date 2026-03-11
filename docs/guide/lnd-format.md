# LND Format Specification

LND (LLM-Native Declaration) is a YAML-based format for declaring structured data meant for LLM consumption.

## Format Version

Current version: **0.2**

## Header

Every LND file must start with a version header:

```yaml
@lnd 0.2
```

## Core Fields

| Field | Required | Description |
|-------|----------|-------------|
| `kind` | Yes | Type of declaration (e.g., `agent_profile`, `task`, `run_profile`) |
| `id` | Yes | Unique identifier for this declaration |
| `status` | Yes | Current status (e.g., `active`, `done`, `open`) |
| `updated_at_utc` | Recommended | ISO-8601 timestamp of last update |
| `purpose` | Recommended | Human-readable description |

## Example: Agent Profile

```yaml
@lnd 0.2
kind: agent_profile
id: AGENT-COORDINATOR-001
status: active
updated_at_utc: 2026-03-11T12:00:00Z
purpose: Canonical rule set for the coordinator agent

workspace_root: /home/user/workspace

hard_rules:
  - use_absolute_paths_only
  - read_before_edit_or_write
  - one_meaningful_unit_per_cycle

authoritative_inputs:
  - evolution/PROJECT_ENTRY.lnd
  - evolution/CURRENT_STATE.lnd
```

## Example: Task Declaration

```yaml
@lnd 0.2
kind: task
id: TASK-001
status: open
priority: p1

objective: |
  Implement the core language features.

acceptance_criteria:
  - Parser handles all base types
  - Validator reports clear errors
  - Documentation is complete
```

## Validation

Use the built-in validator:

```bash
lnd-validate path/to/file.lnd
lnd-validate evolution/  # Validate all .lnd files in directory
```

## Validation Rules

1. **Version header must be first line** - `@lnd 0.2`
2. **Required fields must be present** - `kind`, `id`, `status`
3. **IDs must be unique** - No duplicate IDs across files
4. **Valid YAML syntax** - No tabs, proper indentation
5. **Status values** - Must be valid for the kind

## Common Kinds

| Kind | Purpose |
|------|---------|
| `agent_profile` | Define agent behavior and rules |
| `task` | Track work items |
| `run_profile` | Define execution parameters |
| `cron_protocol` | Define scheduled execution |
| `current_state` | Track execution state |
| `work_items` | Backlog and completed work |

## Multi-line Strings

Use the `|` pipe operator for multi-line strings:

```yaml
description: |
  This is a multi-line string.
  It preserves line breaks.
  Indentation is relative to the first line.
```

## Lists

YAML lists are supported:

```yaml
hard_rules:
  - rule_one
  - rule_two
  - rule_three

nested:
  - name: item_one
    value: 42
  - name: item_two
    value: 99
```

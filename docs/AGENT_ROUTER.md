# AGENT_ROUTER.md

Coordinator-controlled routing file.

## Active Agent Slots
- active_primary: interpreter-runtime
- active_secondary: validation

## Priority Order
1. integration (if red/discrepancy in E2E)
2. validation (if failing tests/contracts)
3. interpreter-runtime
4. language-core

## Override Flags
- force_agent: none
- hold_agents: none

## Notes
- Non-selected agents should SKIP with short status.
- Selected agents should execute one highest-priority backlog item in their bucket.

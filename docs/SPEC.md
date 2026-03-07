version: 1
document: SPEC
project: llm-native-lang
objective: Deterministic language runtime plus deterministic DAG-based UI replay.

core_entities:
  - ProgramGraph
  - Revision
  - UITimelineEvent
  - UISnapshot

primary_outputs:
  - machine_readable_schema_documents
  - test_verified_runtime_behavior
  - append_only_cycle_execution_records

language_minimal_grammar:
  version: 1.0.0
  start: expr
  required_nonterminals:
    - expr
    - let
    - if
    - fn
    - call
    - atom
  productions:
    - "expr -> let | if | fn | call | atom"
    - "let -> 'let' IDENT '=' expr 'in' expr"
    - "if -> 'if' expr 'then' expr 'else' expr"
    - "fn -> 'fn' '(' params? ')' '=>' expr"
    - "call -> IDENT '(' args? ')'"
    - "atom -> IDENT | NUMBER | '(' expr ')'"

non_goals:
  - human_first_prose_as_primary_system_interface
  - ambiguous_process_narration

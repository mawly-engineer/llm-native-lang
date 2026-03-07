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
    - logical_or
    - logical_and
    - call
    - unary
    - atom
    - params
    - args
  productions:
    - "expr -> let | if | fn | logical_or"
    - "let -> 'let' IDENT '=' expr 'in' expr"
    - "if -> 'if' expr 'then' expr 'else' expr"
    - "fn -> 'fn' '(' params? ')' '=>' expr"
    - "logical_or -> logical_and ('or' logical_and)*"
    - "logical_and -> unary ('and' unary)*"
    - "call -> IDENT '(' args? ')'"
    - "unary -> '-' unary | call | atom"
    - "atom -> IDENT | NUMBER | '(' expr ')'"
    - "params -> IDENT (',' IDENT)*"
    - "args -> expr (',' expr)*"

non_goals:
  - human_first_prose_as_primary_system_interface
  - ambiguous_process_narration

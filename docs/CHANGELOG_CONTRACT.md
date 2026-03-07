version: 1
document: CHANGELOG_CONTRACT
purpose: Machine-readable contract for deterministic release versioning and changelog structure.

versioning:
  scheme: semver
  tag_pattern: "^v[0-9]+\\.[0-9]+\\.[0-9]+$"
  initial_version: v0.1.0

changelog_file:
  path: CHANGELOG.md
  required_sections:
    - heading_h1
    - unreleased
    - released_versions_desc

released_version_entry_contract:
  heading_pattern: "^## \[vX.Y.Z\] - YYYY-MM-DD$"
  required_subsections:
    - Added
    - Changed
    - Fixed
    - Validation

release_notes_template:
  path: .github/release-notes-template.md
  placeholders:
    - "{{VERSION}}"
    - "{{DATE_UTC}}"

release_workflow:
  path: .github/workflows/release.yml
  triggers:
    - push_tag_semver
    - manual_dispatch
  hard_gates:
    - deterministic_test_suite_passes
    - changelog_contains_version_section
  outputs:
    - github_release_for_tag

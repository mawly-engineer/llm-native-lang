# Installation

## Requirements

- Python 3.10 or higher
- pip (included with Python)

## Install from Source

```bash
git clone https://github.com/luis/mawly/llm-native-lang.git
cd llm-native-lang
pip install -e .
```

## Install for Development

For development with all optional dependencies:

```bash
pip install -e ".[dev]"
```

This includes:
- Test dependencies (pytest, pytest-cov)
- Documentation tools (mkdocs, mkdocstrings)
- Development utilities (black, ruff, mypy)

## Verify Installation

```bash
# Check version
python -c "from llm_native_lang import __version__; print(__version__)"

# Check CLI tools
kairo --help
lnd-validate --help
lnc-validate --help
```

## Available Commands

After installation, the following commands are available:

| Command | Description |
|---------|-------------|
| `kairo` | Unified CLI for validation and execution |
| `lnd-validate` | Validate LND format files |
| `lnc-validate` | Validate LNC contract files |

## Python Package Structure

```
llm_native_lang/
├── __init__.py          # Package version and metadata
├── runtime/             # Runtime execution modules
├── validators/          # LND and LNC validators
└── cli/                # Command-line interface
```

## Troubleshooting

### Command not found

If CLI commands are not found, ensure your Python scripts directory is on PATH:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
```

### Import errors

If imports fail after installation:

```bash
# Reinstall in editable mode
pip uninstall llm-native-lang
pip install -e .
```

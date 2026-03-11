# Contributing

Thank you for your interest in contributing to LLM-Native Lang!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/luis/mawly/llm-native-lang.git
cd llm-native-lang
```

2. Install in development mode:
```bash
pip install -e ".[dev]"
```

3. Install pre-commit hooks:
```bash
pre-commit install
```

## Project Structure

```
llm-native-lang/
├── evolution/          # Evolution profiles and state
├── formats/            # Format specifications
├── runtime/            # Python runtime
├── scripts/            # Utility scripts
├── src/                # Package source
├── docs/               # Documentation
└── tests/              # Test suite
```

## Making Changes

1. Create a new branch:
```bash
git checkout -b feature/my-feature
```

2. Make your changes

3. Run validation:
```bash
python validate_incremental.py
python scripts/detect_changes.py --mark
```

4. Run tests:
```bash
pytest
```

5. Commit your changes:
```bash
git add .
git commit -m "feat: Description of changes"
```

## Code Style

- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for public functions
- Keep functions focused and small

## Documentation

- Update relevant docs in `docs/`
- Follow the existing structure
- Use clear, concise language
- Include code examples

## Submitting Changes

1. Push your branch:
```bash
git push origin feature/my-feature
```

2. Create a Pull Request

3. Ensure CI passes

## Questions?

Open an issue for questions or discussion.

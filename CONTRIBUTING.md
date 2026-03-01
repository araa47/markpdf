# Contributing

```bash
uv sync --all-extras --dev
```

Before submitting a PR, make sure tests and pre-commit hooks pass:

```bash
uv run pytest
pre-commit run --all-files
```

That's it. Keep changes focused and include tests for new features.

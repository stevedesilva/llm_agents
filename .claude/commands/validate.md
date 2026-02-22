Validate the build by running lint and tests. Both must pass with zero errors.

```bash
uv run ruff check . && uv run pytest -q
```

If lint fails, fix the issues and re-run. If tests fail, investigate and fix the failures. Report the final result.

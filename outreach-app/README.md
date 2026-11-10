# Run the portable app

Use the top-level README. From the repository's top folder, run these commands in macOS Terminal or Windows PowerShell:

```text
uv sync --locked
uv run streamlit run streamlit_app.py
```

This prepares and uses the bundled sample with `config.cloud.toml`, without a sibling dataset directory. The original `config.toml` is retained for advanced sample/full workflows using an external dataset. It is not the public app's configuration.

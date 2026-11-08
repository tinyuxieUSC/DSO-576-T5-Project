"""Portable sample deployment; no sibling data repository is required."""
from pathlib import Path
import runpy
import sys
import streamlit as st

APP = Path(__file__).resolve().parent / "outreach-app"
sys.path.insert(0, str(APP))


@st.cache_resource(show_spinner="Preparing the demonstration sample…")
def prepare_demo(source_signature):
    from outreach.setup import load_config
    from outreach.prepare import prepare_data
    return prepare_data(load_config(APP / "config.cloud.toml", "sample"))


from outreach.setup import load_config
config = load_config(APP / "config.cloud.toml", "sample")
# Hosts can refresh source-file timestamps on any repository update. Include those
# facts in the resource key so a reused process cannot retain an invalid cache.
watched = [config.path, APP / "outreach/data_rules.py", *config.inputs()]
secret = config.local_path('secret_file')
if secret.exists():
    watched.append(secret)
signature = tuple((str(p), p.stat().st_size, p.stat().st_mtime_ns) for p in watched)
prepare_demo(signature)
sys.argv = [str(APP / "app.py"), "--config", str(APP / "config.cloud.toml"), "--mode", "sample"]
runpy.run_path(str(APP / "app.py"), run_name="__main__")

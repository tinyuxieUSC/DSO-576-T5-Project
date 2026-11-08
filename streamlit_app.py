"""Portable sample deployment; no sibling data repository is required."""
from pathlib import Path
import runpy
import sys
import streamlit as st

APP = Path(__file__).resolve().parent / "outreach-app"
sys.path.insert(0, str(APP))


@st.cache_resource(show_spinner="Preparing the demonstration sample…")
def prepare_demo():
    from outreach.setup import load_config
    from outreach.prepare import prepare_data
    return prepare_data(load_config(APP / "config.cloud.toml", "sample"))


prepare_demo()
sys.argv = [str(APP / "app.py"), "--config", str(APP / "config.cloud.toml"), "--mode", "sample"]
runpy.run_path(str(APP / "app.py"), run_name="__main__")

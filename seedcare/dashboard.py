"""Streamlit ダッシュボード。

Usage:
    streamlit run seedcare/dashboard.py
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

from seedcare import db

DB_PATH = Path(os.environ.get("DB_PATH", "data/seedcare.db"))
db.setup(DB_PATH)

st.set_page_config(page_title="SeedCare Monitor", layout="wide")
st_autorefresh(interval=30_000, key="auto_refresh")

st.title("SeedCare Monitor")


def load_data(days: int) -> pd.DataFrame:
    since = datetime.now() - timedelta(days=days)
    rows = db.fetch_range(DB_PATH, since)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(
        rows,
        columns=[
            "dateTime",
            "temperature0",
            "temperature1",
            "moisture0",
            "moisture1",
            "relay0",
            "relay1",
        ],
    )
    df["dateTime"] = pd.to_datetime(df["dateTime"])
    return df


def make_chart(df: pd.DataFrame, title: str) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=df["dateTime"], y=df["temperature0"], name="Temp 0", line=dict(color="#EF553B")),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=df["dateTime"], y=df["temperature1"], name="Temp 1", line=dict(color="#FF7F0E")),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=df["dateTime"], y=df["moisture0"], name="Moisture 0", line=dict(color="#636EFA")),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(x=df["dateTime"], y=df["moisture1"], name="Moisture 1", line=dict(color="#00CC96")),
        secondary_y=True,
    )
    fig.update_layout(title=title, hovermode="x unified", height=450)
    fig.update_yaxes(title_text="Temperature (\u2103)", secondary_y=False)
    fig.update_yaxes(title_text="Moisture (%)", secondary_y=True)
    return fig


# サマリーカード
latest = db.fetch_latest(DB_PATH) if DB_PATH.exists() else None
if latest:
    cols = st.columns(4)
    labels = ["Temp 0", "Temp 1", "Moisture 0", "Moisture 1"]
    units = ["\u2103", "\u2103", "%", "%"]
    for i, col in enumerate(cols):
        col.metric(labels[i], f"{latest[i + 1]:.1f}{units[i]}")

# タブ
tab_day, tab_week = st.tabs(["1日表示", "1週間表示"])

with tab_day:
    df = load_data(1)
    if df.empty:
        st.info("直近1日のデータがありません")
    else:
        st.plotly_chart(make_chart(df, "過去24時間"), use_container_width=True)

with tab_week:
    df = load_data(7)
    if df.empty:
        st.info("直近1週間のデータがありません")
    else:
        st.plotly_chart(make_chart(df, "過去1週間"), use_container_width=True)

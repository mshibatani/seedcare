"""Flask ダッシュボード。

Usage:
    python seedcare/dashboard.py
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from seedcare import db

app = Flask(__name__)

DB_PATH = Path(os.environ.get("DB_PATH", "data/seedcare.db"))
db.setup(DB_PATH)


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/latest")
def api_latest():
    if not DB_PATH.exists():
        return jsonify(None)
    latest = db.fetch_latest(DB_PATH)
    if not latest:
        return jsonify(None)
    return jsonify({
        "dateTime": str(latest[0]),
        "temperature0": latest[1],
        "temperature1": latest[2],
        "moisture0": latest[3],
        "moisture1": latest[4],
        "relay0": latest[5],
        "relay1": latest[6],
    })


@app.route("/api/data")
def api_data():
    days = request.args.get("days", 1, type=int)
    since = datetime.now() - timedelta(days=days)

    if days >= 30:
        rows = db.fetch_range_downsampled(DB_PATH, since, 900)  # 15min
    elif days >= 7:
        rows = db.fetch_range_downsampled(DB_PATH, since, 300)  # 5min
    else:
        rows = db.fetch_range(DB_PATH, since)

    result = {"dateTime": [], "temperature0": [], "temperature1": [],
              "moisture0": [], "moisture1": []}

    for row in rows:
        result["dateTime"].append(str(row[0]))
        result["temperature0"].append(row[1])
        result["temperature1"].append(row[2])
        result["moisture0"].append(row[3])
        result["moisture1"].append(row[4])

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501)

# SeedCare Monitor

ESP32 温湿度データを MQTT で収集し、SQLite に記録、Streamlit で可視化するシステム。

## 技術スタック
- Python 3.11+, paho-mqtt <2.0, Streamlit, Plotly, SQLite (WAL)
- パッケージ管理: uv + hatchling
- デプロイ先: Raspberry Pi 4B (`/opt/app/seedcare/`)

## プロジェクト構造
- `seedcare/` — メインパッケージ（config, db, collector, notifier, dashboard, purge）
- `tests/` — pytest テスト
- `systemd/` — seedcare-dashboard.service
- `docs/` — 設計ドキュメント

## コマンド
```bash
uv run pytest tests/           # テスト実行
uv run python -m seedcare      # コレクタ起動（要 .env）
uv run streamlit run seedcare/dashboard.py  # ダッシュボード起動
```

## 設定
`.env` ファイルで環境変数を管理。`.env.example` を参照。

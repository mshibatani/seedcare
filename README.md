# SeedCare Monitor

ESP32 の温湿度データを MQTT で収集し、サーバー上で記録・可視化するシステム。

```
ESP32 → Mosquitto (Pi:1883) → [collector] → SQLite ← [dashboard] → Browser
                                    ↓
                              [notifier] → Gmail SMTP
```

## セットアップ

### 前提

- Mosquitto MQTT ブローカーが上で稼働
- ESP32 が MQTT でセンサーデータを送信（参考: https://github.com/mshibatani/seedcare-controller/）

### 1. 設定ファイルの作成

```bash
cp .env.example .env
# .env を編集して MQTT、メール通知、閾値を設定
```

主な設定項目:

| 変数 | 説明 | デフォルト |
|------|------|-----------|
| `MQTT_BROKER` | MQTT ブローカーのアドレス | `127.0.0.1` |
| `MQTT_TOPIC` | 購読するトピック | `SHiBA-Plant01/#` |
| `DB_PATH` | SQLite DB のパス | `data/seedcare.db` |
| `LOW_THRESHOLD_TEMPERATURE` | 低温アラート閾値 (℃) | `10.0` |
| `HIGH_THRESHOLD_TEMPERATURE` | 高温アラート閾値 (℃) | `35.0` |
| `RETENTION_DAYS` | データ保持日数 | `120` |

### 2. Pi へのデプロイ（リモート開発スクリプトを別途準備。このレポジトリには含まない）

```bash
# リポジトリルートから
cd remote_raspi/
./deploy.sh ../projects/seedcare raspi.local --restart
```

### 3. systemd サービスの登録

**コレクター**（`app@.service` テンプレートが Pi に必要）:

```bash
ssh pi@raspi.local "sudo systemctl enable --now app@seedcare"
```

**ダッシュボード**:

```bash
scp systemd/seedcare-dashboard.service pi@raspi.local:/tmp/
ssh pi@raspi.local "\
  sudo mv /tmp/seedcare-dashboard.service /etc/systemd/system/ && \
  sudo systemctl daemon-reload && \
  sudo systemctl enable --now seedcare-dashboard"
```

### 4. 動作確認

```bash
# サービスの状態確認
ssh pi@raspi.local "systemctl status app@seedcare seedcare-dashboard"

# ダッシュボードにアクセス
open http://raspi.local:8501
```

## ローカル開発

```bash
uv run pytest tests/           # テスト実行
uv run python -m seedcare      # コレクタ起動（要 .env）
uv run streamlit run seedcare/dashboard.py  # ダッシュボード起動
```

## Pi 環境の補足

Pi (Raspbian Bullseye) ではシステム Python 3.9 を使用。`--system-site-packages` で venv を作成し、numpy/pandas は apt からインストールしている。詳細は [docs/known-issues.md](docs/known-issues.md) を参照。

## 既知の問題

- **macOS Safari** でダッシュボードが表示されない（WebSocket 接続エラー）。Chrome または iPhone Safari を使用のこと。詳細: [docs/known-issues.md](docs/known-issues.md)

## ファイル構成

| ファイル | 説明 |
|----------|------|
| `seedcare/collector.py` | MQTT デーモン。ESP32 からのデータを受信し1分平均に集約して DB に記録 |
| `seedcare/config.py` | `.env` から設定を読み込む dataclass |
| `seedcare/db.py` | SQLite アクセス層（WAL モード対応） |
| `seedcare/dashboard.py` | Streamlit ダッシュボード。30秒ごとに自動更新 |
| `seedcare/notifier.py` | 閾値超過・無通信時のメール通知 |
| `seedcare/purge.py` | 保持期限を超えた古いデータの日次削除 |
| `seedcare/__main__.py` | `python -m seedcare` エントリポイント |

## 開発方法
- Claude Code Opus 4.6 を使用して開発。

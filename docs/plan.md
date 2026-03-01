# SeedCare Monitor — 実装計画

## Context

植物の発芽促進のため、ESP32 で温度・湿度データを MQTT 経由で収集し SQLite に記録するシステム。macOS で手動運用していたものを Raspberry Pi 4B 上で常時稼働させ、Streamlit ダッシュボードで可視化する。メール通知の修復とデータ保持管理も行う。

**決定事項**: プロジェクト名 `seedcare`（plantDev から改名）、DB は新規開始、ダッシュボードにグラフ＋サマリーカード。

## アーキテクチャ

```
ESP32 → Mosquitto (Pi:1883) → [collector] → SQLite ← [dashboard] → Browser
                                    ↓
                              [notifier] → Gmail SMTP
```

Pi 上で 2 つの systemd サービスが動く:
1. `app@seedcare` — MQTT データ収集デーモン
2. `seedcare-dashboard` — Streamlit Web アプリ（port 8501）

## モジュール構成

| モジュール | 役割 |
|-----------|------|
| `config.py` | 環境変数から設定読み込み |
| `db.py` | SQLite アクセス層（WAL モード） |
| `collector.py` | MQTT デーモン |
| `notifier.py` | メール通知（バグ修正済み） |
| `dashboard.py` | Streamlit ダッシュボード |
| `purge.py` | データ保持期限管理（120日） |
| `__main__.py` | `python -m seedcare` エントリポイント |

## デプロイ

```bash
# Pi へデプロイ
./deploy.sh ../projects/seedcare raspi.local --restart

# ダッシュボードの systemd ユニットを配置
scp systemd/seedcare-dashboard.service pi@raspi.local:/tmp/
ssh pi@raspi.local "sudo mv /tmp/seedcare-dashboard.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now seedcare-dashboard"
```

## 旧コードからの改善点

1. **グローバル変数 → クラス**: `MQTTCollector`, `AlertTracker` でカプセル化
2. **ハードコード → 環境変数**: `.env` ファイルで設定管理
3. **send_mail バグ修正**: env var 未設定 `"None"` 問題、例外握りつぶし、成否不明を解消
4. **WAL モード**: collector と dashboard の並行アクセスを安全に
5. **日次パージ**: 120日超の古いデータを自動削除

# Known Issues

## macOS Safari でダッシュボードが表示されない

**環境:** Safari 26.3 / macOS 26.3

**症状:** `http://<pi-ip>:8501` にアクセスすると、Streamlit の HTML シェル（タイトル「Streamlit」）は読み込まれるが、画面が灰色のプレースホルダーのまま描画されない。ページソースは正常に取得できる。

**コンソールエラー:**
```
WebSocket connection to 'ws://192.168.1.203:8501/_stcore/stream' failed:
WebSocket is closed before the connection is established.
```

**影響範囲:** macOS Safari のみ。以下の環境では正常動作を確認済み:
- iOS Safari (iPhone)
- macOS Chrome
- curl (HTTP 200)

**試行済みの対策（効果なし）:**
- `--server.enableCORS false`
- `--server.enableXsrfProtection false`
- `--server.enableWebsocketCompression false`
- `--browser.serverAddress 0.0.0.0`

**原因:** macOS Safari の WebSocket 実装が、LAN 内の非暗号化 `ws://` 接続を確立前に切断している。iOS Safari では同じ制約が適用されないため、macOS 固有の挙動と推測される。

**回避策:** macOS では Chrome を使用する。

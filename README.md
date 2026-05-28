# ai-demo-container

AI Dashboard 動作検証用のデモ Gradio アプリケーション（呼び出し側ツール）。

ダッシュボードゲートウェイ経由で任意の登録済みツールへ `/ping` を投げ、`X-API-Key` と `X-User-Context`
リレーの挙動を目で確認できる。

## 構成
- `app.py`: Gradio アプリ本体 (Port: 7860)
- `requirements.txt`: 依存（gradio, requests）
- `Dockerfile`: コンテナビルド用

## 環境変数

| 変数 | 既定値 | 用途 |
|---|---|---|
| `DASHBOARD_API_URL` | `http://nginx/api` | ゲートウェイのベース URL。単独起動時は host から到達可能な URL に上書き |
| `DASHBOARD_API_KEY` | (空) | UI 初期値にだけ使う（フォームから手入力も可） |
| `TOOL_SLUG` | `ai-backend` | UI 初期値にだけ使う |
| `DEBUG_USER_CONTEXT` | (未設定) | **単独起動でリレー検証する時のみ**設定。X-User-Context トークンを手動投入 |

## 単独起動（開発時に推奨）

ツール開発中はダッシュボードに登録しない方が反復が早い。`make dev` でダッシュボード backend
（`localhost:10101`）が立ち上がっていれば、ai-demo-container は単独で起動できる。

### Python ローカル
```bash
cd ai-demo-container
pip install -r requirements.txt

DASHBOARD_API_URL=http://localhost:10101/api \
DASHBOARD_API_KEY=<ダッシュボードで発行した API キー> \
TOOL_SLUG=ai-backend \
python app.py
# → http://localhost:7860
```

### Docker 単独起動
```bash
docker build -t demo-tool .
docker run --rm -p 7860:7860 \
  -e DASHBOARD_API_URL=http://host.docker.internal:10101/api \
  -e DASHBOARD_API_KEY=... \
  -e TOOL_SLUG=ai-backend \
  demo-tool
```

## X-User-Context リレーを単独で検証する

単独起動だと nginx の `auth_request` が無いので、ブラウザから X-User-Context は届かない。リレー経路を
模擬するには、ダッシュボードで発行された X-User-Context トークンを手動で投入する。

```bash
# 1) ダッシュボードにブラウザでログイン後、devtools で auth_token cookie の値をコピー
#    （Application → Cookies → localhost → auth_token）

# 2) そのトークンで /api/internal/issue-context を叩き、レスポンスヘッダから X-User-Context を取得
curl -i 'http://localhost:10101/api/internal/issue-context' \
     -H "Cookie: auth_token=<step1 で取得した値>"
# → "X-User-Context: <relay_token>" がレスポンスヘッダに出る

# 3) その値を渡して単独起動
DEBUG_USER_CONTEXT="<relay_token>" \
DASHBOARD_API_URL=http://localhost:10101/api \
DASHBOARD_API_KEY=... \
python app.py
```

ダッシュボード「ログ履歴」画面で当該リクエストが `userID=yoshiki`（自分のアカウント）で記録されれば
リレーが効いている。relay_token の有効期限は5分なので、切れたら 2) からやり直し。

## ダッシュボード登録運用（仕上げ時）

開発が落ち着いたら通常どおりダッシュボードにツール登録（routing_type=subdomain 推奨）。
`DASHBOARD_API_URL` は未指定でよく、既定の `http://nginx/api` で docker 内通信に戻る。
`DEBUG_USER_CONTEXT` も外す（nginx auth_request から本物の X-User-Context が来る）。

# ai-demo-container

AI Dashboard 動作検証用のデモ Gradio アプリ（呼び出し側ツールの最小サンプル）。

ダッシュボードゲートウェイ経由で任意の登録済みツールへ `/ping` を投げ、ログイン中ユーザーの
identity が gateway 側で正しく記録されるかを目で確認できる。

## 認証モデル (JWT-only, t-087〜)

ツール側でやることは「受け取った `auth_token` cookie をそのまま gateway 呼び出しに forward する」だけ。
JWT デコード・鍵管理・API キー発行は一切不要。詳細は `ai-dashboard/docs/guides/jwt-cookie-relay.md`。

```python
auth_token = request.cookies.get("auth_token")
cookies = {"auth_token": auth_token} if auth_token else None
requests.get(f"{GATEWAY}/api/gateway/{slug}/ping", cookies=cookies)
```

## 構成
- `app.py`: Gradio アプリ本体 (Port 7860)
- `requirements.txt` / `pyproject.toml`: 依存 (gradio, requests)
- `Dockerfile`: コンテナビルド用

## 環境変数

| 変数 | 既定値 | 用途 |
|---|---|---|
| `DASHBOARD_API_URL` | `http://nginx/api` | ゲートウェイのベース URL。docker 内では既定のままでよい。ホストから単独起動する時は `http://localhost:10101/api` などに上書き |
| `TOOL_SLUG` | `ai-backend` | UI 初期値 (フォームから手入力も可) |
| `DEBUG_AUTH_TOKEN` | (未設定) | **単独起動デバッグ専用**。ブラウザの cookie がプロセスまで届かない場合に JWT を手動で投入する逃げ道 |
| `GRADIO_SERVER_PORT` | `7860` | UI ポート。dashboard 経由で `tool-demo` コンテナが既に 7860 を掴んでいる時は別ポートに切り替える |

## 単独起動 (推奨開発フロー)

ツール開発中はダッシュボードに登録しない方が反復が早い。手順:

1. `cd ai-dashboard && make dev` でダッシュボード一式 (backend: `localhost:10101`) を起動
2. ブラウザで `http://localhost:10101` にログイン (Google または Guest)
3. 同じブラウザで `http://localhost:7860` を開く  
   → `auth_token` cookie は `Domain=.localhost` で発行されているのでこのプロセスにも届く
4. Slug を入れて「Test Gateway Connectivity」を押す  
   → ダッシュボードの「ログ履歴」画面に自分のユーザー名で記録されれば成功

### Python ローカル
```bash
cd ai-demo-container
uv sync   # または: pip install -r requirements.txt

DASHBOARD_API_URL=http://localhost:10101/api \
TOOL_SLUG=ai-backend \
uv run python app.py
# → http://localhost:7860
```

### ⚠ Port 7860 が既に使われている場合

dashboard に demo ツールが登録されていると `tool-demo` コンテナが 7860 を掴んでいて
`OSError: Cannot find empty port in range: 7860-7860` で起動失敗する。回避策:

```bash
# A) 単独起動を別ポートで動かす
GRADIO_SERVER_PORT=7861 \
DASHBOARD_API_URL=http://localhost:10101/api \
uv run python app.py
# → http://localhost:7861

# B) または dashboard 側の demo コンテナを止めて 7860 を空ける
docker rm -f tool-demo
# (dashboard 上で「停止」操作してもよい)
```

### Docker 単独起動
```bash
docker build -t demo-tool .
docker run --rm -p 7860:7860 \
  -e DASHBOARD_API_URL=http://host.docker.internal:10101/api \
  -e TOOL_SLUG=ai-backend \
  demo-tool
```

## cookie が届かないケース (デバッグ用 fallback)

別ブラウザから検証する、curl で叩く、Domain 設定が崩れている、などの理由で `auth_token` cookie が
プロセスに届かない場合は `DEBUG_AUTH_TOKEN` で JWT を直接渡せる。

```bash
# 1) ログイン済みブラウザの devtools で auth_token cookie の値をコピー
#    (Application → Cookies → localhost → auth_token)

# 2) その JWT を渡して単独起動
DEBUG_AUTH_TOKEN="<コピーした JWT>" \
DASHBOARD_API_URL=http://localhost:10101/api \
python app.py
```

JWT の有効期限はデフォルト 24h。切れたら 1) からやり直し。

## curl での直接確認

UI を経由せず curl で gateway を叩く時:
```bash
# ログイン済みブラウザの auth_token を Cookie ヘッダで渡す
curl -i 'http://localhost:10101/api/gateway/ai-backend/ping' \
     -H "Cookie: auth_token=<JWT>"
```

## ダッシュボード登録運用 (本番に近い形で動かす時)

開発が落ち着いたら通常どおりダッシュボードにツール登録 (routing_type=subdomain 推奨)。

- `DASHBOARD_API_URL` は未指定でよく、既定の `http://nginx/api` で docker 内通信に戻る
- `DEBUG_AUTH_TOKEN` も外す (ブラウザ cookie がそのまま流れる)
- 登録後は `http://demo.localhost` (またはサブドメイン) からアクセスし、自分のユーザー名で記録されることを確認

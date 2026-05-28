"""ai-demo-container: ダッシュボードゲートウェイの疎通確認用 Gradio デモ。

JWT-only 方針 (t-087〜) では、ツール作者の責任は
「受け取った auth_token cookie を gateway 呼び出しにそのまま forward する」だけ。
本ファイルは最小サンプルとして、その動作確認を UI 上で行えるようにしている。
"""

import os
import requests
import gradio as gr

# 単独起動時は DASHBOARD_API_URL=http://localhost:10101/api 等で上書き可。
# ダッシュボード管理下 (docker 内) では既定値の http://nginx/api を使う。
BASE_API = os.environ.get("DASHBOARD_API_URL", "http://nginx/api")


def build_url(slug: str) -> str:
    return f"{BASE_API}/{slug.strip('/')}/ping"


def _resolve_auth_token(request: gr.Request | None) -> str | None:
    """auth_token を取得する。

    優先順:
      1. inbound cookie の auth_token  (ブラウザがログイン済みドメインから来た場合)
      2. 環境変数 DEBUG_AUTH_TOKEN     (cookie が流れない単独起動デバッグ用)
    """
    if request is not None and hasattr(request, "cookies"):
        token = request.cookies.get("auth_token")
        if token:
            return token
    return os.environ.get("DEBUG_AUTH_TOKEN") or None


def test_gateway_connection(slug: str, request: gr.Request | None = None):
    if not slug:
        return "⚠️ Slug is required.", {"error": "Slug is required."}

    url = build_url(slug)
    auth_token = _resolve_auth_token(request)
    cookies = {"auth_token": auth_token} if auth_token else None

    if not auth_token:
        # ゲートウェイは未認証だと 401 を返すが、デバッグ容易化のためフロント側でもヒントを出す。
        return url, {
            "warning": (
                "auth_token cookie が見つかりませんでした。ダッシュボードにログイン済みのブラウザ"
                "から開くか、単独起動時は DEBUG_AUTH_TOKEN 環境変数を設定してください。"
            ),
        }

    try:
        resp = requests.get(url, cookies=cookies, timeout=5)
        result = {
            "status_code": resp.status_code,
            "url": url,
            "headers": dict(resp.headers),
            "body": resp.text,
        }
        try:
            result["json"] = resp.json()
        except Exception:
            pass
        return url, result
    except Exception as e:
        return url, {"error": f"Request failed: {str(e)}"}


with gr.Blocks(title="AI Dashboard Demo") as demo:
    gr.Markdown("# 🌐 AI Dashboard Demo - Gateway Test")
    gr.Markdown(
        "Validate connectivity with any registered tool via the `ai-dashboard` API Gateway.\n\n"
        "**URL format**: `{base}/{slug}/ping` (e.g. `http://nginx/api/ai-backend/ping`)\n\n"
        "**認証**: ブラウザの `auth_token` cookie をそのまま gateway へ forward します。"
        "ツール側で API キーや JWT のデコードは不要です (JWT-only 方針)。"
    )

    with gr.Row():
        with gr.Column():
            slug = gr.Textbox(
                label="Tool Slug",
                placeholder="ai-backend",
                value=os.environ.get("TOOL_SLUG", "ai-backend"),
            )
            url_preview = gr.Textbox(
                label="Request URL (preview)",
                value=build_url(os.environ.get("TOOL_SLUG", "ai-backend")),
                interactive=False,
            )
            btn = gr.Button("Test Gateway Connectivity", variant="primary")

        with gr.Column():
            output = gr.JSON(label="Gateway Response")

    # Update URL preview on slug change
    slug.change(fn=build_url, inputs=slug, outputs=url_preview)

    btn.click(
        fn=test_gateway_connection,
        inputs=[slug],
        outputs=[url_preview, output],
    )

if __name__ == "__main__":
    # ポート切替可能 (デフォルト 7860、tool-demo コンテナと衝突する場合は別ポートを env で指定)
    server_port = int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=server_port)

import os
import requests
import gradio as gr

# 単独起動時は DASHBOARD_API_URL=http://localhost:10101/api 等で上書き可
BASE_API = os.environ.get("DASHBOARD_API_URL", "http://nginx/api")

def build_url(slug: str) -> str:
    return f"{BASE_API}/{slug.strip('/')}/ping"

def test_gateway_connection(api_key: str, slug: str, request: gr.Request = None):
    if not api_key:
        return "⚠️ API Key is required.", {"error": "API Key is required."}
    if not slug:
        return "⚠️ Slug is required.", {"error": "Slug is required."}

    url = build_url(slug)
    headers = {"X-API-Key": api_key}
    if request is not None:
        user_context = request.headers.get("x-user-context")
        if user_context:
            headers["X-User-Context"] = user_context

    # Dev fallback: 単独起動時は nginx auth_request が無く X-User-Context が
    # 来ないので、DEBUG_USER_CONTEXT を設定するとリレー先頭ホップを模擬できる
    if "X-User-Context" not in headers:
        debug_ctx = os.environ.get("DEBUG_USER_CONTEXT")
        if debug_ctx:
            headers["X-User-Context"] = debug_ctx

    try:
        resp = requests.get(url, headers=headers, timeout=5)
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
        "**URL format**: `http://nginx/api/{slug}/ping`"
    )

    with gr.Row():
        with gr.Column():
            api_key = gr.Textbox(
                label="Dashboard API Key (X-API-Key)",
                placeholder="aid_...",
                type="password",
                value=os.environ.get("DASHBOARD_API_KEY", ""),
            )
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
        inputs=[api_key, slug],
        outputs=[url_preview, output],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

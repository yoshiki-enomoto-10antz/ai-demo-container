import os
import requests
import gradio as gr

def test_gateway_connection(api_key, base_url):
    if not api_key:
        return {"error": "API Key is required."}
    
    url = f"{base_url.rstrip('/')}/gateway/ai-gradio-backend/ping"
    headers = {
        "X-API-Key": api_key
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        result = {
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp.text
        }
        try:
            result["json"] = resp.json()
        except Exception:
            pass
        return result
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

# Define Gradio Interface using Blocks
with gr.Blocks(title="AI Dashboard Demo") as demo:
    gr.Markdown("# 🌐 AI Dashboard Demo - Gateway Test")
    gr.Markdown("Validate connectivity with `ai-gradio-backend` via the `ai-dashboard` API Gateway.")
    
    with gr.Row():
        with gr.Column():
            api_key = gr.Textbox(
                label="Dashboard API Key (X-API-Key)", 
                placeholder="aid_...", 
                type="password",
                value=os.environ.get("DASHBOARD_API_KEY", "")
            )
            base_url = gr.Textbox(
                label="Dashboard API Base URL", 
                value="http://nginx/api"
            )
            btn = gr.Button("Test Gateway Connectivity", variant="primary")
        
        with gr.Column():
            output = gr.JSON(label="Gateway Response")
            
    btn.click(
        fn=test_gateway_connection,
        inputs=[api_key, base_url],
        outputs=output
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

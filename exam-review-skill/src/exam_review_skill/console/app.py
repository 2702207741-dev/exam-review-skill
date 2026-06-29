"""
Quick Console — Gradio 调试面板

上传文件 → 预览解析 → 一键生成 → 下载
"""

from __future__ import annotations


def create_app():
    """创建 Gradio 应用"""
    try:
        import gradio as gr
    except ImportError:
        raise ImportError(
            "Quick Console 需要 gradio。安装: pip install gradio"
        )

    from .components.upload import handle_upload
    from .components.preview import generate_preview
    from .components.download import generate_and_download

    # 自定义 CSS (Dragon Dark 主题)
    custom_css = """
    .gradio-container { background: #0a0e27 !important; color: #e0e0e0 !important; }
    .gradio-container * { border-color: #2a2a4e !important; }
    .gradio-container input, .gradio-container textarea, .gradio-container select {
        background: #1a1a3e !important; color: #e0e0e0 !important; border: 1px solid #333 !important;
    }
    .gradio-container button {
        background: linear-gradient(135deg, #ffd54f, #ffb300) !important;
        color: #0a0e27 !important; font-weight: bold !important; border: none !important;
    }
    .gradio-container button:hover { opacity: 0.9; }
    .gradio-container .tab-nav button { background: #1a1a3e !important; color: #aaa !important; }
    .gradio-container .tab-nav button.selected { background: #ffd54f !important; color: #0a0e27 !important; }
    """

    with gr.Blocks(
        title="Exam Review Skill v2.0 - Quick Console",
        css=custom_css,
        theme=gr.themes.Soft(),
    ) as app:
        gr.Markdown(
            "# Exam Review Skill v2.0 — Quick Console\n"
            "上传学习素材，一键生成期末复习资料。支持 PPTX/DOCX/PDF/TXT/Markdown。"
        )

        # 状态存储
        files_state = gr.State([])

        with gr.Row():
            with gr.Column(scale=1):
                # ① 上传区域
                gr.Markdown("### ① 上传素材")
                file_upload = gr.File(
                    label="拖拽文件到此处",
                    file_count="multiple",
                    file_types=[".pptx", ".docx", ".pdf", ".txt", ".md"],
                )
                upload_status = gr.Textbox(label="状态", interactive=False, lines=2)

                # ② 配置
                gr.Markdown("### ② 配置")
                course_name = gr.Textbox(label="课程名称", placeholder="如：Python 程序设计")
                analysis_mode = gr.Radio(
                    ["llm", "rule"],
                    label="分析模式",
                    value="llm",
                    info="llm: DeepSeek API 语义分析 | rule: 离线规则引擎",
                )
                mind_map_depth = gr.Slider(
                    1, 5, value=3, step=1, label="思维导图深度"
                )
                focus = gr.Dropdown(
                    ["均衡", "概念", "公式", "例题", "定理证明"],
                    label="侧重方向",
                    value="均衡",
                )

                analyze_btn = gr.Button("🚀 开始分析", variant="primary")

            with gr.Column(scale=2):
                # ③ 预览区域
                gr.Markdown("### ③ 预览")
                stats_text = gr.Textbox(label="统计", interactive=False)

                with gr.Tabs():
                    with gr.TabItem("思维导图"):
                        mindmap_preview = gr.HTML()
                    with gr.TabItem("基础概念"):
                        basic_preview = gr.HTML()
                    with gr.TabItem("高频考点"):
                        hf_preview = gr.HTML()
                    with gr.TabItem("易错点"):
                        error_preview = gr.HTML()

        # ④ 下载区域
        gr.Markdown("### ④ 下载")
        with gr.Row():
            generate_btn = gr.Button("📦 生成下载文件", variant="secondary")
        with gr.Row():
            json_download = gr.File(label="JSON 完整结果")
            md_download = gr.File(label="Markdown 思维导图")
            mermaid_download = gr.File(label="Mermaid 导图")
            html_download = gr.File(label="知识图谱 HTML (D3.js)")

        # 事件绑定
        file_upload.change(
            fn=handle_upload,
            inputs=[file_upload],
            outputs=[upload_status],
        ).then(
            fn=lambda f: f,
            inputs=[file_upload],
            outputs=[files_state],
        )

        analyze_btn.click(
            fn=generate_preview,
            inputs=[files_state, course_name, analysis_mode],
            outputs=[mindmap_preview, basic_preview, hf_preview, error_preview, stats_text],
        )

        generate_btn.click(
            fn=generate_and_download,
            inputs=[files_state, course_name, mind_map_depth, focus, analysis_mode],
            outputs=[json_download, md_download, mermaid_download, html_download],
        )

    return app


def launch(port: int = 7860, share: bool = False):
    """启动 Quick Console"""
    app = create_app()
    app.launch(server_port=port, share=share)


if __name__ == "__main__":
    launch()

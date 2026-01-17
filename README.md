# WPT AutoGen Studio Pro

WPT AutoGen Studio 是一款基于 AI 的 Web 平台测试 (Web Platform Tests) 脚本自动化构建工作站。它可以帮助开发者通过自然语言描述快速生成符合 W3C 标准的测试用例，并在本地 WPT Server 环境中进行实时调试。

## ✨ 核心特性

- 🚀 **智能生成**：利用 GPT-4o / Gemini 2.0 引擎快速编排标准的 WPT 脚本。
- 📝 **交互式编辑器**：内置沉浸式代码编辑器，支持所见即所得的微调。
- 🌓 **双模皮肤**：支持高级冷色 (Cool Pro) 与暖色 (Amber Gold) 皮肤一键切换。
- 📁 **全量集成**：完美对接本地全量 WPT 仓库，支持 `local_test` 目录隔离存储。
- 🌐 **一键预览**：自动映射本地 WPT Server (8000 端口)，实现秒级跑测。

## 🛠️ 安装与运行

1. **准备全量 WPT 环境** (可选):
   ```bash
   git clone --depth 1 https://github.com/web-platform-tests/wpt.git
   ```

2. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境**:
   创建 `.env` 文件并填入您的 API KEY:
   ```env
   OPENAI_API_KEY=your_api_key_here
   OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
   ```

4. **启动应用**:
   ```bash
   python3 -m streamlit run src/app.py
   ```

## 📂 目录结构

- `src/`: 核心源代码 (Engine, App)
- `prompts/`: 结构化提示词模板
- `.env`: 环境配置文件 (不提交至仓库)

---
Built with ❤️ for Web Standards Developers.

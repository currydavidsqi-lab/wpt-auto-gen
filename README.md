# WPT Studio Pro

WPT Studio Pro 是一款基于 AI 的 Web 平台测试 (Web Platform Tests) 脚本自动化构建工作站。它集成了生成、编辑、同步、运行全链路功能，赋能开发者快速产出符合 W3C 标准的测试用例。

## ✨ 核心特性

- 🚀 **智能生成**：利用 GPT-4o / Gemini 2.0 引擎快速编排标准的 WPT 脚本。
- 🛠️ **环境自愈**：应用自动检测本地 WPT 仓库状态，支持一键极速初始化（Git Clone）。
- 📝 **沉浸式编辑器**：内置交互式代码编辑器，支持所见即所得的实时调试。
- 📡 **Server 自动管护**：后台自动开启并管理 WPT HTTP Server (8000端口)，进程随网页启停。
- 🌓 **双模皮肤**：提供高级深色 (Dark) 与浅色 (Light) 模式，适配不同开发场景。
- 🌏 **全中文交互**：深度汉化的 UI 界面，提供极致的使用爽感。

## 🛠️ 安装与运行

1. **拉取仓库**:
   ```bash
   git clone https://github.com/currydavidsqi-lab/wpt-auto-gen.git
   cd wpt-auto-gen
   ```

2. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

3. **启动应用**:
   ```bash
   python3 -m streamlit run src/app.py
   ```

4. **初始化环境**:
   在启动后的网页侧边栏，点击 **“🛠️ 自动初始化 WPT 环境”** 按钮，系统将自动为您克隆官方 WPT 仓库并配置 Server。

## 📂 目录结构

- `src/`: 核心源代码 (Engine, App, Runner)
- `prompts/`: 结构化提示词模板
- `wpt/`: (自动拉取) 官方 Web 平台测试仓库
- `wpt/local_test/`: 生成用例的默认存放位置

---
Built with ❤️ for Web Standards Professionals.

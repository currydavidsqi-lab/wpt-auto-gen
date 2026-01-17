import streamlit as st
import os
import time
from pathlib import Path
from engine import generate_wpt_code
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# --- 1. 主题与持久化配置 ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

st.set_page_config(
    page_title="WPT Studio Pro",
    page_icon="🧪",
    layout="wide"
)

# --- 2. 旗舰配色方案 ---
THEMES = {
    'light': {
        'bg': '#FFFFFF',
        'sub_bg': '#F8FAFC',
        'sidebar': '#F1F5F9',
        'text': '#1E293B',
        'sub_text': '#64748B',
        'primary': '#2563EB',
        'border': '#E2E8F0',
        'input_bg': '#FFFFFF',
        'code_bg': '#FDFDFD'
    },
    'dark': {
        'bg': '#0F172A',
        'sub_bg': '#1E293B',
        'sidebar': '#020617',
        'text': '#F1F5F9',
        'sub_text': '#94A3B8',
        'primary': '#3B82F6',
        'border': '#334155',
        'input_bg': '#1E293B',
        'code_bg': '#0B1120'
    }
}

curr = THEMES[st.session_state.theme]

# --- 3. 动态 CSS 注入 (解决颜色可见性与 UX) ---
# 注意：在 f-string 中，CSS 的大括号需要转义为 {{ 和 }}
st.markdown(f"""
    <style>
    /* 全局背景 */
    .stApp {{
        background-color: {curr['bg']};
        color: {curr['text']};
    }}
    
    /* 侧边栏美化 */
    [data-testid="stSidebar"] {{
        background-color: {curr['sidebar']} !important;
        border-right: 1px solid {curr['border']} !important;
    }}
    [data-testid="stSidebar"] * {{
        color: {curr['text']} !important;
    }}

    /* 修复顶部 Header 颜色（解决深色模式白边问题） */
    header[data-testid="stHeader"] {{
        background-color: {curr['bg']} !important;
        border-bottom: 1px solid {curr['border']} !important;
    }}
    header[data-testid="stHeader"] * {{
        color: {curr['text']} !important;
    }}
    
    /* 修复输入框文字颜色与样式 */
    .stTextArea textarea {{
        color: {curr['text']} !important;
        background-color: {curr['input_bg']} !important;
        border: 1px solid {curr['border']} !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        line-height: 1.6 !important;
    }}
    .stTextInput input {{
        color: {curr['text']} !important;
        background-color: {curr['input_bg']} !important;
        border: 1px solid {curr['border']} !important;
        border-radius: 10px !important;
    }}
    
    /* 占位符可见性 */
    ::placeholder {{
        color: {curr['sub_text']} !important;
        opacity: 0.5;
    }}

    /* 标题样式 */
    h1, h2, h3 {{
        color: {curr['text']} !important;
        font-weight: 800 !important;
        letter-spacing: -1.5px !important;
    }}

    /* 主按钮样式 */
    div.stButton > button {{
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        border: 1px solid {curr['border']} !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        background-color: {curr['bg']} !important;
        color: {curr['text']} !important;
    }}
    div.stButton > button[kind="primary"] {{
        background-color: {curr['primary']} !important;
        color: white !important;
        border: none !important;
    }}
    div.stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
    }}

    /* 代码编辑器样式 */
    .editor-box textarea {{
        background-color: {curr['code_bg']} !important;
        font-family: 'Fira Code', 'JetBrains Mono', monospace !important;
        font-size: 14px !important;
    }}
    
    /* 移除冗余装饰 */
    .st-emotion-cache-12w0qpk {{
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 侧边栏：核心配置 ---
with st.sidebar:
    st.markdown("### 🛠️ 工作站设置")
    
    # 主题切换
    st.markdown("#### 🌗 主题模式")
    mode = st.toggle("深色模式", value=(st.session_state.theme == 'dark'))
    new_theme = 'dark' if mode else 'light'
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()
    
    st.divider()
    
    # 路径配置
    st.markdown("#### 📂 WPT 路径")
    wpt_root = st.text_input("仓库目录", 
                            value=os.getenv("WPT_ROOT", "/Users/oh5/Documents/Code/wpt"),
                            label_visibility="collapsed")
    st.caption("脚本将同步至 `/local_test/` 文件夹")
    
    # API 配置
    st.divider()
    with st.expander("🔑 接口凭据"):
        api_key = st.text_input("API KEY", value=os.getenv("OPENAI_API_KEY", ""), type="password")
        base_url = st.text_input("Base URL", value=os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"))
        model_name = st.text_input("模型选择", value="gemini-2.0-flash")

# --- 5. 主界面：英雄式输入区 ---
st.markdown(f"<h1 style='text-align: center;'>WPT Studio <span style='color:{curr['primary']}'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: {curr['sub_text']}; margin-top: -15px;'>工业级 Web 平台测试脚本自动化工作站</p>", unsafe_allow_html=True)

st.write("")

# 需求输入大框
demand = st.text_area("Test Purpose", 
                     placeholder="例如：验证 Geolocation API 的基本授权逻辑...", 
                     height=140,
                     label_visibility="collapsed")

# 指令工具条
col_tag, col_go = st.columns([4, 1])
with col_tag:
    feature = st.text_input("Feature Tag", placeholder="特性标签 (如: geolocation, css-grid...)", label_visibility="collapsed")
with col_go:
    generate_btn = st.button("🚀 构建脚本", type="primary", use_container_width=True)

# 初始化 Session State
if 'code' not in st.session_state:
    st.session_state.code = ""
if 'filename' not in st.session_state:
    st.session_state.filename = "test.html"

# --- 生成逻辑 ---
if generate_btn:
    if not demand:
        st.toast("⚠️ 请输入测试需求描述", icon="❗")
    elif not api_key:
        st.error("❌ API KEY 未配置，请检查侧边栏。")
    else:
        with st.status("🏗️ 正在编排 WPT 脚本...", expanded=False) as status:
            try:
                result = generate_wpt_code(demand, feature, api_key, base_url, model_name)
                st.session_state.code = result.get("content", "")
                
                # 1. 提取原始文件名并打平路径
                raw_filename = os.path.basename(result.get("filename", "test.html"))
                name_part, ext_part = os.path.splitext(raw_filename)
                
                # 2. 追加时间戳后缀，确保每次生成均为唯一新文件，彻底解决缓存问题
                timestamp = time.strftime("%H%M%S")
                st.session_state.filename = f"{name_part}_{timestamp}{ext_part}"
                
                status.update(label="✅ 脚本构建完成", state="complete")
                st.balloons()
            except Exception as e:
                status.update(label="❌ 生成失败", state="error")
                st.error(str(e))

# --- 6. 沉浸式工作台 ---
if st.session_state.code:
    st.write("")
    st.markdown("---")
    
    # 顶部工具栏
    t_col1, t_col2, t_col3, t_col4 = st.columns([2, 1, 1, 1])
    
    with t_col1:
        st.markdown(f"<div style='padding-top: 8px; font-weight: 700; color: {curr['primary']};'>📁 {st.session_state.filename}</div>", unsafe_allow_html=True)
    
    with t_col2:
        target_dir = Path(wpt_root) / "local_test"
        if st.button("💾 同步本地", use_container_width=True):
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                full_path = target_dir / st.session_state.filename
                full_path.write_text(st.session_state.code, encoding="utf-8")
                st.toast("同步成功！", icon="✅")
            except Exception as e:
                st.error(f"写入失败: {e}")
                
    with t_col3:
        wpt_url = f"http://web-platform.test:8000/local_test/{st.session_state.filename}"
        st.link_button("🌐 测试预览", wpt_url, type="primary", use_container_width=True)
    
    with t_col4:
        if st.button("🧹 重置", use_container_width=True):
            st.session_state.code = ""
            st.rerun()

    # 沉浸式编辑器
    edited_code = st.text_area(
        "Source Code Editor",
        value=st.session_state.code,
        height=600,
        label_visibility="collapsed",
        key="editor_main"
    )
    st.session_state.code = edited_code

st.write("")
st.write("")
st.markdown(f"<p style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>WPT Studio Pro v4.0 | Next-Gen Testing Workflow</p>", unsafe_allow_html=True)

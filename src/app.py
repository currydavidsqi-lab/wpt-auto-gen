import streamlit as st
import os
import time
import subprocess
import atexit
import signal
import sys
from pathlib import Path
from engine import generate_wpt_code
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# --- 0. 环境自动化配置逻辑 ---
@st.cache_resource
def check_and_init_env():
    """确保 WPT 仓库路径正确"""
    base_dir = Path(__file__).parent.parent
    wpt_path = base_dir / "wpt"
    return wpt_path

# --- 1. Server 管理逻辑 ---
@st.cache_resource
def get_server_manager():
    class ServerManager:
        def __init__(self):
            self.process = None
            self.current_root = None

        def start(self, root_path):
            if not os.path.exists(root_path):
                return False
            if self.process and self.current_root == root_path:
                if self.process.poll() is None:
                    return True
            
            self.stop()
            try:
                # 启动 http.server
                preexec = os.setsid if os.name != 'nt' else None
                self.process = subprocess.Popen(
                    [sys.executable, "-m", "http.server", "8000"],
                    cwd=root_path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=preexec
                )
                self.current_root = root_path
                time.sleep(0.5)
                return True
            except Exception as e:
                print(f"Server start error: {e}")
                return False

        def stop(self):
            if self.process:
                try:
                    if os.name != 'nt':
                        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                    else:
                        self.process.terminate()
                except:
                    pass
                finally:
                    self.process = None
                    self.current_root = None

    manager = ServerManager()
    atexit.register(manager.stop)
    return manager

server_manager = get_server_manager()

# --- 2. 页面配置 ---
st.set_page_config(
    page_title="WPT Studio Pro",
    page_icon="🧪",
    layout="wide"
)

# 初始化 Session State
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

# --- 3. 侧边栏：环境自动化与配置 ---
with st.sidebar:
    st.title("🧪 WPT Studio Pro")
    st.markdown("---")
    
    # 1. WPT 仓库自动初始化
    st.markdown("#### 📂 仓库环境")
    wpt_root_path = check_and_init_env()
    
    # 允许通过侧边栏自定义路径，但默认指向项目内
    wpt_root = st.text_input("WPT 根目录", value=os.getenv("WPT_ROOT", str(wpt_root_path)))
    
    if not os.path.exists(wpt_root):
        st.error("🔴 WPT 仓库缺失")
        if st.button("🛠️ 自动初始化 WPT 环境", use_container_width=True):
            with st.status("正在拉取官方 WPT 仓库 (极速模式)...") as status:
                try:
                    subprocess.run(["git", "clone", "--depth", "1", "https://github.com/web-platform-tests/wpt.git", wpt_root], check=True)
                    status.update(label="✅ 环境准备就绪！", state="complete")
                    st.rerun()
                except Exception as e:
                    status.update(label="❌ 初始化失败", state="error")
                    st.error(f"请检查网络或手动执行: git clone --depth 1 https://github.com/web-platform-tests/wpt.git {wpt_root}")
    else:
        if server_manager.start(wpt_root):
            st.success("🟢 本地 Server 已就绪 (8000)")
        else:
            st.error("🔴 Server 启动失败")

    # 2. 主题切换
    st.divider()
    st.markdown("#### 🌗 界面外观")
    mode = st.toggle("深色模式", value=(st.session_state.theme == 'dark'))
    new_theme = 'dark' if mode else 'light'
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

    # 3. API 配置
    st.divider()
    with st.expander("🔑 API 访问凭据"):
        api_key = st.text_input("API KEY", value=os.getenv("OPENAI_API_KEY", ""), type="password")
        base_url = st.text_input("Base URL", value=os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"))
        model_name = st.text_input("模型名称", value="gemini-2.0-flash")

# --- 4. 动态风格注入 ---
curr = {
    'light': {
        'bg': '#FFFFFF', 
        'sidebar': '#F1F5F9', 
        'text': '#1E293B', 
        'sub_text': '#64748B', 
        'primary': '#2563EB', 
        'border': '#E2E8F0', 
        'input_bg': '#FFFFFF',
        'btn_text': '#1E293B'
    },
    'dark': {
        'bg': '#0F172A', 
        'sidebar': '#020617', 
        'text': '#F1F5F9', 
        'sub_text': '#94A3B8', 
        'primary': '#3B82F6', 
        'border': '#334155', 
        'input_bg': '#1E293B',
        'btn_text': '#F1F5F9'
    }
}[st.session_state.theme]

st.markdown(f"""
    <style>
    .stApp {{ background-color: {curr['bg']}; color: {curr['text']}; }}
    
    /* 侧边栏美化 */
    [data-testid="stSidebar"] {{ background-color: {curr['sidebar']} !important; border-right: 1px solid {curr['border']} !important; }}
    [data-testid="stSidebar"] * {{ color: {curr['text']} !important; }}
    
    /* 强制修复侧边栏折叠框 (Expander) 标题和文字颜色 */
    [data-testid="stSidebar"] .st-emotion-cache-p5msec {{ color: {curr['text']} !important; }}
    [data-testid="stSidebar"] summary {{ color: {curr['text']} !important; }}
    [data-testid="stSidebar"] label {{ color: {curr['text']} !important; }}
    [data-testid="stSidebar"] p {{ color: {curr['text']} !important; }}
    
    /* Header 适配 */
    header[data-testid="stHeader"] {{ background-color: {curr['bg']} !important; border-bottom: 1px solid {curr['border']} !important; }}
    header[data-testid="stHeader"] * {{ color: {curr['text']} !important; }}
    
    /* 输入框文字颜色修复 */
    .stTextArea textarea, .stTextInput input {{ 
        color: {curr['text']} !important; 
        background-color: {curr['input_bg']} !important; 
        border: 1px solid {curr['border']} !important; 
        border-radius: 12px !important;
        -webkit-text-fill-color: {curr['text']} !important;
    }}
    
    /* 按钮文字颜色修复 */
    div.stButton > button {{ 
        border-radius: 12px !important; 
        font-weight: 600 !important; 
        color: {curr['btn_text']} !important;
        background-color: {curr['input_bg']} !important;
        border: 1px solid {curr['border']} !important;
        transition: all 0.2s ease-in-out !important;
    }}
    div.stButton > button[kind="primary"] {{ 
        background-color: {curr['primary']} !important; 
        color: white !important; 
        border: none !important; 
    }}
    
    /* 占位符颜色 */
    ::placeholder {{ color: {curr['sub_text']} !important; opacity: 0.6; }}
    
    /* 移除冗余边框 */
    .st-emotion-cache-12w0qpk {{ border: none !important; background: transparent !important; box-shadow: none !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. 主界面 ---
st.markdown(f"<h1 style='text-align: center;'>WPT Studio <span style='color:{curr['primary']}'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: {curr['sub_text']}; margin-top: -15px;'>工业级 Web 平台测试脚本自动化工作站 (v4.7)</p>", unsafe_allow_html=True)

st.write("")

# 需求输入
demand = st.text_area("Test Requirement", placeholder="请输入您的测试目标...", height=140, label_visibility="collapsed")

# 指令条
col_tag, col_go = st.columns([4, 1])
with col_tag:
    feature = st.text_input("Feature Tag", placeholder="特性标签...", label_visibility="collapsed")
with col_go:
    generate_btn = st.button("🚀 构建脚本", type="primary", use_container_width=True)

# 初始化状态
if 'code' not in st.session_state: st.session_state.code = ""
if 'filename' not in st.session_state: st.session_state.filename = "test.html"

# 生成逻辑
if generate_btn:
    if not demand: st.toast("请输入需求", icon="⚠️")
    elif not api_key: st.error("API KEY 未配置")
    else:
        with st.status("🏗️ 正在编排脚本...", expanded=False) as status:
            try:
                result = generate_wpt_code(demand, feature, api_key, base_url, model_name)
                st.session_state.code = result.get("content", "")
                raw_filename = os.path.basename(result.get("filename", "test.html"))
                name_part, ext_part = os.path.splitext(raw_filename)
                st.session_state.filename = f"{name_part}_{time.strftime('%H%M%S')}.html"
                status.update(label="✅ 生成成功", state="complete")
                st.balloons()
            except Exception as e:
                status.update(label="❌ 失败", state="error")
                st.error(str(e))

# --- 6. 工作台 ---
if st.session_state.code:
    st.markdown("---")
    t_col1, t_col2, t_col3, t_col4 = st.columns([2, 1, 1, 1])
    
    with t_col1:
        st.markdown(f"<div style='padding-top: 8px; font-weight: 700; color: {curr['primary']};'>📁 {st.session_state.filename}</div>", unsafe_allow_html=True)
    
    with t_col2:
        if st.button("💾 同步本地", use_container_width=True):
            try:
                target_dir = Path(wpt_root) / "local_test"
                target_dir.mkdir(parents=True, exist_ok=True)
                (target_dir / st.session_state.filename).write_text(st.session_state.code, encoding="utf-8")
                st.toast("同步成功！", icon="✅")
            except Exception as e: st.error(f"写入失败: {e}")
                
    with t_col3:
        wpt_url = f"http://localhost:8000/local_test/{st.session_state.filename}"
        st.link_button("🌐 测试运行", wpt_url, type="primary", use_container_width=True)
    
    with t_col4:
        if st.button("🧹 重置工作台", use_container_width=True):
            st.session_state.code = ""; st.rerun()

    st.session_state.code = st.text_area("Code Editor", value=st.session_state.code, height=600, label_visibility="collapsed", key="main_editor")

st.write("")
st.markdown(f"<p style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>WPT Studio Pro v4.7 | 环境自动化版</p>", unsafe_allow_html=True)

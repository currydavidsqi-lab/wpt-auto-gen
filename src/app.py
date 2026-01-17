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

# --- 1. Server 管理逻辑 ---
@st.cache_resource
def get_server_manager():
    class ServerManager:
        def __init__(self):
            self.process = None
            self.current_root = None

        def start(self, root_path):
            if self.process and self.current_root == root_path:
                if self.process.poll() is None:
                    return True
            
            self.stop()
            
            try:
                self.process = subprocess.Popen(
                    [sys.executable, "-m", "http.server", "8000"],
                    cwd=root_path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid if os.name != 'nt' else None
                )
                self.current_root = root_path
                time.sleep(0.5)
                return True
            except Exception as e:
                print(f"服务启动失败: {e}")
                return False

        def stop(self):
            if self.process:
                try:
                    if os.name != 'nt':
                        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                    else:
                        self.process.terminate()
                except Exception as e:
                    print(f"停止服务时出错: {e}")
                finally:
                    self.process = None
                    self.current_root = None

    manager = ServerManager()
    atexit.register(manager.stop)
    return manager

server_manager = get_server_manager()

# --- 2. 页面基本配置 ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

st.set_page_config(
    page_title="WPT Studio Pro",
    page_icon="🧪",
    layout="wide"
)

# --- 3. 旗舰配色方案 ---
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

# --- 4. 动态 CSS 注入 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {curr['bg']}; color: {curr['text']}; }}
    [data-testid="stSidebar"] {{ background-color: {curr['sidebar']} !important; border-right: 1px solid {curr['border']} !important; }}
    [data-testid="stSidebar"] * {{ color: {curr['text']} !important; }}
    header[data-testid="stHeader"] {{ background-color: {curr['bg']} !important; border-bottom: 1px solid {curr['border']} !important; }}
    header[data-testid="stHeader"] * {{ color: {curr['text']} !important; }}
    .stTextArea textarea {{ color: {curr['text']} !important; background-color: {curr['input_bg']} !important; border: 1px solid {curr['border']} !important; border-radius: 12px !important; padding: 1rem !important; line-height: 1.6 !important; }}
    .stTextInput input {{ color: {curr['text']} !important; background-color: {curr['input_bg']} !important; border: 1px solid {curr['border']} !important; border-radius: 10px !important; }}
    ::placeholder {{ color: {curr['sub_text']} !important; opacity: 0.5; }}
    div.stButton > button {{ border-radius: 12px !important; padding: 0.6rem 1.5rem !important; font-weight: 600 !important; transition: all 0.2s; }}
    div.stButton > button[kind="primary"] {{ background-color: {curr['primary']} !important; color: white !important; border: none !important; }}
    div.stButton > button:hover {{ transform: translateY(-2px) !important; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important; }}
    .st-emotion-cache-12w0qpk {{ border: none !important; background: transparent !important; box-shadow: none !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. 侧边栏：核心配置 ---
with st.sidebar:
    st.title("🧪 工作站配置")
    
    # 主题切换
    st.markdown("#### 🌗 界面外观")
    mode = st.toggle("深色模式", value=(st.session_state.theme == 'dark'))
    new_theme = 'dark' if mode else 'light'
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()
    
    st.divider()
    
    # 路径配置
    st.markdown("#### 📂 WPT 环境")
    project_wpt_path = str(Path(__file__).parent.parent / "wpt")
    wpt_root = st.text_input("仓库根目录", 
                            value=os.getenv("WPT_ROOT", project_wpt_path),
                            label_visibility="collapsed")
    st.caption("脚本将自动同步至 `/local_test/` 目录")
    
    # 自动管理 Server
    if os.path.exists(wpt_root):
        if server_manager.start(wpt_root):
            st.success("🟢 服务运行中 (端口:8000)")
        else:
            st.error("🔴 服务启动失败")
    else:
        st.warning("⚠️ 无效的 WPT 路径")

    # API 配置
    st.divider()
    with st.expander("🔑 API 访问凭据"):
        api_key = st.text_input("API 密钥", value=os.getenv("OPENAI_API_KEY", ""), type="password")
        base_url = st.text_input("接口地址", value=os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"))
        model_name = st.text_input("模型名称", value="gemini-2.0-flash")

# --- 6. 主界面：输入区 ---
st.markdown(f"<h1 style='text-align: center;'>WPT Studio <span style='color:{curr['primary']}'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: {curr['sub_text']}; margin-top: -15px;'>专业级 Web 平台测试脚本自动化工作站</p>", unsafe_allow_html=True)

st.write("")

# 需求输入
demand = st.text_area("您的测试目标是什么？", 
                     placeholder="例如：验证 Geolocation API 在用户拒绝权限时的错误处理逻辑...", 
                     height=140,
                     label_visibility="collapsed")

# 标签与按钮
col_tag, col_go = st.columns([4, 1])
with col_tag:
    feature = st.text_input("特性标签", placeholder="例如: geolocation, css-grid...", label_visibility="collapsed")
with col_go:
    generate_btn = st.button("🚀 生成脚本", type="primary", use_container_width=True)

# 初始化 Session State
if 'code' not in st.session_state: st.session_state.code = ""
if 'filename' not in st.session_state: st.session_state.filename = "test.html"

# 生成逻辑
if generate_btn:
    if not demand: st.toast("请输入需求描述", icon="⚠️")
    elif not api_key: st.error("API 密钥未配置，请在侧边栏设置")
    else:
        with st.status("🏗️ 正在编排脚本...", expanded=False) as status:
            try:
                result = generate_wpt_code(demand, feature, api_key, base_url, model_name)
                st.session_state.code = result.get("content", "")
                raw_filename = os.path.basename(result.get("filename", "test.html"))
                name_part, ext_part = os.path.splitext(raw_filename)
                st.session_state.filename = f"{name_part}_{time.strftime('%H%M%S')}{ext_part}"
                status.update(label="✅ 生成成功", state="complete")
                st.balloons()
            except Exception as e:
                status.update(label="❌ 生成失败", state="error")
                st.error(str(e))

# --- 7. 沉浸式工作台 ---
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
                st.toast("已同步至 WPT 目录", icon="✅")
            except Exception as e:
                st.error(f"同步失败: {e}")
                
    with t_col3:
        # 使用 localhost 替代 web-platform.test
        wpt_url = f"http://localhost:8000/local_test/{st.session_state.filename}"
        st.link_button("🌐 运行预览", wpt_url, type="primary", use_container_width=True)
    
    with t_col4:
        if st.button("🧹 重置工作台", use_container_width=True):
            st.session_state.code = ""
            st.rerun()

    # 沉浸式编辑器
    edited_code = st.text_area(
        "编辑器",
        value=st.session_state.code,
        height=600,
        label_visibility="collapsed",
        key="editor_main"
    )
    st.session_state.code = edited_code

st.write("")
st.write("")
st.markdown(f"<p style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>WPT Studio Pro v4.5 | 下一代测试流自动化</p>", unsafe_allow_html=True)

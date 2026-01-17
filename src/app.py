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
            # 基础环境检查
            if not os.path.exists(root_path):
                return False
                
            # 如果路径没变且进程正在运行，则无需重复启动
            if self.process and self.current_root == root_path:
                if self.process.poll() is None:
                    return True
            
            self.stop()
            
            try:
                # 启动 http.server
                # 仅在 Unix 系统支持 os.setsid
                preexec = None
                if os.name != 'nt':
                    preexec = os.setsid
                    
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
    # 注册退出时的清理钩子
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
if 'env_mode' not in st.session_state:
    st.session_state.env_mode = '本地开发'

# --- 3. 侧边栏：环境切换与配置 ---
with st.sidebar:
    st.title("🧪 WPT Studio Pro")
    st.markdown("---")
    
    # 环境模式切换
    st.session_state.env_mode = st.radio(
        "选择运行环境",
        ["本地开发", "云端部署"],
        help="本地模式支持自动开启 Server 并同步文件；云端模式仅提供生成与下载。"
    )
    
    st.divider()
    
    # 路径配置逻辑
    st.markdown("#### 📂 WPT 仓库路径")
    # 自动定位项目内的 wpt 目录
    base_dir = Path(__file__).parent.parent
    project_wpt_path = str(base_dir / "wpt")
    
    if st.session_state.env_mode == "本地开发":
        wpt_root = st.text_input("本地 WPT 根目录", value=project_wpt_path)
        if os.path.exists(wpt_root):
            if server_manager.start(wpt_root):
                st.success("🟢 本地 Server 已开启 (8000)")
            else:
                st.error("🔴 Server 启动失败")
        else:
            st.warning("⚠️ 请输入有效的本地路径")
    else:
        st.info("☁️ 云端模式：禁用后台进程启动")
        wpt_root = project_wpt_path
        st.caption(f"预设路径: `{wpt_root}`")

    # 主题切换
    st.divider()
    st.markdown("#### 🌗 界面外观")
    mode = st.toggle("深色模式", value=(st.session_state.theme == 'dark'))
    st.session_state.theme = 'dark' if mode else 'light'

    # API 配置
    with st.expander("🔑 API 访问凭据"):
        api_key = st.text_input("API KEY", value=os.getenv("OPENAI_API_KEY", ""), type="password")
        base_url = st.text_input("Base URL", value=os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"))
        model_name = st.text_input("模型名称", value="gemini-2.0-flash")

# --- 4. 动态风格注入 ---
curr = {
    'light': {'bg': '#FFFFFF', 'sidebar': '#F1F5F9', 'text': '#1E293B', 'sub_text': '#64748B', 'primary': '#2563EB', 'border': '#E2E8F0', 'input_bg': '#FFFFFF'},
    'dark': {'bg': '#0F172A', 'sidebar': '#020617', 'text': '#F1F5F9', 'sub_text': '#94A3B8', 'primary': '#3B82F6', 'border': '#334155', 'input_bg': '#1E293B'}
}[st.session_state.theme]

st.markdown(f"""
    <style>
    .stApp {{ background-color: {curr['bg']}; color: {curr['text']}; }}
    [data-testid="stSidebar"] {{ background-color: {curr['sidebar']} !important; border-right: 1px solid {curr['border']} !important; }}
    [data-testid="stSidebar"] * {{ color: {curr['text']} !important; }}
    header[data-testid="stHeader"] {{ background-color: {curr['bg']} !important; border-bottom: 1px solid {curr['border']} !important; }}
    header[data-testid="stHeader"] * {{ color: {curr['text']} !important; }}
    .stTextArea textarea, .stTextInput input {{ color: {curr['text']} !important; background-color: {curr['input_bg']} !important; border: 1px solid {curr['border']} !important; border-radius: 12px !important; padding: 1rem !important; }}
    ::placeholder {{ color: {curr['sub_text']} !important; opacity: 0.5; }}
    div.stButton > button {{ border-radius: 12px !important; font-weight: 600 !important; transition: all 0.2s; }}
    div.stButton > button[kind="primary"] {{ background-color: {curr['primary']} !important; color: white !important; border: none !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. 主界面 ---
st.markdown(f"<h1 style='text-align: center;'>WPT Studio <span style='color:{curr['primary']}'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: {curr['sub_text']}; margin-top: -15px;'>工业级 Web platform 测试脚本自动化工作站 (v5.0)</p>", unsafe_allow_html=True)

st.write("")

# 需求输入
demand = st.text_area("您的测试目标是什么？", placeholder="描述您想测试的 Web 特性...", height=120, label_visibility="collapsed")

col_tag, col_go = st.columns([4, 1])
with col_tag:
    feature = st.text_input("特性标签", placeholder="特性标签 (如: geolocation, css-grid...)", label_visibility="collapsed")
with col_go:
    generate_btn = st.button("🚀 开始构建", type="primary", use_container_width=True)

if 'code' not in st.session_state: st.session_state.code = ""
if 'filename' not in st.session_state: st.session_state.filename = "test.html"

# 生成逻辑
if generate_btn:
    if not demand: st.toast("请输入需求描述", icon="⚠️")
    elif not api_key: st.error("API 密钥未配置")
    else:
        with st.status("🏗️ 正在编排脚本...", expanded=False) as status:
            try:
                result = generate_wpt_code(demand, feature, api_key, base_url, model_name)
                st.session_state.code = result.get("content", "")
                raw_filename = os.path.basename(result.get("filename", "test.html"))
                st.session_state.filename = f"{os.path.splitext(raw_filename)[0]}_{time.strftime('%H%M%S')}.html"
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
        if st.button("💾 同步至仓库", use_container_width=True):
            try:
                target_dir = Path(wpt_root) / "local_test"
                target_dir.mkdir(parents=True, exist_ok=True)
                (target_dir / st.session_state.filename).write_text(st.session_state.code, encoding="utf-8")
                st.toast("已成功写入 local_test/", icon="✅")
            except Exception as e:
                st.error(f"写入失败 (可能环境受限): {e}")
                
    with t_col3:
        if st.session_state.env_mode == "本地开发":
            wpt_url = f"http://localhost:8000/local_test/{st.session_state.filename}"
            st.link_button("🌐 测试运行", wpt_url, type="primary", use_container_width=True)
        else:
            st.button("🌐 预览受限", disabled=True, use_container_width=True, help="云端环境不支持访问本地 localhost 端口")
    
    with t_col4:
        if st.button("🧹 重置", use_container_width=True):
            st.session_state.code = ""
            st.rerun()

    st.session_state.code = st.text_area("编辑器", value=st.session_state.code, height=600, label_visibility="collapsed")

st.markdown(f"<p style='text-align: center; color: #94a3b8; font-size: 0.8rem; padding-top: 30px;'>WPT Studio Pro v5.0 | {st.session_state.env_mode}模式</p>", unsafe_allow_html=True)

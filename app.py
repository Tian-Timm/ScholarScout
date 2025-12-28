import streamlit as st
import pandas as pd
import datetime
import os
import subprocess
import sys

# === Playwright Installation for Streamlit Cloud ===
@st.cache_resource
def install_playwright_browsers():
    print("⬇️ Installing Playwright browsers...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("✅ Playwright browsers installed.")
    except Exception as e:
        print(f"❌ Failed to install Playwright browsers: {e}")

# Run installation once
install_playwright_browsers()

# 引入你的后端函数
from main import process_faculty_url 

# === 0. 多语言配置 (Localization) ===
LANG = {
    "English": {
        "title": "🎓 ScholarScout: Faculty Research Extractor",
        "sidebar_config": "⚙️ Configuration",
        "api_keys": "🔑 API Credentials",
        "api_expander": "API Keys Configuration",
        "api_info": "These keys are required to run the scraper. They are not stored permanently.",
        "deepseek_label": "DeepSeek API Key (Required)",
        "s2_label": "Semantic Scholar API Key (Optional)",
        "target_url": "Target URL",
        "target_url_help": "Enter the URL of the faculty directory page.",
        "uni_name": "University Name",
        "uni_name_help": "Enter the full name of the university for verification.",
        "start_btn": "🚀 Start Scraping",
        "error_api": "❌ DeepSeek API Key is required! Please enter it in the sidebar.",
        "error_fields": "❌ Please fill in both Target URL and University Name!",
        "status_working": "🕵️ ScholarScout is working...",
        "status_init": "1️⃣ Initializing scraper...",
        "status_scraping": "2️⃣ Scraping from: {}",
        "status_processing": "3️⃣ Received {} records. Processing...",
        "status_empty": "⚠️ No faculty members found.",
        "status_reading": "3️⃣ Reading generated file...",
        "status_complete": "✅ Mission Complete!",
        "status_failed": "❌ Execution Failed",
        "save_msg": "💾 Saving temporary file: {}...",
        "metrics_total": "Total Faculty",
        "metrics_s2": "S2 Verified",
        "metrics_web": "Web/Other",
        "data_preview": "📊 Data Preview",
        "download_btn": "📥 Download Excel Report",
    },
    "中文": {
        "title": "🎓 ScholarScout: 教授科研方向提取工具",
        "sidebar_config": "⚙️ 配置选项",
        "api_keys": "🔑 API 凭证",
        "api_expander": "API Key 配置",
        "api_info": "运行爬虫需要 API Key，它们仅临时使用，不会被永久保存。",
        "deepseek_label": "DeepSeek API Key (必填)",
        "s2_label": "Semantic Scholar API Key (选填)",
        "target_url": "目标网址 (Target URL)",
        "target_url_help": "输入学院教职人员列表页面的网址。",
        "uni_name": "大学全名 (University Name)",
        "uni_name_help": "输入大学英文全名，用于学术数据库核验。",
        "start_btn": "🚀 开始采集",
        "error_api": "❌ 必须填写 DeepSeek API Key！请在侧边栏输入。",
        "error_fields": "❌ 请同时填写目标网址和大学名称！",
        "status_working": "🕵️ ScholarScout 正在运行...",
        "status_init": "1️⃣ 正在初始化爬虫...",
        "status_scraping": "2️⃣ 正在抓取: {}...",
        "status_processing": "3️⃣ 已获取 {} 条记录，正在进行智能分析...",
        "status_empty": "⚠️ 未找到任何教职人员。",
        "status_reading": "3️⃣ 正在读取生成的文件...",
        "status_complete": "✅ 任务完成！",
        "status_failed": "❌ 执行失败",
        "save_msg": "💾 正在保存临时文件: {}...",
        "metrics_total": "教师总数",
        "metrics_s2": "学术库验证",
        "metrics_web": "网页提取",
        "data_preview": "📊 数据预览",
        "download_btn": "📥 下载 Excel 报告",
    }
}

# === 1. 页面基础配置 ===
st.set_page_config(
    page_title="ScholarScout Dashboard",
    page_icon="🎓",
    layout="wide"
)

# 语言选择器放在侧边栏最上方
with st.sidebar:
    selected_lang = st.radio("Language / 语言", ["English", "中文"])
    T = LANG[selected_lang]

st.title(T["title"])

# === 2. 侧边栏配置 (继续) ===
with st.sidebar:
    st.header(T["api_keys"])
    
    with st.expander(T["api_expander"], expanded=True):
        st.info(T["api_info"])
        
        deepseek_key = st.text_input(
            T["deepseek_label"],
            type="password",
            help="Get it from https://platform.deepseek.com/",
            placeholder="sk-..."
        )
        
        s2_key = st.text_input(
            T["s2_label"],
            type="password",
            help="Get it from https://www.semanticscholar.org/product/api.",
            placeholder="Optional"
        )

    st.divider()

    st.header(T["sidebar_config"])
    with st.form("config_form"):
        target_url = st.text_input(
            T["target_url"], 
            placeholder="https://hci.cs.wisc.edu/",
            help=T["target_url_help"]
        )
        uni_name = st.text_input(
            T["uni_name"], 
            placeholder="University of Wisconsin-Madison",
            help=T["uni_name_help"]
        )
        submitted = st.form_submit_button(T["start_btn"])

# === 3. 核心逻辑 ===
# 初始化状态
if 'df_result' not in st.session_state:
    st.session_state.df_result = None
if 'csv_path' not in st.session_state:
    st.session_state.csv_path = None

if submitted:
    # 0. 验证 API Key
    if not deepseek_key:
        st.error(T["error_api"])
    elif not target_url or not uni_name:
        st.error(T["error_fields"])
    else:
        # 设置环境变量供后端使用
        os.environ["DEEPSEEK_API_KEY"] = deepseek_key
        if s2_key:
            os.environ["S2_API_KEY"] = s2_key
        # 清除可能存在的旧环境变量（如果用户清空了输入框）
        elif "S2_API_KEY" in os.environ:
            del os.environ["S2_API_KEY"]

        # 重置状态
        st.session_state.df_result = None
        st.session_state.csv_path = None
        
        with st.status(T["status_working"], expanded=True) as status:
            try:
                st.write(T["status_init"])
                st.write(T["status_scraping"].format(uni_name))
                
                # --- 调用后端 (传递语言参数) ---
                # 这里的 result 极大概率是一个 List (列表)
                # Pass 'en' for English, 'zh' for Chinese
                lang_code = "en" if selected_lang == "English" else "zh"
                result = process_faculty_url(target_url, uni_name, language=lang_code)
                
                final_df = None
                final_filename = ""

                # === 🚑 智能处理逻辑 (修复核心) ===
                
                # 情况 A: 后端直接返回了数据列表 (你的现状)
                if isinstance(result, list):
                    st.write(T["status_processing"].format(len(result)))
                    
                    if not result:
                        st.warning(T["status_empty"])
                        status.update(label="⚠️ Finished but empty", state="error")
                    else:
                        # 1. 把列表转为 DataFrame
                        final_df = pd.DataFrame(result)
                        
                        # 2. 前端自己生成文件名
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
                        safe_uni_name = "".join([c if c.isalnum() else "_" for c in uni_name])
                        final_filename = f"{safe_uni_name}_{timestamp}.xlsx"
                        
                        # 3. 保存文件 (以便下载)
                        st.write(T["save_msg"].format(final_filename))
                        final_df.to_excel(final_filename, index=False)
                
                # 情况 B: 后端返回了文件名 (以防万一你以后改了后端)
                elif isinstance(result, str):
                    st.write(T["status_reading"])
                    final_filename = result
                    final_df = pd.read_excel(result)
                
                else:
                    st.error(f"Unknown return type: {type(result)}")

                # === 处理完成 ===
                
                if final_df is not None and not final_df.empty:
                    # 更新 Session State，强制刷新页面显示
                    st.session_state.df_result = final_df
                    st.session_state.csv_path = final_filename
                    status.update(label=T["status_complete"], state="complete", expanded=False)
                
            except Exception as e:
                status.update(label=T["status_failed"], state="error")
                st.error(f"An error occurred: {str(e)}")

# === 4. 结果展示区 ===
if st.session_state.df_result is not None:
    df = st.session_state.df_result
    
    st.divider()
    
    # 指标卡片
    col1, col2, col3 = st.columns(3)
    col1.metric(T["metrics_total"], len(df))
    
    # 尝试统计验证状态
    if 'Data_Source' in df.columns:
        s2_count = len(df[df['Data_Source'] == 'S2_Verified'])
        web_count = len(df[df['Data_Source'] == 'Web_Bio'])
    else:
        s2_count = 0
        web_count = len(df)
        
    col2.metric(T["metrics_s2"], s2_count)
    col3.metric(T["metrics_web"], web_count)
    
    # 数据表
    st.subheader(T["data_preview"])
    st.dataframe(df, use_container_width=True)
    
    # 下载按钮
    if st.session_state.csv_path and os.path.exists(st.session_state.csv_path):
        with open(st.session_state.csv_path, "rb") as file:
            st.download_button(
                label=T["download_btn"],
                data=file,
                file_name=st.session_state.csv_path,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
# 🎓 ScholarScout

ScholarScout 是一个基于 AI 的大学教授信息采集与研究方向自动总结工具。

## ✨ 功能特点
- **自动采集**: 输入学院 URL，自动抓取教授列表。
- **智能验证**: 利用 Semantic Scholar 数据库验证教授身份，排除重名干扰。
- **AI 总结**: 使用 DeepSeek 大模型自动总结教授的研究方向。
- **Excel 导出**: 一键下载整理好的 Excel 报表。

## 🚀 如何运行
1. 输入 **DeepSeek API Key** (必需)。
2. 输入目标学院的 **Faculty List URL** 和 **大学名称**。
3. 点击 **Start Scraping**。

## 🛠️ 技术栈
- Streamlit (Web 界面)
- ScrapeGraphAI (智能爬虫)
- Semantic Scholar API (学术数据)
- DeepSeek LLM (文本总结)
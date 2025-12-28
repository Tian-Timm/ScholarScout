<<<<<<< HEAD
# 🎓 ScholarScout  
**AI-powered Faculty Intelligence & Academic Profiling Tool**  
**基于 AI 的高校教师信息采集与研究画像工具**

🔗 **Live Demo / 在线体验**  
👉 https://scholarscout-forphd.streamlit.app/

---

## 📌 项目简介 | Overview

**ScholarScout** 是一个基于 AI 的学术数据采集与清洗工具，  
用于从高校官网中提取教师信息，并自动构建其 **研究方向画像（Research Profiles）**。

与追求“全自动”的工具不同，ScholarScout 的核心目标是 **高置信度（High Confidence）输出**：

- 通过多重验证机制  
- 最大限度减少 **重名、错配、学术幻觉**  
- 最终交付 **可快速人工确认的结构化结果**

---

**ScholarScout** is an AI-powered academic data extraction and enrichment tool designed to collect faculty information from university websites and generate reliable research profiles.

Rather than chasing full automation, ScholarScout prioritizes **high-confidence outputs** by combining deterministic rules, academic databases, and LLM reasoning—delivering results that are **fast to review and easy to trust**.

---

## ✨ 功能特点 | Key Features

### 🔹 自动采集 | Automated Faculty Scraping
- 输入学院 **Faculty List URL**
- 自动抓取：
  - 教授姓名
  - 职称 / Title
  - 个人主页链接

Input a faculty directory URL to automatically extract faculty names, titles, and profile links.

---

### 🔹 智能身份验证 | Identity Verification
- 基于 **Semantic Scholar** 学术数据库
- 多轮搜索 + 裁判逻辑
- 显著降低 **同名异人（Name Ambiguity）** 风险

Verify faculty identities using Semantic Scholar with multi-stage matching and re-verification logic.

---

### 🔹 AI 研究方向总结 | AI-powered Research Profiling
- 使用 **DeepSeek 大模型**
- 自动生成：
  - 中文研究方向摘要
  - 近年代表性论文列表

Generate concise Chinese research summaries and representative publications using DeepSeek LLM.

---

### 🔹 Excel 一键交付 | One-click Excel Export
- 自动生成结构化 Excel 报表
- 内置 **置信度标记**
- 支持人工快速复核与筛选

Export a clean, structured Excel file with confidence labels for fast manual review.

---

## 🚀 使用方式 | How to Use

**中文**
1. 配置 **DeepSeek API Key**（必需）
2. 输入目标学院的 Faculty List URL 与大学名称
3. 点击 **Start Scraping**，等待系统生成结果

**English**
1. Provide your **DeepSeek API Key** (required)
2. Enter the target Faculty List URL and University Name
3. Click **Start Scraping** to generate results

---

## 🛠️ 技术栈 | Tech Stack

- **Streamlit** – Web UI  
- **ScrapeGraphAI** – LLM-powered scraping framework  
- **Semantic Scholar API** – Academic metadata source  
- **DeepSeek LLM** – Research summarization & reasoning  

---

## ⚠️ 设计理念 | Design Philosophy

- ❌ 不追求 100% 全自动  
- ✅ 优先保证 **数据准确性 & 可解释性**  
- 🤝 **人机协同**：AI 负责 90%，人类确认最后 10%

---

- ❌ Not fully automated by design  
- ✅ Accuracy and interpretability over speed  
- 🤝 Human-in-the-loop for final validation
=======
🎓 ScholarScout
<p align="center"> <strong>AI-powered Faculty Intelligence & Academic Profiling Tool</strong>

AI-powered Faculty Intelligence & Academic Profiling Tool
基于 AI 的高校教师信息采集与研究画像工具

📌 项目简介 | Overview

ScholarScout 是一个基于 AI 的学术数据采集与清洗工具，用于从高校官网中提取教授信息，并自动构建其研究方向画像。

ScholarScout 的核心目标不是“全自动”，而是 高置信度（High Confidence）：
通过多重验证机制，最大限度减少重名、错配和学术幻觉问题，最终交付 可人工快速确认的结构化结果。

ScholarScout is an AI-powered academic data extraction and enrichment tool designed to collect faculty information from university websites and automatically generate reliable research profiles.

Instead of pursuing full automation, ScholarScout focuses on high-confidence outputs by combining deterministic rules, academic databases, and LLM reasoning—delivering results that are fast to review and easy to trust.

✨ 功能特点 | Key Features
🔹 自动采集 | Automated Faculty Scraping

输入学院 Faculty List URL

自动抓取教授姓名、头衔、个人主页链接等基础信息

Input a faculty directory URL and automatically extract faculty names, titles, and profile links.

🔹 智能身份验证 | Identity Verification

基于 Semantic Scholar 学术数据库

通过多重搜索与裁判逻辑，降低同名异人风险

Verify faculty identities using Semantic Scholar with multi-stage matching and re-verification logic to reduce name ambiguity.

🔹 AI 研究方向总结 | AI-powered Research Profiling

使用 DeepSeek 大模型

自动生成中文研究方向摘要

提取近年代表性论文

Generate concise research summaries and representative publications using DeepSeek LLM.

🔹 Excel 一键交付 | Excel Export

自动生成结构化 Excel 报表

包含置信度标记，支持人工快速复核

Export a clean, structured Excel file with confidence labels for fast manual review.


🚀 使用方式 | How to Run

配置 DeepSeek API Key（必需）

输入目标学院的 Faculty List URL 和 大学名称

点击 Start Scraping，等待系统生成结果

Provide your DeepSeek API Key (required)

Enter the target Faculty List URL and University Name

Click Start Scraping to generate results


🛠️ 技术栈 | Tech Stack

Streamlit – Web UI

ScrapeGraphAI – LLM-powered scraping framework

Semantic Scholar API – Academic metadata source

DeepSeek LLM – Research summarization & reasoning


⚠️ 设计理念 | Design Philosophy

❌ 不追求 100% 全自动

✅ 优先保证数据准确性与可解释性

🤝 人机协同：AI 负责 90%，人类确认最后 10%

❌ Not fully automated by design

✅ Accuracy and interpretability over speed

🤝 Human-in-the-loop for final validation
>>>>>>> 266857b521280d63a61109f173c146cbb021ac11

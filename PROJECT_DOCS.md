# 项目技术文档：核心逻辑与问题分析

本文档详细说明了 **ScholarScout** 项目中“教师个人主页抓取”与“近期研究获取”两大核心模块的实现逻辑，并重点分析了当前出现“Profile Link 错误”导致“研究匹配失败”的连锁反应机制。

## 1. 核心模块：教师列表与 Profile Link 抓取 (`scraper.py`)

### 1.1 实现逻辑
该模块负责从系所 Directory 页面提取教师的基本信息（姓名、职称、个人主页链接）。

1.  **获取 (Fetching)**
    *   **代码**: `requests.get(url, headers=...)`
    *   **机制**: 使用 Python 标准 HTTP 库获取页面的 **静态 HTML 源码**。
    *   **局限**: 无法执行页面上的 JavaScript 代码。如果页面是单页应用 (SPA) 或依赖 JS 渲染列表，获取到的源码可能为空或不完整。

2.  **清洗 (Cleaning)**
    *   **代码**: `utils.clean_html(html_content)`
    *   **机制**: 将 HTML 转换为 Markdown 格式的纯文本。
        *   关键转换：将 `<a href="/people/john">John</a>` 转换为文本 `John (/people/john)`。
        *   目的：让 LLM 能在纯文本中“看到”链接与姓名的对应关系。

3.  **提取 (Extraction)**
    *   **代码**: `SmartScraperGraph` + `DeepSeek`
    *   **机制**: 将清洗后的文本输入 LLM，Prompt 要求提取 JSON 列表。
    *   **Prompt 策略**: 强制要求返回 `[{"name": "...", "profile_link": "..."}]` 格式。

4.  **后处理 (Post-processing)**
    *   **代码**: `urljoin(base_url, link)`
    *   **机制**: 针对提取出的相对路径（如 `/faculty/smith`），自动拼接 Base URL 生成绝对路径。

### 1.2 问题分析：为什么 Profile Link 会错？
目前观察到 Profile Link 经常错误（如无效链接、文字代替链接），主要原因如下：

*   **动态渲染问题 (最常见)**:
    *   目标网站（如 BYU CS）可能使用 JavaScript 动态加载教师卡片。`requests` 只能拿到初始 HTML 骨架，其中可能只有按钮文字（如 "View Profile"）而没有实际的 `href` 属性。
    *   **后果**: 清洗后的文本中只有名字和 "View Profile" 字样，没有 URL。LLM 被迫“幻觉”编造一个链接，或者提取失败。
*   **清洗丢失**:
    *   如果 HTML 结构复杂，`clean_html` 可能没能正确地将 `href` 保留在姓名旁边，导致 LLM 无法将链接与人名关联。

---

## 2. 核心模块：近期研究获取与身份匹配 (`s2_client.py`)

### 2.1 实现逻辑：三阶段搜索策略
该模块负责在 Semantic Scholar (S2) 数据库中找到对应的作者。为了解决重名问题（Homonyms），采用了“漏斗式”的三阶段搜索。

*   **阶段 1: 姓名 + 学校精准匹配 (Strict Match)**
    *   **Query**: `"{Name} {University}"`
    *   **判断**: 如果 S2 返回结果，且结果中的 `affiliations` 字段包含学校名称关键词。
    *   **结果**: 命中则直接采用 (Confidence: High)。

*   **阶段 2: 姓名 + 研究领域关键词匹配 (Keyword Assisted)**
    *   **依赖**: **必须拥有正确的 Profile Link**。
    *   **流程**:
        1.  访问 Profile Link（由模块 1 提供）。
        2.  抓取个人简介，LLM 提取一个核心关键词（如 "Computer Vision"）。
        3.  **Query**: `"{Name} {Keyword}"`。
    *   **原理**: 即使学校名字在 S2 数据库中没写全，加上具体的研究领域通常能唯一确定一名学者。

*   **阶段 3: 纯姓名兜底 (Name Only Fallback)**
    *   **触发条件**: 阶段 1 和 阶段 2 均失败。
    *   **Query**: `"{Name}"`
    *   **流程**: 获取前 5-10 名同名学者，按引用量或名字相似度排序。
    *   **风险**: 极高。对于常见名（如 "Wei Wang", "James Smith"），S2 可能会返回一位高引用的物理学家，而不是我们要找的 CS 教授。

### 2.2 问题分析：为什么研究匹配会失败？
这是一个典型的**级联故障 (Cascading Failure)**。

1.  **源头错误**: 模块 1 未能正确抓取 Profile Link（或者是错误的链接）。
2.  **阶段 2 失效**:
    *   系统尝试访问错误的链接 -> 页面 404 或内容为空。
    *   无法提取“研究领域关键词”。
    *   阶段 2 (Keyword Search) 被迫跳过。
3.  **被迫进入阶段 3**:
    *   系统只能使用纯姓名搜索。
    *   对于常见名字，系统无法区分“本校的 John Doe”和“外校的 John Doe”。
    *   **结果**: 经常抓取到同名的其他学者，导致“Recent Studies”显示的是完全不相关的论文。

---

## 3. 解决方案建议 (Roadmap)

### 针对 Profile Link 错误的修复
1.  **引入 Headless Browser**: 
    *   放弃 `requests`，改用 `Playwright` 或 `Selenium`。
    *   **作用**: 能执行 JavaScript，等待页面渲染完成后再提取 HTML，确保能拿到真实的 `href`。
2.  **增强 Prompt**:
    *   明确指示 LLM 如果找不到链接，返回 `null`，而不是编造。

### 针对研究匹配失败的修复
1.  **Google Search 补救**:
    *   如果在 S2 搜不到，先用 Google Search API 搜 `"{Name} {University} Semantic Scholar"`，通常能直接找到 S2 的 Profile ID。
2.  **论文标题反向验证**:
    *   如果 Profile 页面有论文列表，先提取 1-2 篇论文标题。
    *   在 S2 中搜索“论文标题”而不是“人名”，这是唯一确定作者的最强手段。


## 1. Project Overview
**ScholarScout** is an intelligent faculty verification system...
[...truncated for brevity...]
## 5. Verification & Ground Truth
**"How do we know the LLM is right?"**
...
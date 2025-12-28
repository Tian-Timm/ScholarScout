import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_client():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DeepSeek API Key not found. Please set it in the sidebar.")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

def summarize_from_papers(papers: list, name: str | None = None, language: str = "zh") -> str:
    titles = []
    abstracts = []
    for p in papers or []:
        t = p.get("title")
        if t:
            titles.append(t)
        tl = p.get("tldr")
        if isinstance(tl, dict):
            abstracts.append(tl.get("text"))
        elif isinstance(tl, str):
            abstracts.append(tl)
    content = {
        "name": name or "",
        "titles": titles,
        "abstracts": [a for a in abstracts if a]
    }
    
    if language == "zh":
        prompt = (
            f"基于以下论文标题和摘要（Paper Titles and Abstracts），总结教授 {content['name']} 的研究方向。\n"
            "请使用简体中文（Simplified Chinese），以第三人称撰写一段约 100-150 字的学术简介。\n"
            "重点概括其核心研究领域和技术兴趣。保持专业学术风格，避免翻译腔，保留必要的英文专有名词。\n\n"
            f"Titles: {content['titles']}\nAbstracts: {content['abstracts']}"
        )
    else:
        prompt = (
            f"Based on the following paper titles and abstracts, summarize the research direction of Professor {content['name']}.\n"
            "Please write a professional academic biography (about 100-150 words) in English in the third person.\n"
            "Focus on summarizing their core research areas and technical interests. Maintain a professional academic tone.\n\n"
            f"Titles: {content['titles']}\nAbstracts: {content['abstracts']}"
        )
    
    try:
        client = get_client()
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a professional academic research assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return ""

def summarize_from_bio(bio_text: str, name: str | None = None, language: str = "zh") -> str:
    if language == "zh":
        prompt = (
            f"基于以下英文个人简介（Biography）文本，总结教授 {name or ''} 的研究方向。\n"
            "请使用简体中文（Simplified Chinese），以第三人称撰写一段约 100-150 字的学术简介。\n"
            "去除客套话，专注于学术贡献和研究领域。保持专业学术风格，避免翻译腔，保留必要的英文专有名词。\n\n"
            f"Bio Text: {bio_text or ''}"
        )
    else:
        prompt = (
            f"Based on the following biography text, summarize the research direction of Professor {name or ''}.\n"
            "Please write a professional academic biography (about 100-150 words) in English in the third person.\n"
            "Remove polite filler words and focus on academic contributions and research areas. Maintain a professional academic tone.\n\n"
            f"Bio Text: {bio_text or ''}"
        )
        
    try:
        client = get_client()
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a professional academic research assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return ""

import os, logging, json, re
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI
from .moderate import moderate_post

load_dotenv()

def _client():
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def call_gpt(system:str, user:str)->str:
    client = _client()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
        temperature=0.3,
    )
    return resp.choices[0].message.content

def make_article(item:Dict)->Dict:
    system = "Bạn là biên tập viên cẩn trọng. Tóm tắt có trích dẫn URL gốc. Không bịa."
    user = f"""Tạo bài viết 500–800 từ bằng tiếng Việt dựa trên nguồn sau:
- Title: {item['title']}
- Source URL: {item['url']}
- Extracted text (truncated):
{item['text'][:4000]}

Yêu cầu:
1) Tiêu đề ngắn
2) Tóm tắt 50 từ
3) Nội dung 3–5 mục, có dẫn nguồn (URL)
4) Bullet các dữ kiện chính + URL nguồn
5) SEO meta (title <= 60 ký tự, description <= 150)
"""
    content = call_gpt(system, user)
    title = content.splitlines()[0].strip()[:120] if content else (item.get("title") or "Bài tổng hợp")
    post = {"type":"article","title": title, "content":content, "source_url": item["url"]}
    # Safety moderation
    mod = moderate_post(post)
    post["moderation"] = mod
    # Safe mode: pending/draft only
    if mod.get("decision") == "BLOCK":
        post["status"] = "draft"
    else:
        post["status"] = "pending"
    return post

def generate_all(items:List[Dict])->List[Dict]:
    posts = []
    for it in items[:20]:
        try:
            posts.append(make_article(it))
        except Exception as ex:
            logging.warning(f"Gen skip {it.get('url')}: {ex}")
    return posts

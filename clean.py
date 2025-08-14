import os, json, re, logging
from typing import List, Dict
from bs4 import BeautifulSoup
from pathlib import Path

def html_to_text(html:str)->str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script","style","noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text[:100000]

def normalize(raw:dict)->dict:
    title = raw.get("meta",{}).get("title")
    text = html_to_text(raw["content"])
    if not title:
        title = text[:80]
    return {
        "url": raw["url"],
        "title": title,
        "text": text,
        "published": raw.get("meta",{}).get("published")
    }

def clean_all(paths:List[str])->List[Dict]:
    out = []
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                raw = json.load(f)
            out.append(normalize(raw))
        except Exception as ex:
            logging.warning(f"Clean skip {p}: {ex}")
    return out

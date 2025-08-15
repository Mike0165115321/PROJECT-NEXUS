# manage_news.py
# (V3 - RAG Index Builder for News - Complete Code)
# หน้าที่: ดึงข่าว, ขูดเนื้อหาเต็ม, และสร้าง FAISS Index + Mapping file

import feedparser
import requests
import faiss
import json
import os
import time
import torch
import datetime
from newspaper import Article
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from core.config import settings

# --- 1. การตั้งค่า ---
NEWS_INDEX_DIR = "data/news_index"
NEWS_FAISS_PATH = os.path.join(NEWS_INDEX_DIR, "news_faiss.index")
NEWS_MAPPING_PATH = os.path.join(NEWS_INDEX_DIR, "news_mapping.json")

NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
RSS_FEEDS = {
    "Reuters Tech": "https://www.reuters.com/pf/api/v2/content/corp/rss/US/technology-news-idUSKBN0P204J20150622",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Wired Top Stories": "https://www.wired.com/feed/rss",
    "Ars Technica": "http://feeds.arstechnica.com/arstechnica/index/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "MIT Technology Review": "https://www.technologyreview.com/feed/",
    "Reuters Business": "https://www.reuters.com/pf/api/v2/content/corp/rss/US/business-news-idUSKBN0P002020150615",
    "Bloomberg Markets": "https://feeds.bloomberg.com/markets/news.rss",
    "The Economist": "https://www.economist.com/finance-and-economics/rss.xml",
    "Harvard Business Review": "https://hbr.org/rss/topic/latest",
    "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Associated Press (AP)": "https://apnews.com/hub/ap-top-news/rss.xml",
    "Thai PBS": "https://www.thaipbs.or.th/rss/news.xml",
    "Thairath": "https://www.thairath.co.th/rss/news.xml"
}

# --- 2. ฟังก์ชันดึงและขูดข้อมูล ---
def fetch_from_newsapi() -> List[Dict]:
    print("📰 Fetching news from NewsAPI.org...")
    if not settings.NEWS_KEY:
        print("  - ⚠️ NewsAPI key not found in .env file.")
        return []
    
    params = {'country': 'us', 'pageSize': 20, 'apiKey': settings.NEWS_KEY}
    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=15)
        response.raise_for_status()
        articles = response.json().get('articles', [])
        print(f"  - Fetched {len(articles)} articles from NewsAPI.")
        return [{
            "published_at": a.get("publishedAt"),
            "source_name": a.get("source", {}).get("name"),
            "title": a.get("title"),
            "description": a.get("description"),
            "url": a.get("url")
        } for a in articles]
    except Exception as e:
        print(f"  - ❌ NewsAPI Error: {e}")
        return []

def fetch_from_rss(url: str, source: str) -> List[Dict]:
    """ดึงข่าวจากแหล่ง RSS Feed"""
    print(f"📰 Fetching news from RSS: {source}...")
    try:
        feed = feedparser.parse(url)
        print(f"  - Fetched {len(feed.entries)} entries from {source}.")
        return [{
            "published_at": entry.get("published", datetime.datetime.now().isoformat()),
            "source_name": source,
            "title": entry.get("title"),
            "description": entry.get("summary"),
            "url": entry.get("link")
        } for entry in feed.entries]
    except Exception as e:
        print(f"  - ❌ RSS Error ({source}): {e}")
        return []

def scrape_article_content(url: str) -> str:
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception:
        return ""

def collect_and_scrape_articles() -> List[Dict]:
    """รวบรวมลิงก์ข่าวทั้งหมด, ขูดเนื้อหา, และคืนค่าเป็น List of Dictionaries ที่สมบูรณ์"""
    print("--- 📰 Starting News Collection ---")
    initial_articles = []
    initial_articles.extend(fetch_from_newsapi())
    for name, url in RSS_FEEDS.items():
        initial_articles.extend(fetch_from_rss(url, name))

    print(f"\n🔬 Found {len(initial_articles)} potential articles. Starting scraping process...")
    full_articles = []
    for article_data in initial_articles:
        url = article_data.get("url")
        title = article_data.get("title")
        if not url or not title: continue
        
        print(f"  - Scraping: {title[:60]}...")
        full_content = scrape_article_content(url)
        
        if full_content:
            article_data['full_content'] = full_content
            full_articles.append(article_data)
            time.sleep(1)

    print(f"\n💾 Collected {len(full_articles)} articles with full content.")
    return full_articles

def build_news_index(articles: List[Dict]):
    if not articles:
        print("🟡 No valid articles to build index.")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n⚙️  Initializing embedder on device: {device.upper()}")
    
    model = SentenceTransformer("intfloat/multilingual-e5-large", device=device)
    
    texts_to_embed = [
        f"หัวข้อ: {a.get('title', '')}\nเนื้อหา: {a.get('full_content', '')}" 
        for a in articles
    ]
    
    print(f"🧠 Generating embeddings for {len(texts_to_embed)} articles...")
    embeddings = model.encode(
        ["passage: " + text for text in texts_to_embed], 
        show_progress_bar=True, 
        convert_to_numpy=True
    ).astype("float32")
    
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    
    mapping = {}
    for i, article in enumerate(articles):
        article['embedding_text'] = texts_to_embed[i]
        mapping[str(i)] = article
    
    os.makedirs(NEWS_INDEX_DIR, exist_ok=True)
    print(f"💾 Saving News Index to '{NEWS_FAISS_PATH}'...")
    faiss.write_index(index, NEWS_FAISS_PATH)
    
    print(f"💾 Saving News Mapping to '{NEWS_MAPPING_PATH}'...")
    with open(NEWS_MAPPING_PATH, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("--- 📰 Starting News Intelligence Gathering & Indexing 📰 ---")
    print("="*60)
    
    articles_with_content = collect_and_scrape_articles()
    build_news_index(articles_with_content)
    
    print("\n" + "="*60)
    print("✅ News RAG Index build process complete!")
    print("="*60)
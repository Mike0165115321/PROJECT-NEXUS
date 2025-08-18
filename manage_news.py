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
from tqdm import tqdm
from newspaper import Article, Config, ArticleException
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Set
from concurrent.futures import ThreadPoolExecutor, as_completed 
from core.config import settings
from urllib.parse import urlparse
import traceback

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
    "Hacker News": "https://news.ycombinator.com/rss",
    "Scientific American": "http://rss.sciam.com/sciam/news",
    "ScienceDaily": "https://www.sciencedaily.com/rss/top.xml",
    
    "Reuters Business": "https://www.reuters.com/pf/api/v2/content/corp/rss/US/business-news-idUSKBN0P002020150615",
    "Bloomberg Markets": "https://feeds.bloomberg.com/markets/news.rss",
    "The Economist": "https://www.economist.com/finance-and-economics/rss.xml",
    "Harvard Business Review": "https://hbr.org/rss/topic/latest",
    "Financial Times": "https://www.ft.com/world?format=rss",
    "Wall Street Journal": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",

    "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Associated Press (AP)": "https://apnews.com/hub/ap-top-news/rss.xml",
    "The New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "The Guardian": "https://www.theguardian.com/world/rss",
    "Al Jazeera English": "https://www.aljazeera.com/xml/rss/all.xml",

    "Thai PBS": "https://www.thaipbs.or.th/rss/news.xml",
    "Thairath": "https://www.thairath.co.th/rss/news.xml",
    "The Standard": "https://thestandard.co/feed/",
    "Blognone": "https://www.blognone.com/rss.xml",
    "Brand Buffet": "https://www.brandbuffet.in.th/feed/"
}

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
        config = Config()
        config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        config.request_timeout = 15

        article = Article(url, config=config)
        article.download()
        article.parse()

        return sanitize_text(article.text)     
    except ArticleException:
        # ดักจับ Error เฉพาะของ newspaper3k (เช่น 404 Not Found)
        return ""
    except Exception:
        # ดักจับ Error ทั่วไปอื่นๆ
        return ""
    
def sanitize_text(text: str) -> str:
    if not text:
        return ""
    # ลบตัวอักษรแปลก ๆ เช่น U+2028 (LS) และ U+2029 (PS)
    return text.replace("\u2028", " ").replace("\u2029", " ")

def load_existing_urls(mapping_path: str) -> Set[str]:
    """โหลด URL ของข่าวที่มีอยู่แล้วใน Index"""
    if not os.path.exists(mapping_path):
        return set()
    
    existing_urls = set()
    with open(mapping_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            for item in data.values():
                if url := item.get("url"):
                    existing_urls.add(url)
        except json.JSONDecodeError:
            print("  - ⚠️ Could not parse existing mapping file. Starting fresh.")
    
    print(f"🔍 Found {len(existing_urls)} existing articles in the index.")
    return existing_urls

def collect_and_scrape_articles(existing_urls: Set[str]) -> List[Dict]:
    print("--- 📰 Starting News Collection (True Incremental Mode) ---")
    
    initial_articles = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(fetch_from_newsapi)]
        for name, url in RSS_FEEDS.items():
            futures.append(executor.submit(fetch_from_rss, url, name))
        
        for future in as_completed(futures):
            try:
                initial_articles.extend(future.result())
            except Exception as e:
                print(f"  - ❌ A fetch task failed: {e}")

    new_articles_to_process = [
        article for article in initial_articles 
        if article.get("url") and article.get("url") not in existing_urls
    ]
    
    print(f"\n🔬 Found {len(new_articles_to_process)} new articles to scrape.")
    if not new_articles_to_process:
        return []

    articles_by_domain = {}
    for article in new_articles_to_process:
        if url := article.get("url"):
            try:
                domain = urlparse(url).netloc.replace('www.', '')
                if domain not in articles_by_domain:
                    articles_by_domain[domain] = []
                articles_by_domain[domain].append(article)
            except Exception:
                continue

    full_articles = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_domain = {
            executor.submit(scrape_article_content, articles[0].get("url")): domain
            for domain, articles in articles_by_domain.items() if articles
        }
        
        progress_bar = tqdm(total=len(new_articles_to_process), desc="Scraping New Articles")

        while future_to_domain:
            for future in as_completed(future_to_domain):
                domain = future_to_domain.pop(future)
                try:
                    content = future.result()
                    article_data = articles_by_domain[domain].pop(0)
                    if content:
                        article_data['full_content'] = content
                        full_articles.append(article_data)
                except Exception as e:
                    print(f"  - ❌ Scrape failed for a URL from {domain}: {e}")
                
                progress_bar.update(1)

                if articles_by_domain[domain]:
                    next_article = articles_by_domain[domain][0]
                    new_future = executor.submit(scrape_article_content, next_article.get("url"))
                    future_to_domain[new_future] = domain
                
                time.sleep(0.2)
        
        progress_bar.close()

    print(f"\n💾 Collected {len(full_articles)} articles with full content.")
    return full_articles

def build_news_index(articles: List[Dict], batch_size: int = 64):
    if not articles:
        print("🟡 No new articles to build index.")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer("intfloat/multilingual-e5-large", device=device)
    if device == "cuda":
        model.half()
    
    if os.path.exists(NEWS_FAISS_PATH):
        print("  - Appending to existing index...")
        index = faiss.read_index(NEWS_FAISS_PATH)
        with open(NEWS_MAPPING_PATH, "r", encoding="utf-8") as f:
            mapping = json.load(f)
    else:
        print("  - Creating new index...")
        index = None
        mapping = {}

    print(f"🧠 Generating embeddings for {len(articles)} new articles in batches of {batch_size}...")
    
    for i in tqdm(range(0, len(articles), batch_size), desc="  - Encoding Batches"):
        batch_articles = articles[i:i+batch_size]
        
        texts_to_embed = [
                            f"หัวข้อ: {sanitize_text(a.get('title', ''))}\nเนื้อหา: {sanitize_text(a.get('full_content', ''))}"
                            for a in batch_articles
                        ]
        
        new_embeddings = model.encode(
            ["passage: " + text for text in texts_to_embed], 
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        if index is None:
            index = faiss.IndexFlatL2(new_embeddings.shape[1])
        
        index.add(new_embeddings)

        start_id = len(mapping)
        for j, article in enumerate(batch_articles):
            article['title'] = sanitize_text(article.get('title', ''))
            article['description'] = sanitize_text(article.get('description', ''))
            article['full_content'] = sanitize_text(article.get('full_content', ''))
            article['embedding_text'] = texts_to_embed[j]
            mapping[str(start_id + j)] = article

    os.makedirs(NEWS_INDEX_DIR, exist_ok=True)
    faiss.write_index(index, NEWS_FAISS_PATH)
    with open(NEWS_MAPPING_PATH, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=4)
    
    print(f"✅ News RAG Index updated successfully! Total articles: {index.ntotal}")

if __name__ == "__main__":
    try:
        print("\n" + "="*60)
        print("--- 📰 Starting News Intelligence Gathering & Indexing (V5) 📰 ---")
        print("="*60)
        
        existing_urls = load_existing_urls(NEWS_MAPPING_PATH)
        new_articles = collect_and_scrape_articles(existing_urls)
        build_news_index(new_articles)

    except KeyboardInterrupt:
        print("\n\n🛑 Process interrupted by user (Ctrl+C).")
    except Exception as e:
        print(f"\n❌ A critical error occurred in the main process: {e}")
        traceback.print_exc()
    finally:
        print("\n" + "="*60)
        print("✅ News RAG Index build process finished or was interrupted.")
        print("="*60)
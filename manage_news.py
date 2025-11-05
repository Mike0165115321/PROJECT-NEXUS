# (V6.1 - BGE-M3 Optimized, FP16 VRAM, Class Architecture, Dynamic Batching)
# หน้าที่: ดึงข่าว, ขูดเนื้อหาเต็ม, และสร้าง FAISS Index + Mapping file (ในรูปแบบ Class)

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
import numpy as np 

class NewsBuilder:
    
    def __init__(self, model_name="BAAI/bge-m3"):
        print("⚙️  News Builder is initializing...")
        
        self.NEWS_INDEX_DIR = "data/news_index"
        self.NEWS_FAISS_PATH = os.path.join(self.NEWS_INDEX_DIR, "news_faiss.index")
        self.NEWS_MAPPING_PATH = os.path.join(self.NEWS_INDEX_DIR, "news_mapping.json")

        self.NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
        self.RSS_FEEDS = {
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
            
            "Google News (TH)": "https://news.google.com/rss?hl=th&gl=TH&ceid=TH:th", 
            "Thai PBS": "https://www.thaipbs.or.th/rss/news.xml",
            "Thairath": "https://www.thairath.co.th/rss/news.xml",
            "The Standard": "https://thestandard.co/feed/",
            "Blognone": "https://www.blognone.com/rss.xml",
            "Brand Buffet": "https://www.brandbuffet.in.th/feed/"
        }
        
        self.settings = settings
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"  - Initializing on device: {device.upper()}")
        
        self.model = SentenceTransformer(model_name, device="cpu")
        
        if device == "cuda":
            print("  - ⚡️ Converting model to FP16 (on CPU) for VRAM efficiency...")
            self.model.half()
            print("  - ⚡️ Moving FP16 model to CUDA...")
            self.model.to(device)
            
        print(f"✅ Embedding model '{model_name}' loaded successfully (FP16: {device=='cuda'}).")


    def _sanitize_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace("\u2028", " ").replace("\u2029", " ")
        text = " ".join(text.split()) 
        return text.strip()

    def fetch_from_newsapi(self) -> List[Dict]:
        print("📰 Fetching news from NewsAPI.org...")
        if not self.settings.NEWS_KEY:
            print("   - ⚠️ NewsAPI key not found in .env file.")
            return []
        
        params = {'country': 'us', 'pageSize': 20, 'apiKey': self.settings.NEWS_KEY}
        try:
            response = requests.get(self.NEWS_API_URL, params=params, timeout=15)
            response.raise_for_status()
            articles = response.json().get('articles', [])
            print(f"   - Fetched {len(articles)} articles from NewsAPI.")
            return [{
                "published_at": a.get("publishedAt"),
                "source_name": a.get("source", {}).get("name"),
                "title": a.get("title"),
                "description": a.get("description"),
                "url": a.get("url")
            } for a in articles]
        except Exception as e:
            print(f"   - ❌ NewsAPI Error: {e}")
            return []

    def fetch_from_rss(self, url: str, source: str) -> List[Dict]:
        """ดึงข่าวจากแหล่ง RSS Feed"""
        try:
            feed = feedparser.parse(url)
            return [{
                "published_at": entry.get("published", datetime.datetime.now().isoformat()),
                "source_name": source,
                "title": entry.get("title"),
                "description": entry.get("summary"),
                "url": entry.get("link")
            } for entry in feed.entries]
        except Exception as e:
            print(f"   - ❌ RSS Error ({source}): {e}")
            return []

    def scrape_article_content(self, url: str) -> str:
        try:
            config = Config()
            config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            config.request_timeout = 15

            article = Article(url, config=config)
            article.download()
            article.parse()

            return self._sanitize_text(article.text)
        except ArticleException:
            return ""
        except Exception:
            return ""
        
    def load_existing_urls(self) -> Set[str]:
        """โหลด URL ของข่าวที่มีอยู่แล้วใน Index"""
        if not os.path.exists(self.NEWS_MAPPING_PATH):
            return set()
        
        existing_urls = set()
        with open(self.NEWS_MAPPING_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                for item in data.values():
                    if url := item.get("url"):
                        existing_urls.add(url)
            except json.JSONDecodeError:
                print("   - ⚠️ Could not parse existing mapping file. Starting fresh.")
        
        print(f"🔍 Found {len(existing_urls)} existing articles in the index.")
        return existing_urls

    def collect_and_scrape_articles(self, existing_urls: Set[str]) -> List[Dict]:
        print("--- 📰 Starting News Collection (True Incremental Mode) ---")
        
        initial_articles = []
        with ThreadPoolExecutor(max_workers=15) as executor:
            print("  - Submitting fetch tasks (NewsAPI + RSS)...")
            futures = [executor.submit(self.fetch_from_newsapi)]
            for name, url in self.RSS_FEEDS.items():
                futures.append(executor.submit(self.fetch_from_rss, url, name))
            
            for future in as_completed(futures):
                try:
                    initial_articles.extend(future.result())
                except Exception as e:
                    print(f"   - ❌ A fetch task failed: {e}")

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
                executor.submit(self.scrape_article_content, articles[0].get("url")): domain
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
                        print(f"   - ❌ Scrape failed for a URL from {domain}: {e}")
                    
                    progress_bar.update(1)

                    if articles_by_domain[domain]:
                        next_article = articles_by_domain[domain][0]
                        new_future = executor.submit(self.scrape_article_content, next_article.get("url"))
                        future_to_domain[new_future] = domain
                    
                    time.sleep(0.2) # หน่วงเวลาเล็กน้อยเพื่อกันการโดนแบน
            
            progress_bar.close()

        print(f"\n💾 Collected {len(full_articles)} articles with full content.")
        return full_articles

    # --- [V6.1] MODIFIED FUNCTION: build_news_index ---
    # ลบ 'batch_size' parameter ออก เพราะเราจะกำหนดแบบไดนามิก
    def build_news_index(self, articles: List[Dict]):
        if not articles:
            print("🟡 No new articles to build index.")
            return

        if os.path.exists(self.NEWS_FAISS_PATH):
            print("   - Appending to existing index...")
            index = faiss.read_index(self.NEWS_FAISS_PATH)
            with open(self.NEWS_MAPPING_PATH, "r", encoding="utf-8") as f:
                mapping = json.load(f)
        else:
            print("   - Creating new index...")
            index = None
            mapping = {}

        print(f"🧠 Generating embeddings for {len(articles)} new articles...")
        
        # --- [V6.1] Step 1: วัดขนาดและเตรียมข้อมูล ---
        # เราจะประมวลผลบทความทั้งหมดก่อน เพื่อวัดความยาวและเรียงลำดับ
        print("   - Step 1: Measuring and preparing all new articles...")
        jobs = []
        for article_data in articles:
            title = self._sanitize_text(article_data.get('title', ''))
            content = self._sanitize_text(article_data.get('full_content', ''))
            embedding_text = f"หัวข้อ: {title}\nเนื้อหา: {content}"
            
            jobs.append({
                "article_data": article_data,
                "embedding_text": embedding_text,
                "length": len(embedding_text) # ใช้ความยาวตัวอักษรเป็น proxy
            })

        # --- [V6.1] Step 2: เรียงลำดับจากสั้นไปยาว ---
        print(f"   - Step 2: Sorting {len(jobs)} jobs by text length...")
        sorted_jobs = sorted(jobs, key=lambda x: x['length'])

        # --- [V6.1] Step 3: สร้าง Batch แบบไดนามิก ---
        print("   - Step 3: Encoding with Dynamic Batching...")
        
        # ย้าย tqdm มาอยู่นอก loop
        pbar = tqdm(total=len(sorted_jobs), desc="   - Encoding Batches")
        
        # กำหนด ID เริ่มต้นสำหรับ mapping (สำคัญมาก!)
        start_id = len(mapping) 
        
        current_idx = 0
        while current_idx < len(sorted_jobs):
            
            # 3.1) ดึงบทความที่ยาวที่สุดใน batch ที่กำลังจะสร้าง (คือตัวแรกของ list ที่เหลือ)
            # เราใช้ความยาวนี้เป็นเกณฑ์ในการตัดสินใจขนาด batch
            max_len_in_batch = sorted_jobs[current_idx]['length']

            # 3.2) ตัดสินใจขนาด Batch (Dynamic Batch Size)
            # นี่คือค่าประมาณการ (Heuristics) ที่ปลอดภัย
            # ถ้าตัวที่ยาวสุดยังสั้น -> ใช้อันที่ยาวกว่า
            # OOM ของคุณเกิดที่ [4, 2048, 1024] (ประมาณ 8192 "Token-like units")
            # เราจะใช้ค่าที่ต่ำกว่านั้น
            
            # (ค่าเหล่านี้คุณสามารถจูนได้ ถ้ายัง OOM ก็ลด batch size ลงอีก)
            if max_len_in_batch > 16000:   # ~4000+ tokens (ยาวมาก)
                dynamic_batch_size = 4     # ลดลงจาก 4 (ที่คุณบอกว่า OOM) -> อาจจะต้อง 2 หรือ 1
            elif max_len_in_batch > 8000:  # ~2000+ tokens (ยาว)
                dynamic_batch_size = 8
            elif max_len_in_batch > 4000:  # ~1000+ tokens
                dynamic_batch_size = 32
            else:                          # < 1000 tokens (สั้น)
                dynamic_batch_size = 64    # ขนาดใหญ่ได้
            
            # *** [V6.1] SAFETY CHECK (ปรับแก้จาก V6.1) ***
            # ถ้าเราพบว่า batch_size = 4, len = 2048 (ประมาณ 8000+ chars) มัน OOM
            # เราต้องปรับตรรกะให้ปลอดภัยกว่านี้
            
            if max_len_in_batch > 8000:    # ~2000+ tokens (ที่เคย OOM)
                dynamic_batch_size = 2     # *** ใช้ 2 เพื่อความปลอดภัยสูงสุด ***
            elif max_len_in_batch > 4000:  # ~1000+ tokens
                dynamic_batch_size = 8
            elif max_len_in_batch > 2000:
                dynamic_batch_size = 32
            else:                          # < 500 tokens (สั้นมาก)
                dynamic_batch_size = 64    # ขนาดใหญ่ได้

            # 3.3) สร้าง Batch
            end_idx = min(current_idx + dynamic_batch_size, len(sorted_jobs))
            batch_jobs = sorted_jobs[current_idx:end_idx]
            
            if not batch_jobs:
                break # ควรจะไม่เกิดขึ้น แต่ใส่ไว้กันเหนียว

            texts_to_embed = [job['embedding_text'] for job in batch_jobs]
            batch_articles_data = [job['article_data'] for job in batch_jobs]
            
            # 3.4) Encode (เหมือนเดิม)
            new_embeddings = self.model.encode(
                texts_to_embed,
                show_progress_bar=False,
                convert_to_numpy=True
            ).astype("float32")
            
            faiss.normalize_L2(new_embeddings)

            # 3.5) Add to Index (เหมือนเดิม)
            if index is None:
                print("   - (First batch) Initializing new index with IndexFlatIP.")
                index = faiss.IndexFlatIP(new_embeddings.shape[1])
            
            index.add(new_embeddings)

            # 3.6) Update Mapping (ปรับปรุงเล็กน้อย)
            for j, article_data in enumerate(batch_articles_data):
                article_data['title'] = self._sanitize_text(article_data.get('title', ''))
                article_data['description'] = self._sanitize_text(article_data.get('description', ''))
                article_data['full_content'] = self._sanitize_text(article_data.get('full_content', ''))
                article_data['embedding_text'] = texts_to_embed[j]
                
                # ใช้ 'start_id' ที่เรานับต่อเนื่อง
                mapping[str(start_id + j)] = article_data

            # 3.7) อัปเดตตัวแปรสำหรับ Loop
            pbar.update(len(batch_jobs)) # อัปเดต progress bar ตามจำนวนที่ทำจริง
            start_id += len(batch_jobs)  # เพิ่ม ID เริ่มต้นสำหรับ batch ถัดไป
            current_idx = end_idx        # ขยับ index ไปที่จุดเริ่มต้นของ batch ถัดไป

        pbar.close() # ปิด Pbar เมื่อ loop จบ

        os.makedirs(self.NEWS_INDEX_DIR, exist_ok=True)
        faiss.write_index(index, self.NEWS_FAISS_PATH)
        with open(self.NEWS_MAPPING_PATH, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=4)
        
        print(f"✅ News RAG Index updated successfully! Total articles: {index.ntotal}")

if __name__ == "__main__":
    try:
        print("\n" + "="*60)
        print("--- 📰 Starting News Intelligence Gathering & Indexing (V6.1) 📰 ---")
        print("="*60)
        
        builder = NewsBuilder()
        
        existing_urls = builder.load_existing_urls()
        new_articles = builder.collect_and_scrape_articles(existing_urls)
        
        # สังเกตว่าเราไม่ต้องส่ง batch_size ไปแล้ว
        builder.build_news_index(new_articles)

    except KeyboardInterrupt:
        print("\n\n🛑 Process interrupted by user (Ctrl+C).")
    except Exception as e:
        print(f"\n❌ A critical error occurred in the main process: {e}")
        traceback.print_exc()
    finally:
        print("\n" + "="*60)
        print("✅ News RAG Index build process finished or was interrupted.")
        print("="*60)
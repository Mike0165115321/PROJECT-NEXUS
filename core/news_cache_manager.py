# core/news_cache_manager.py
# (V3.1 - Added structured search method)

import faiss
import json
import os
from sentence_transformers import SentenceTransformer
from typing import List, Dict

NEWS_INDEX_DIR = "data/news_index"
NEWS_FAISS_PATH = os.path.join(NEWS_INDEX_DIR, "news_faiss.index")
NEWS_MAPPING_PATH = os.path.join(NEWS_INDEX_DIR, "news_mapping.json")

class NewsCacheManager:
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.embedder = SentenceTransformer(model_name)
        self.index = None
        self.mapping = None
        self._load_index()
        print("📰 News RAG Engine is ready.")

    def _load_index(self):
        if os.path.exists(NEWS_FAISS_PATH) and os.path.exists(NEWS_MAPPING_PATH):
            try:
                print("  - Loading existing news index...")
                self.index = faiss.read_index(NEWS_FAISS_PATH)
                with open(NEWS_MAPPING_PATH, "r", encoding="utf-8") as f:
                    self.mapping = json.load(f)
                print("  - News index loaded successfully.")
            except Exception as e:
                print(f"  - ⚠️ Error loading news index: {e}")
                self.index = None
                self.mapping = None
        else:
            print("  - 🟡 News index not found. Run 'manage_news.py' to create it.")

    def search(self, query: str, k: int = 3) -> str:
        """
        ค้นหาและคืนค่าเป็น "บริบท" (String) สำหรับ ConsultantAgent
        """
        results = self.search_structured_data(query, k=k)
        
        if not results or "error" in results[0]:
            return "ไม่พบข่าวที่เกี่ยวข้องในคลังข้อมูลล่าสุด"

        context = "\n---\n".join([
            f"จาก {res.get('source_name', 'N/A')} ({res.get('published_at', '')[:10]}):\n"
            f"หัวข้อ: {res.get('title', '')}\n"
            f"เนื้อหา: {res.get('full_content', '')}"
            for res in results
        ])
        return context

    def search_structured_data(self, query: str, k: int = 5) -> List[Dict]:
        """
        ค้นหาและคืนค่าเป็น "ข้อมูลดิบ" (List of Dictionaries) สำหรับ NewsAgent
        """
        if not self.index or not self.mapping:
            return [{"error": "คลังข่าวสารยังไม่ถูกสร้างขึ้น"}]

        print(f"🔍 News RAG: Searching for '{query[:20]}...' (Structured)")
        try:
            query_vector = self.embedder.encode([query], convert_to_numpy=True).astype("float32")
            _, indices = self.index.search(query_vector, k)
            
            results = [self.mapping.get(str(i)) for i in indices[0] if self.mapping.get(str(i))]
            
            if not results:
                return [{"error": "ไม่พบข่าวที่เกี่ยวข้อง"}]
                
            return results
            
        except Exception as e:
            print(f"❌ News RAG: Error during structured search: {e}")
            return [{"error": "เกิดข้อผิดพลาดขณะค้นหาในคลังข่าวสาร"}]
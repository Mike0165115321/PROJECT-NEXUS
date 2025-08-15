# core/news_rag_engine.py
# (V1.0 - Specialized News Vector Search Engine)

import faiss
import json
import os
from sentence_transformers import SentenceTransformer
import torch
from typing import List, Dict, Any

class NewsRAGEngine:
    def __init__(self, 
                 embedder_model: str = "intfloat/multilingual-e5-large", 
                 news_index_path: str = "data/news_index"):
        
        print("📰 เครื่องยนต์ News RAG กำลังเริ่มต้น...")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embedder = SentenceTransformer(embedder_model, device=device)
        
        self.news_index = None
        self.news_mapping = None
        self._load_news_index(news_index_path)

        print("✅ News RAG Engine is ready.")

    def _load_news_index(self, path: str):
        print("  - 📰 Loading News Vector Base (FAISS on CPU)...")
        if not os.path.exists(path):
            print(f"    - 🟡 News RAG index path not found: '{path}'. News search will be disabled.")
            return
        try:
            faiss_path = os.path.join(path, "news_faiss.index") 
            mapping_path = os.path.join(path, "news_mapping.json")
            
            if not os.path.exists(faiss_path) or not os.path.exists(mapping_path):
                print("    - 🟡 News RAG index files not found. News search will be disabled.")
                return

            self.news_index = faiss.read_index(faiss_path)
            
            with open(mapping_path, "r", encoding="utf-8") as f:
                self.news_mapping = json.load(f)
            
            print(f"    - ✅ ฐานข้อมูลข่าวกรอง {len(self.news_mapping)} บทความ พร้อมใช้งาน!")
        except Exception as e:
            print(f"    - ❌ Critical error loading news index: {e}")
            self.news_index = None
            self.news_mapping = None

    def search(self, query: str, top_k: int = 7) -> str:
        """
        ค้นหาใน News Index ด้วย Vector Search และคืนค่าเป็น context string
        """
        if not self.news_index or not self.news_mapping:
            return "ไม่พบข้อมูลข่าวสารที่เกี่ยวข้อง"
        
        query_vector = self.embedder.encode(["query: " + query], convert_to_numpy=True).astype("float32")
        
        distances, indices = self.news_index.search(query_vector, top_k)
        
        results = []
        for i in indices[0]:
            if str(i) in self.news_mapping:
                item = self.news_mapping[str(i)]
                context = f"จากแหล่งข่าว '{item.get('source_name')}':\nหัวข้อ: {item.get('title')}\nสรุป: {item.get('description')}\n---\n"
                results.append(context)
        
        if not results:
            return "ไม่พบข้อมูลข่าวสารที่เกี่ยวข้อง"
            
        return "\n".join(results)
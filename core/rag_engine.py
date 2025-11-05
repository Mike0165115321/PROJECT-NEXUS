# (V32.1 - Async Startup & BGE-M3 Ready)

import faiss
import json
import os
from sentence_transformers import SentenceTransformer, CrossEncoder
import torch
from typing import List, Dict, Any, Optional
import asyncio

class RAGEngine:
    def __init__(self, 
                 embedder: SentenceTransformer, 
                 reranker: CrossEncoder,
                 book_index_path: str = "data/index",
                 memory_index_path: str = "data/memory_index",
                 graph_index_path: str = "data/graph_index",
                 news_index_path: str = "data/news_index"):
        
        print("⚙️  ห้องเครื่องยนต์ RAG (V32.1 - BGE-M3 Ready) กำลังเริ่มต้น...")
        
        self.embedder = embedder
        self.reranker = reranker
        
        self.book_index_path = book_index_path
        self.memory_index_path = memory_index_path
        self.graph_index_path = graph_index_path
        self.news_index_path = news_index_path
        
        self.book_indexes, self.book_mappings, self.available_categories = {}, {}, []
        self.memory_index, self.memory_mapping = None, None
        self.graph_index, self.graph_mapping = None, None
        self.news_index, self.news_mapping = None, None

    async def load_models_and_index(self):
        """[V32] โหลด Index ทั้ง 4 (แบบ Async) เพื่อไม่ให้บล็อก 'lifespan'"""
        
        print("    - 📚 [V32] Loading Book Knowledge Bases (Async)...")
        await asyncio.to_thread(self._load_book_indexes, self.book_index_path)
        
        print("    - 🧠 [V32] Loading Memory Knowledge Base (Async)...")
        await asyncio.to_thread(self._load_memory_index, self.memory_index_path)
        
        print("    - 🕸️  [V32] Loading Knowledge Graph Vector Base (Async)...")
        await asyncio.to_thread(self._load_graph_index, self.graph_index_path)
        
        print("    - 📰 [V32] Loading News Vector Base (Async)...")
        await asyncio.to_thread(self._load_news_index, self.news_index_path)
        
        print("✅ [V32.1] Unified RAG Engine (Async + BGE-M3) is fully loaded and ready.")

    def _load_book_indexes(self, base_path: str):
        print("        - [V32] Loading Book Knowledge Bases (FAISS on CPU)...")
        if not os.path.exists(base_path): 
            print("            - 🟡 ไม่พบหมวดหมู่หนังสือที่สามารถโหลดได้")
            return
        for category_name in os.listdir(base_path):
            category_path = os.path.join(base_path, category_name)
            if os.path.isdir(category_path):
                try:
                    index_path = os.path.join(category_path, "faiss.index")
                    mapping_path = os.path.join(category_path, "mapping.jsonl")
                    if not os.path.exists(index_path) or not os.path.exists(mapping_path): continue
                    index = faiss.read_index(index_path)
                    mapping = {str(i): json.loads(line) for i, line in enumerate(open(mapping_path, "r", encoding="utf-8"))}
                    self.book_indexes[category_name] = {"index": index, "mapping": mapping}
                    self.available_categories.append(category_name)
                except Exception as e:
                    print(f"            - ❌ Error loading book index for '{category_name}': {e}")
        self.available_categories.sort()
        print(f"            - ✅ ความรู้หนังสือ {len(self.available_categories)} หมวดหมู่ พร้อมใช้งาน")

    def _load_memory_index(self, path: str):
        print("        - [V32] Loading Memory Knowledge Base (FAISS on CPU)...")
        if not os.path.exists(path):
            print(f"            - 🟡 Memory RAG index path not found: '{path}'.")
            return
        try:
            faiss_path = os.path.join(path, "memory_faiss.index") 
            mapping_path = os.path.join(path, "memory_mapping.json")
            if not os.path.exists(faiss_path) or not os.path.exists(mapping_path): return
            self.memory_index = faiss.read_index(faiss_path)
            with open(mapping_path, "r", encoding="utf-8") as f:
                self.memory_mapping = list(json.load(f).values())
            print(f"            - ✅ สมองส่วนความทรงจำ {len(self.memory_mapping)} ตื่น!!")
        except Exception as e:
            print(f"            - ❌ Critical error loading memory index: {e}")

    def _load_graph_index(self, path: str):
        print("        - [V32] Loading Knowledge Graph Vector Base (FAISS on CPU)...")
        if not os.path.exists(path):
            print(f"            - 🟡 KG-RAG index path not found: '{path}'.")
            return
        try:
            faiss_path = os.path.join(path, "graph_faiss.index") 
            mapping_path = os.path.join(path, "graph_mapping.jsonl")
            if not os.path.exists(faiss_path) or not os.path.exists(mapping_path): return
            self.graph_index = faiss.read_index(faiss_path)
            mapping = {str(i): json.loads(line) for i, line in enumerate(open(mapping_path, "r", encoding="utf-8"))}
            self.graph_mapping = mapping
            print(f"            - ✅ ฐานความรู้ Knowledge Graph {len(self.graph_mapping)} พร้อมใช้งาน!")
        except Exception as e:
            print(f"            - ❌ Critical error loading graph index: {e}")

    def _load_news_index(self, path: str):
        print("        - [V32] Loading News Vector Base (FAISS on CPU)...")
        if not os.path.exists(path):
            print(f"            - 🟡 News RAG index path not found: '{path}'.")
            return
        try:
            faiss_path = os.path.join(path, "news_faiss.index") 
            mapping_path = os.path.join(path, "news_mapping.json")
            if not os.path.exists(faiss_path) or not os.path.exists(mapping_path): return
            self.news_index = faiss.read_index(faiss_path)
            with open(mapping_path, "r", encoding="utf-8") as f:
                self.news_mapping = json.load(f)
            print(f"            - ✅ ฐานข้อมูลข่าวกรอง {len(self.news_mapping)} บทความ พร้อมใช้งาน!")
        except Exception as e:
            print(f"            - ❌ Critical error loading news index: {e}")

    async def get_all_book_titles(self) -> list:
        
        def _blocking_get_titles():
            print("    - 📚 [V32] Getting all book titles (Sync in Thread)...")
            all_titles = set(item.get("book_title").strip() 
                             for cat_data in self.book_indexes.values() 
                             for item in cat_data["mapping"].values() 
                             if item.get("book_title"))
            return sorted(list(all_titles))

        titles = await asyncio.to_thread(_blocking_get_titles)
        return titles

    async def search_books(self, query: str, top_k_retrieval: int = 5, top_k_rerank: int = 5,
                           return_raw_chunks: bool = False, 
                           target_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        
        search_scope = {cat: self.book_indexes[cat] for cat in target_categories if cat in self.book_indexes} if target_categories else self.book_indexes
        if not search_scope: search_scope = self.book_indexes
        
        try:
            query_vector = await asyncio.to_thread(
                self.embedder.encode, [query], convert_to_numpy=True
            )

            def _blocking_faiss_search():
                candidates = []
                for category, data in search_scope.items():
                    distances, indices = data["index"].search(query_vector, top_k_retrieval)
                    for i in indices[0]:
                        if item := data["mapping"].get(str(i)):
                            item['category'] = category 
                            candidates.append(item)
                return candidates

            all_candidates = await asyncio.to_thread(_blocking_faiss_search)
            
            if not all_candidates: return {"context": "", "sources": [], "raw_chunks": []}
            
            unique_candidates = list({item['embedding_text']: item for item in all_candidates}.values())
            sentence_pairs = [[query, item.get('embedding_text', '')] for item in unique_candidates]
            
            scores = await asyncio.to_thread(
                self.reranker.predict, sentence_pairs
            )
            
            reranked_results = sorted(zip(scores, unique_candidates), key=lambda x: x[0], reverse=True)
            top_results = reranked_results[:top_k_rerank]
            
            if not top_results: return {"context": "", "sources": [], "raw_chunks": []}
            
            final_contexts = [item.get("embedding_text", "") for _, item in top_results]
            raw_sources = [item.get("book_title") for _, item in top_results]
            final_sources = sorted(list(set(source for source in raw_sources if source)))
            
            result = {"context": "\n\n---\n\n".join(final_contexts), "sources": final_sources}
            if return_raw_chunks:
                result["raw_chunks"] = [dict(item, rerank_score=float(score)) for score, item in top_results]
                
            return result
        
        except Exception as e:
            print(f"❌ Error during async search_books: {e}")
            return {"context": "", "sources": [], "raw_chunks": []}

    async def search_memory(self, query: str, top_k: int = 5) -> List[Dict]:
        if not self.memory_index or not self.memory_mapping: return []
        
        query_vector = await asyncio.to_thread(
            self.embedder.encode, [query], convert_to_numpy=True
        )
        distances, indices = await asyncio.to_thread(
            self.memory_index.search, query_vector, top_k
        )
        
        results = []
        for dist, i in zip(distances[0], indices[0]):
            if i < len(self.memory_mapping):
                item = self.memory_mapping[i].copy()
                item['score'] = float(dist)
                results.append(item)
        return results

    async def search_graph(self, query: str, top_k: int = 3) -> List[Dict]:
        if not self.graph_index or not self.graph_mapping: return []
        
        query_vector = await asyncio.to_thread(
            self.embedder.encode, [query], convert_to_numpy=True
        )
        distances, indices = await asyncio.to_thread(
            self.graph_index.search, query_vector, top_k
        )
        
        results, found_ids = [], set()
        for dist, i in zip(distances[0], indices[0]):
            if item := self.graph_mapping.get(str(i)):
                item_copy = item.copy()
                item_id = item_copy.get('id')
                if item_id not in found_ids:
                    item_copy['score'] = float(dist)
                    results.append(item_copy)
                    found_ids.add(item_id)
        return results

    async def search_news(self, query: str, top_k: int = 7) -> str:
        if not self.news_index or not self.news_mapping: return "ไม่พบข้อมูลข่าวสารที่เกี่ยวข้อง"
        
        query_vector = await asyncio.to_thread(
            self.embedder.encode, [query], convert_to_numpy=True
        )
        distances, indices = await asyncio.to_thread(
            self.news_index.search, query_vector, top_k
        )
        
        results = []
        for i in indices[0]:
            if item := self.news_mapping.get(str(i)):
                context = f"จากแหล่งข่าว '{item.get('source_name')}':\nหัวข้อ: {item.get('title')}\nสรุป: {item.get('description')}\n---\n"
                results.append(context)
        return "\n".join(results) if results else "ไม่พบข้อมูลข่าวสารที่เกี่ยวข้อง"
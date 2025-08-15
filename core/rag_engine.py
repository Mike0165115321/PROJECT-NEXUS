# core/rag_engine.py
# (V5.1 - Final Stable Hybrid GPU/CPU Mode)

import faiss
import json
import os
from sentence_transformers import SentenceTransformer, CrossEncoder
import torch
from typing import List, Dict, Any, Optional

class RAGEngine:
    def __init__(self, 
                 embedder_model: str = "intfloat/multilingual-e5-large", 
                 reranker_model: str = "BAAI/bge-reranker-base",
                 book_index_path: str = "data/index",
                 memory_index_path: str = "data/memory_index"):
        
        print("⚙️  ห้องเครื่องยนต์ RAG กำลังเริ่มต้น...")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cuda":
            print("  - ปลดล็อคขุมพลัง GPU (CUDA) ถูกเปิดใช้งาน การค้นหาจะเร็วและทรงพลัง")
        else:
            print(f"  - ใช้ Device สำหรับ Models: {device.upper()}")
        
        self.embedder = SentenceTransformer(embedder_model, device=device)
        self.reranker = CrossEncoder(reranker_model, device=device)
        
        self.book_indexes = {}
        self.book_mappings = {}
        self.available_categories = []
        self._load_book_indexes(book_index_path)
        
        self.memory_index = None
        self.memory_mapping = None
        self._load_memory_index(memory_index_path)

        print("✅ RAG Engine is ready.")

    def _load_book_indexes(self, base_path: str):
        print("📚 Loading Book Knowledge Bases (FAISS on CPU)...")
        if not os.path.exists(base_path): 
            print("  - 🟡 ไม่พบหมวดหมู่หนังสือที่สามารถโหลดได้")
            return
        for category_name in os.listdir(base_path):
            category_path = os.path.join(base_path, category_name)
            if os.path.isdir(category_path):
                try:
                    index_path = os.path.join(category_path, "faiss.index")
                    mapping_path = os.path.join(category_path, "mapping.jsonl")
                    
                    if not os.path.exists(index_path) or not os.path.exists(mapping_path):
                        continue

                    index = faiss.read_index(index_path)
                    
                    mapping = {}
                    with open(mapping_path, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f):
                            mapping[str(i)] = json.loads(line)
                    
                    self.book_indexes[category_name] = {"index": index, "mapping": mapping}
                    self.available_categories.append(category_name)
                except Exception as e:
                    print(f"  - ❌ Error loading index for '{category_name}': {e}")
        self.available_categories.sort()
        print(f"  - ✅ ความรู้หนังสือ {len(self.available_categories)} พร้อมใช้งาน")

    def _load_memory_index(self, path: str):
        print("🧠 Loading Memory Knowledge Base (FAISS on CPU)...")
        if not os.path.exists(path):
            print(f"  - 🟡 Memory RAG index path not found: '{path}'. Memory search will be disabled.")
            return
        try:
            faiss_path = os.path.join(path, "memory_faiss.index") 
            mapping_path = os.path.join(path, "memory_mapping.json")
            
            if not os.path.exists(faiss_path) or not os.path.exists(mapping_path):
                print("  - 🟡 Memory RAG index files not found inside the directory. Memory search will be disabled.")
                return

            self.memory_index = faiss.read_index(faiss_path)
            
            with open(mapping_path, "r", encoding="utf-8") as f:
                memory_data_dict = json.load(f)
                self.memory_mapping = list(memory_data_dict.values())
            
            print(f"  - ✅ สมองส่วนความทรงจำ {len(self.memory_mapping)} ตื่น!!")
        except Exception as e:
            print(f"  - ❌ Critical error loading memory index: {e}")
            self.memory_index = None
            self.memory_mapping = None

    def get_all_book_titles(self) -> list:
        all_titles = set()
        for cat_data in self.book_indexes.values():
            for item in cat_data["mapping"].values():
                if item.get("book_title"):
                    all_titles.add(item.get("book_title").strip())
        return sorted(list(all_titles))

    def search_books(self, query: str, top_k_retrieval: int = 10, top_k_rerank: int = 5, 
                   return_raw_chunks: bool = False, 
                   target_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        search_scope = {}
        if target_categories:
            for cat in target_categories:
                if cat in self.book_indexes:
                    search_scope[cat] = self.book_indexes[cat]
            if not search_scope:
                 search_scope = self.book_indexes
        else:
            search_scope = self.book_indexes
        all_candidates = []
        query_vector = self.embedder.encode([query], convert_to_numpy=True).astype("float32")
        for category, data in search_scope.items():
            distances, indices = data["index"].search(query_vector, top_k_retrieval)
            for i in indices[0]:
                item = data["mapping"].get(str(i))
                if item:
                    item['category'] = category 
                    all_candidates.append(item)
        if not all_candidates:
            return {"context": "", "sources": [], "raw_chunks": []}
        unique_candidates = list({item['embedding_text']: item for item in all_candidates}.values())
        sentence_pairs = [[query, item.get('embedding_text', '')] for item in unique_candidates]
        scores = self.reranker.predict(sentence_pairs)
        reranked_results = sorted(zip(scores, unique_candidates), key=lambda x: x[0], reverse=True)
        top_results = reranked_results[:top_k_rerank]
        if not top_results:
            return {"context": "", "sources": [], "raw_chunks": []}
        final_contexts = [item.get("embedding_text", "") for score, item in top_results]
        raw_sources = [item.get("book_title") for score, item in top_results]
        final_sources = sorted(list(set(source for source in raw_sources if source)))
        result = {"context": "\n\n---\n\n".join(final_contexts), "sources": final_sources}
        if return_raw_chunks:
            chunks_with_scores = [dict(item, rerank_score=float(score)) for score, item in top_results]
            result["raw_chunks"] = chunks_with_scores
        return result

    def search_memory(self, query: str, top_k: int = 5) -> List[Dict]:
        if not self.memory_index or not self.memory_mapping:
            return []
        query_vector = self.embedder.encode([query], convert_to_numpy=True).astype("float32")
        distances, indices = self.memory_index.search(query_vector, top_k)
        results = []
        for dist, i in zip(distances[0], indices[0]):
            if i < len(self.memory_mapping):
                item = self.memory_mapping[i].copy()
                item['score'] = float(dist)
                results.append(item)
        return results
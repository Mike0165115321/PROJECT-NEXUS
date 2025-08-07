# core/long_term_memory_manager.py
# (V5 - The Fast Searcher: Read-Only & Optimized)

import faiss
import json
import os
import torch
from sentence_transformers import SentenceTransformer
from typing import List, Dict

class LongTermMemoryManager:
    """
    รับผิดชอบการ "ค้นหา" ความทรงจำระยะยาวที่ถูกประมวลผลแล้วเท่านั้น
    ถูกออกแบบมาให้ทำงานเร็วที่สุดเพื่อไม่ให้กระทบการตอบสนองของ Agent
    """
    def __init__(self, embedding_model: str, index_dir: str):
        
        self.index_path = os.path.join(index_dir, "memory_faiss.index")
        self.mapping_path = os.path.join(index_dir, "memory_mapping.jsonl") # ⭐️ ใช้ .jsonl

        # โหลดโมเดลสำหรับค้นหา
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"⚙️  LTM Search Embedder is initializing on device: {device.upper()}")
        self.embedder = SentenceTransformer(embedding_model, device=device)

        self.index: faiss.Index | None = None
        self.mapping_count: int = 0
        self._load_existing_index()
        
        print("🏛️  Long Term Memory Manager (V5 - Searcher) is ready.")

    def _load_existing_index(self):
        """โหลด Index และ Mapping ที่ถูกสร้างไว้แล้วจากดิสก์"""
        if os.path.exists(self.index_path) and os.path.exists(self.mapping_path):
            try:
                print("🧠 LTM: Loading existing memory index for searching...")
                self.index = faiss.read_index(self.index_path)
                with open(self.mapping_path, "r", encoding="utf-8") as f:
                    self.mapping_count = sum(1 for _ in f)
                
                if self.index.ntotal != self.mapping_count:
                    print(f"⚠️ LTM Searcher: Index mismatch! (Index: {self.index.ntotal}, Mapping: {self.mapping_count}).")
                else:
                    print(f"✅ LTM Searcher: Ready with {self.index.ntotal} memories.")
            except Exception as e:
                print(f"⚠️ LTM Searcher: Could not load memory index. Search will be disabled. Error: {e}")
        else:
            print("🟡 LTM Searcher: Memory index not found. Search is currently disabled.")

    def reload_index(self):
        """
        เมธอดสำหรับให้ระบบเรียกใช้เพื่อโหลด Index ใหม่
        หลังจากที่ 'manage_memory.py' ทำงานเสร็จ
        """
        print("🔄 LTM Searcher: Reloading memory index...")
        self._load_existing_index()

    def search_relevant_memories(self, query: str, k: int = 2) -> List[Dict]:
        """ค้นหาความทรงจำที่เกี่ยวข้องจาก Index ที่โหลดไว้"""
        if self.index is None: return [] 
        
        print(f"🧠 LTM Searcher: Searching memories for '{query[:20]}...'")
        try:
            query_vector = self.embedder.encode(["query: " + query], convert_to_numpy=True).astype("float32")
            _, indices = self.index.search(query_vector, k)
            
            # อ่านจาก .jsonl ตาม index ที่ได้มาอย่างมีประสิทธิภาพ
            found_memories = []
            with open(self.mapping_path, "r", encoding="utf-8") as f:
                lines = {i: line for i, line in enumerate(f)}
            
            for i in indices[0]:
                if i in lines:
                    found_memories.append(json.loads(lines[i]))

            if found_memories:
                print(f"✅ LTM Searcher: Found {len(found_memories)} relevant memories.")
            return found_memories
        except Exception as e:
            print(f"❌ LTM Searcher: Error searching memories: {e}")
            return []
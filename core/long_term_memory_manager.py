# (V35.0 - BGE-M3 Ready: Prefix Removed, Normalization Added, Stable Load)

import faiss
import json
import os
import torch
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import asyncio 
import numpy as np 

class LongTermMemoryManager:
    def __init__(self, embedding_model: str, index_dir: str):
        
        self.index_path = os.path.join(index_dir, "memory_faiss.index")
        self.mapping_path = os.path.join(index_dir, "memory_mapping.jsonl") 
        self.embedding_model_name = embedding_model 
        
        self.embedder: SentenceTransformer | None = None
        self.index: faiss.Index | None = None
        self.mapping_count: int = 0
        self.mapping: List[Dict] = []
        
        
        print("🏛️  Long Term Memory Manager (V35 - Awaiting Load) is ready.")

    async def load_models_and_index(self):
        """[V35] โหลดโมเดลและ Index (แบบ Async) และ VRAM เสถียร"""
        
        print(f"⚙️  LTM Search Embedder is initializing (Async)...")
        
        def _blocking_load_embedder():
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"    - LTM Embedder loading on CPU first...")
            embedder = SentenceTransformer(self.embedding_model_name, device="cpu")
            
            if device == "cuda":
                print("    - ⚡️ Converting LTM Embedder to FP16 (on CPU)...")
                embedder.half()
                print("    - ⚡️ Moving FP16 LTM Embedder to CUDA...")
                embedder.to(device)
            print(f"    - ✅ LTM Embedder loaded successfully (FP16: {device=='cuda'}).")
            return embedder
        
        try:
            self.embedder = await asyncio.to_thread(_blocking_load_embedder)
        except Exception as e:
            print(f"❌ LTM Searcher: Failed to load SentenceTransformer: {e}")
            return 
        print("🧠 LTM: Loading existing memory index and mapping (Async)...")
        
        def _blocking_load_index():
            if os.path.exists(self.index_path) and os.path.exists(self.mapping_path):
                try:
                    index = faiss.read_index(self.index_path)
                    with open(self.mapping_path, "r", encoding="utf-8") as f:
                        mapping = [json.loads(line) for line in f]
                    return index, mapping
                except Exception as e:
                    print(f"⚠️ LTM Searcher: Could not load memory index. Error: {e}")
            else:
                print("🟡 LTM Searcher: Memory index not found.")
            return None, []

        index, mapping = await asyncio.to_thread(_blocking_load_index)
        
        if index and mapping:
            self.index = index
            self.mapping = mapping
            if self.index.ntotal != len(self.mapping):
                print(f"⚠️ LTM Searcher: Index mismatch! (Index: {self.index.ntotal}, Mapping: {len(self.mapping)}).")
            else:
                print(f"✅ LTM Searcher: Ready with {self.index.ntotal} memories.")
        else:
            print("🟡 LTM Searcher: Search is currently disabled.")


    async def reload_index(self):
        print("🔄 LTM Searcher: Reloading memory index (Async)...")
        await self.load_models_and_index() 

    def search_relevant_memories(self, query: str, k: int = 2) -> List[Dict]:
        if self.index is None or not self.mapping or self.embedder is None: 
            print("🟡 LTM Searcher: Search disabled (Models not loaded).")
            return []
        
        print(f"🧠 LTM Searcher: Searching memories for '{query[:20]}...' (Sync in Thread)")
        try:
            query_vector = self.embedder.encode([query], convert_to_numpy=True).astype("float32")
            
            faiss.normalize_L2(query_vector)
            
            _, indices = self.index.search(query_vector, k)
            
            found_memories = [self.mapping[i] for i in indices[0] if i < len(self.mapping)]

            if found_memories:
                print(f"✅ LTM Searcher: Found {len(found_memories)} relevant memories.")
            return found_memories
        except Exception as e:
            print(f"❌ LTM Searcher: Error searching memories: {e}")
            return []
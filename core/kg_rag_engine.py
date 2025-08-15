# core/kg_rag_engine.py
# (V1.0 - Specialized Knowledge Graph Vector Search Engine)

import faiss
import json
import os
from sentence_transformers import SentenceTransformer
import torch
from typing import List, Dict, Any

class KGRAGEngine:
    def __init__(self, 
                 embedder_model: str = "intfloat/multilingual-e5-large", 
                 graph_index_path: str = "data/graph_index"):
        
        print("🕸️  เครื่องยนต์ KG-RAG กำลังเริ่มต้น...")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cuda":
            print("  - KG-RAG: ปลดล็อคขุมพลัง GPU (CUDA)")
        else:
            print(f"  - KG-RAG: ใช้ Device สำหรับ Models: {device.upper()}")
        
        self.embedder = SentenceTransformer(embedder_model, device=device)
        
        self.graph_index = None
        self.graph_mapping = None
        self._load_graph_index(graph_index_path)

        print("✅ KG-RAG Engine is ready.")

    def _load_graph_index(self, path: str):
        print("  - 🕸️  Loading Knowledge Graph Vector Base (FAISS on CPU)...")
        if not os.path.exists(path):
            print(f"    - 🟡 KG-RAG index path not found: '{path}'. Graph search will be disabled.")
            return
        try:
            faiss_path = os.path.join(path, "graph_faiss.index") 
            mapping_path = os.path.join(path, "graph_mapping.jsonl")
            
            if not os.path.exists(faiss_path) or not os.path.exists(mapping_path):
                print("    - 🟡 KG-RAG index files not found. Graph search will be disabled.")
                return

            self.graph_index = faiss.read_index(faiss_path)
            
            mapping = {}
            with open(mapping_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    mapping[str(i)] = json.loads(line)
            self.graph_mapping = mapping
            
            print(f"    - ✅ ฐานความรู้ Knowledge Graph {len(self.graph_mapping)} พร้อมใช้งาน!")
        except Exception as e:
            print(f"    - ❌ Critical error loading graph index: {e}")
            self.graph_index = None
            self.graph_mapping = None

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        ค้นหาใน Knowledge Graph โดยใช้ Vector Search โดยตรง
        """
        if not self.graph_index or not self.graph_mapping:
            return []
        
        query_vector = self.embedder.encode(["query: " + query], convert_to_numpy=True).astype("float32")
        
        distances, indices = self.graph_index.search(query_vector, top_k)
        
        results = []
        found_ids = set()
        for dist, i in zip(distances[0], indices[0]):
            if str(i) in self.graph_mapping:
                item = self.graph_mapping[str(i)].copy()
                item_id = item.get('id')
                if item_id not in found_ids:
                    item['score'] = float(dist)
                    results.append(item)
                    found_ids.add(item_id)
        return results
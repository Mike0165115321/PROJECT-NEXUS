# manage_kg_data.py
# (V1.2 - Integrated with GraphManager for robustness)

import os
import json
import faiss
from sentence_transformers import SentenceTransformer
import torch
from typing import List, Dict
from core.graph_manager import GraphManager

class KGIndexBuilder:
    def __init__(self, model_name="intfloat/multilingual-e5-large"):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"⚙️  KG Index Builder is initializing on device: {device.upper()}")
        self.model = SentenceTransformer(model_name, device=device)
        print(f"✅ Embedding model '{model_name}' loaded successfully.")
        
        self.graph_manager = GraphManager()

    def close(self):
        self.graph_manager.close()

    def fetch_all_concepts(self) -> List[Dict]:
        """
        ใช้ GraphManager เพื่อดึงข้อมูล Node ทั้งหมดที่เราต้องการจะทำ Index
        """
        if not self.graph_manager.driver:
            print("❌ Cannot fetch concepts, GraphManager is not connected.")
            return []
            
        print("\n--- 🕸️  Fetching all concepts via GraphManager... ---")
        
        query = """
        MATCH (n)
        WHERE (n:Concept OR n:Strategy OR n:Technique OR n:Risk OR n:Book)
        AND n.name IS NOT NULL AND n.description IS NOT NULL
        RETURN n.id AS id, n.name AS name, n.description AS description, labels(n) AS labels
        """
        
        all_concepts = self.graph_manager.execute_read_query(query)
        
        print(f"  - 📦 Found {len(all_concepts)} concepts to process.")
        return all_concepts

    def build_and_save_index(self, concepts: List[Dict], index_folder: str):
        if not concepts:
            print("  - 🟡 No concepts to index. Skipping.")
            return

        print(f"\n--- 🏭 Building index for {len(concepts)} concepts ---")
        os.makedirs(index_folder, exist_ok=True)
        
        texts_to_embed = []
        mapping_data = []
        
        for item in concepts:
            name = item.get("name", "")
            description = item.get("description", "")
            labels = item.get("labels", [])
            label_str = labels[0] if labels else "ข้อมูล"
            
            embedding_text = f"{label_str}เรื่อง '{name}': {description}"
            texts_to_embed.append("query: " + embedding_text)
            
            map_item = item.copy()
            map_item['embedding_text'] = embedding_text
            mapping_data.append(map_item)

        print(f"  - 🧠 Generating {len(texts_to_embed)} embeddings (using {str(self.model.device).upper()})...")
        embeddings = self.model.encode(
            texts_to_embed, 
            convert_to_numpy=True, 
            show_progress_bar=True
        ).astype("float32")
        
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)
        
        faiss.write_index(index, os.path.join(index_folder, "graph_faiss.index"))
        
        mapping_filepath = os.path.join(index_folder, "graph_mapping.jsonl")
        with open(mapping_filepath, "w", encoding="utf-8") as f:
            for item in mapping_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                
        print(f"  - ✅ Knowledge Graph index saved successfully to '{index_folder}'.")

if __name__ == "__main__":
    INDEX_FOLDER = "data/graph_index"

    print("\n" + "="*60)
    print("--- 🛠️  Starting KG-RAG Vector Base Construction  🛠️ ---")
    print("="*60)

    builder = KGIndexBuilder()
    if builder.graph_manager.driver:
        concepts_from_db = builder.fetch_all_concepts()
        builder.build_and_save_index(concepts_from_db, index_folder=INDEX_FOLDER)
        builder.close()
    else:
        print("Could not proceed without a valid Neo4j connection.")
        
    print("\n" + "="*60)
    print("✅ KG-RAG build process finished!")
    print("="*60)
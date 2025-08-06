# manage_data.py
# (V4 - The Final, GPU-Accelerated RAG Architect)

import os
import json
import faiss
from sentence_transformers import SentenceTransformer
import torch # ⭐️ 1. Import PyTorch
from typing import List, Dict
from collections import defaultdict

class RAGBuilder:
    """
    สถาปนิกผู้สร้างคลังความรู้ RAG
    รับผิดชอบการสร้าง Vector Indexes ทั้งหมดสำหรับคลังหนังสือ
    """
    def __init__(self, model_name="intfloat/multilingual-e5-large"):
        # ⭐️ 2. ตรวจจับและเปิดใช้งาน GPU ⭐️
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"⚙️  RAG Builder is initializing on device: {device.upper()}")
        
        # ส่ง device เข้าไปใน SentenceTransformer เพื่อใช้พลัง GPU
        self.model = SentenceTransformer(model_name, device=device)
        print(f"✅ Embedding model '{model_name}' loaded successfully.")

    def load_and_group_data_by_category(self, data_folder: str) -> Dict[str, List[Dict]]:
        """อ่านข้อมูลหนังสือทั้งหมดและจัดกลุ่มตามหมวดหมู่"""
        categorized_data = defaultdict(list)
        print(f"\n--- 📚 Loading and grouping book data from '{data_folder}' ---")
        
        # ... (ตรรกะส่วนนี้ของคุณดีมากอยู่แล้ว ไม่ต้องแก้ไข) ...
        for filename in sorted(os.listdir(data_folder)):
            if not filename.endswith(".jsonl"): continue
            path = os.path.join(data_folder, filename)
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        item = json.loads(line)
                        category = item.get("category", "Uncategorized").strip().replace("/", "-")
                        if item.get("content"):
                            categorized_data[category].append(item)
                    except json.JSONDecodeError: continue
        
        print(f"📦 Found {len(categorized_data)} categories to process.")
        return categorized_data

    def build_and_save_category_index(self, category: str, items: List[Dict], base_index_folder: str):
        """
        สร้างและบันทึก Index สำหรับหมวดหมู่เดียว
        """
        print(f"\n--- 🏭 Building index for category: '{category}' ---")
        safe_category_name = category.replace(" ", "_").replace("/", "-")
        category_folder = os.path.join(base_index_folder, safe_category_name)
        os.makedirs(category_folder, exist_ok=True)
        
        texts_to_embed = []
        mapping_data = [] # ใช้ List ธรรมดาจะง่ายกว่า
        
        for item in items:
            book = item.get("book_title", "N/A")
            content = item.get("content", "")
            # เพิ่ม "query: " นำหน้า content ตามคำแนะนำของโมเดล e5 เพื่อคุณภาพที่ดีขึ้น
            embedding_text = f"จากหนังสือ '{book}': {content}"
            texts_to_embed.append("query: " + embedding_text)
            
            # เก็บข้อมูลที่จำเป็นสำหรับ mapping
            item['embedding_text'] = embedding_text
            mapping_data.append(item)

        if not texts_to_embed:
            print(f"  - 🟡 No text to index for category '{category}'. Skipping.")
            return

        print(f"  - 🧠 Generating {len(texts_to_embed)} embeddings (this may take a while)...")
        embeddings = self.model.encode(
            texts_to_embed, 
            convert_to_numpy=True, 
            show_progress_bar=True
        ).astype("float32")
        
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)
        
        faiss.write_index(index, os.path.join(category_folder, "faiss.index"))
        
        mapping_filepath = os.path.join(category_folder, "mapping.jsonl")
        with open(mapping_filepath, "w", encoding="utf-8") as f:
            for item in mapping_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                
        print(f"  - ✅ Index for '{category}' saved successfully.")

if __name__ == "__main__":
    DATA_FOLDER = "data/books"
    INDEX_FOLDER = "data/index"

    print("\n" + "="*60)
    print("--- 🛠️  Starting RAG Knowledge Base Construction  🛠️ ---")
    print("="*60)

    builder = RAGBuilder()
    categorized_books = builder.load_and_group_data_by_category(data_folder=DATA_FOLDER)
    
    for category, items in categorized_books.items():
        builder.build_and_save_category_index(category, items, base_index_folder=INDEX_FOLDER)
        
    print("\n" + "="*60)
    print("✅ All category indexes have been built successfully!")
    print("="*60)
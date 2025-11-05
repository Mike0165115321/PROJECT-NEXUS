# (V4.4 - BGE-M3 Optimized & FP16 VRAM)

import os
import json
import faiss
from sentence_transformers import SentenceTransformer
import torch
import re
import shutil
from typing import List, Dict, Set
from collections import defaultdict
import numpy as np 

class RAGBuilder:
    def __init__(self, model_name="BAAI/bge-m3"):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"⚙️  RAG Builder is initializing on device: {device.upper()}")
        
        self.model = SentenceTransformer(model_name, device=device)
        
        if device == "cuda":
            print("  - ⚡️ Converting Embedding model to FP16 for VRAM efficiency...")
            self.model.half()

        print(f"✅ Embedding model '{model_name}' loaded successfully (FP16: {device=='cuda'}).")


    def _sanitize_name(self, name: str) -> str:
        name = re.sub(r'\s+', ' ', name)
        name = name.strip()
        name = re.sub(r'[/\\:*?"<>|]+', '-', name)
        return name

    def load_and_group_data_by_category(self, data_folder: str) -> Dict[str, List[Dict]]:
        categorized_data = defaultdict(list)
        print(f"\n--- 📚 Loading and grouping book data from '{data_folder}' ---")
        
        files_to_process = sorted([f for f in os.listdir(data_folder) if f.endswith(".jsonl")])
        
        if not files_to_process:
            print("  - 🟡 No new books to process.")
            return {}

        for filename in files_to_process:
            path = os.path.join(data_folder, filename)
            with open(path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        item = json.loads(line)
                        category_raw = item.get("category", "Uncategorized")
                        
                        category_clean = re.sub(r'\s+', ' ', category_raw).strip()
                        
                        item['_source_filename'] = filename
                        item['_source_line_num'] = line_num
                        if item.get("content"):
                            categorized_data[category_clean].append(item)
                    except json.JSONDecodeError: 
                        print(f"  - ⚠️ Skipping malformed JSON on line {line_num} in '{filename}'")
                        continue
        
        print(f"📦 Found {len(categorized_data)} categories to process from {len(files_to_process)} files.")
        return categorized_data

    def build_and_save_category_index(self, category: str, items: List[Dict], base_index_folder: str):
        print(f"\n--- 🏭 Building index for category: '{category}' ---")
        safe_category_name = self._sanitize_name(category)
        category_folder = os.path.join(base_index_folder, safe_category_name)
        os.makedirs(category_folder, exist_ok=True)
        
        texts_to_embed = []
        mapping_data = []
        processed_filenames: Set[str] = set()
        
        for item in items:
            book = item.get("book_title", "N/A")
            chapter = item.get("chapter_title", "")
            subsection = item.get("subsection_title", "")
            content = item.get("content", "")

            context_parts = [f"จากหนังสือ '{book}'"]
            if chapter: context_parts.append(f"บทที่ '{chapter}'")
            if subsection: context_parts.append(f"หัวข้อ '{subsection}'")
            context_str = ", ".join(context_parts)
            
            embedding_text = f"{context_str}: {content}"
            texts_to_embed.append(embedding_text)
            
            item['embedding_text'] = embedding_text
            mapping_data.append(item)
            processed_filenames.add(item['_source_filename'])

        if not texts_to_embed:
            print(f"  - 🟡 No text to index for category '{category}'. Skipping.")
            return set()

        print(f"  - 🧠 Generating {len(texts_to_embed)} embeddings (using {str(self.model.device).upper()})...")
        embeddings = self.model.encode(
            texts_to_embed, 
            convert_to_numpy=True, 
            show_progress_bar=True
        ).astype("float32")
        
        faiss.normalize_L2(embeddings)
        
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        
        faiss.write_index(index, os.path.join(category_folder, "faiss.index"))
        
        mapping_filepath = os.path.join(category_folder, "mapping.jsonl")
        with open(mapping_filepath, "w", encoding="utf-8") as f:
            for item in mapping_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                
        print(f"  - ✅ Index for '{category}' saved successfully.")
        return processed_filenames

if __name__ == "__main__":
    DATA_FOLDER = "data/books"
    INDEX_FOLDER = "data/index"
    PROCESSED_FOLDER = os.path.join(DATA_FOLDER, "_processed")
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)

    print("\n" + "="*60)
    print("--- 🛠️  Starting RAG Knowledge Base Construction (BGE-M3 / FP16) 🛠️ ---")
    print("="*60)

    builder = RAGBuilder()
    categorized_books = builder.load_and_group_data_by_category(data_folder=DATA_FOLDER)
    
    all_processed_files_in_run: Set[str] = set()

    for category, items in categorized_books.items():
        processed_files_for_category = builder.build_and_save_category_index(
            category, items, base_index_folder=INDEX_FOLDER
        )
        all_processed_files_in_run.update(processed_files_for_category)

    if all_processed_files_in_run:
        print(f"\n--- 🚀 Moving {len(all_processed_files_in_run)} processed files ---")
        for filename in sorted(list(all_processed_files_in_run)):
            source_path = os.path.join(DATA_FOLDER, filename)
            dest_path = os.path.join(PROCESSED_FOLDER, filename)
            if os.path.exists(source_path):
                shutil.move(source_path, dest_path)
                print(f"  - Moved '{filename}' to _processed folder.")
        
    print("\n" + "="*60)
    print("✅ RAG build process finished successfully!")
    print("="*60)
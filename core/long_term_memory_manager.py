# core/long_term_memory_manager.py
# (V4 - Upgraded for Groq & Centralized Config)

import sqlite3
from groq import Groq # ⭐️ 1. เปลี่ยนมาใช้ Groq
import faiss
import json
import os
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

class LongTermMemoryManager:
    def __init__(self, key_manager, model_name: str,
                 db_path: str = "data/memory.db", 
                 index_path: str = "data/memory_index/memory_faiss.index",
                 mapping_path: str = "data/memory_index/memory_mapping.json"):
        
        self.db_path = db_path
        self.index_path = index_path
        self.mapping_path = mapping_path
        self.key_manager = key_manager
        self.model_name = model_name
        self._init_db()

        self.embedder = SentenceTransformer("intfloat/multilingual-e5-large")
        self.index = None
        self.mapping = None
        self._load_existing_index()
        print("🏛️  Long Term Memory Manager (V4 - Groq) is ready.")

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS long_term_memories (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    keywords TEXT,
                    UNIQUE(session_id, title)
                )
            ''')
        print("🗄️  LTM DB Table (Structured) is ready.")

    def _load_existing_index(self):
        if os.path.exists(self.index_path) and os.path.exists(self.mapping_path):
            try:
                print("🧠 LTM: Loading existing memory index...")
                self.index = faiss.read_index(self.index_path)
                with open(self.mapping_path, "r", encoding="utf-8") as f:
                    self.mapping = json.load(f)
                print("✅ LTM: Memory RAG system is ready.")
            except Exception as e:
                print(f"⚠️ LTM: Could not load memory index. Error: {e}")
        else:
            print("🟡 LTM: Memory index not found. Will be created after first summarization.")

    def _add_structured_memory(self, memory: Dict, session_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO long_term_memories (session_id, title, summary, keywords) VALUES (?, ?, ?, ?)",
                (session_id, memory.get("title"), memory.get("summary"), ", ".join(memory.get("keywords", [])))
            )

    def _get_all_memories_from_db(self, session_id: str) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT title, summary, keywords FROM long_term_memories WHERE session_id = ? ORDER BY id", (session_id,))
            return [dict(row) for row in cursor.fetchall()]

    async def _rebuild_index_from_db(self, session_id: str):
        print("🧠 LTM: Rebuilding memory index from all memories...")
        memories = self._get_all_memories_from_db(session_id)
        if not memories:
            print("🟡 LTM: No memories in DB to build index.")
            return

        texts_to_embed = [f"หัวข้อ: {mem.get('title', '')}\nสรุป: {mem.get('summary', '')}" for mem in memories]
        embeddings = self.embedder.encode(texts_to_embed, convert_to_numpy=True).astype("float32")
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)
        mapping = {str(i): memory for i, memory in enumerate(memories)}
        
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(index, self.index_path)
        with open(self.mapping_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
            
        self.index = index
        self.mapping = mapping
        print("✅ LTM: Memory index rebuilt and reloaded successfully!")

    async def process_and_add_memory(self, conversation: List[Dict[str, Any]], session_id: str):
        """
        ประมวลผลบทสนทนาเพื่อสกัดและบันทึกเป็นความทรงจำระยะยาว
        """
        if not self.key_manager or len(conversation) < 2: return
        print("🏛️  LTM: Processing conversation for structured memory...")
        
        try:
            api_key = self.key_manager.get_key()
            client = Groq(api_key=api_key)

            full_transcript = "\n".join([f"- {turn.get('role')}: {turn.get('content')}" for turn in conversation])
            prompt = f"""
คุณคือ AI ผู้เชี่ยวชาญด้านการย่อยข้อมูล (Data Distiller) ภารกิจของคุณคือการวิเคราะห์บทสนทนาต่อไปนี้ และสกัด "แก่นของความทรงจำ" ออกมาในรูปแบบ JSON object ที่มีโครงสร้างชัดเจน

**โครงสร้าง JSON ที่ต้องการ:**
{{
  "title": "หัวข้อหลักของความทรงจำนี้ (4-5 คำ)",
  "summary": "สรุปใจความสำคัญของสิ่งที่ได้เรียนรู้หรือตัดสินใจ (1-2 ประโยค)",
  "keywords": ["คำสำคัญที่เกี่ยวข้อง 3-5 คำ"]
}}

**กฎ:**
- ตอบกลับเป็น JSON object ที่สมบูรณ์เท่านั้น ห้ามมีข้อความอื่นใดๆ

**บทสนทนาเพื่อวิเคราะห์:**
---
{full_transcript}
---

**ผลลัพธ์ (JSON Output):**
"""
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                response_format={"type": "json_object"}
            )
            
            json_str = chat_completion.choices[0].message.content
            memory_data = json.loads(json_str)
            
            if isinstance(memory_data, dict) and memory_data.get("title") and memory_data.get("summary"):
                print(f"  -> New Memory Archived: {memory_data['title']}")
                self._add_structured_memory(memory_data, session_id)
                self._rebuild_index_from_db(session_id)

        except Exception as e:
            print(f"❌ LTM: Failed to process structured memory: {e}")

    def search_relevant_memories(self, query: str, session_id: str = "default_user", k: int = 2) -> List[Dict]:
        if not self.index or not self.mapping: return [] 
        print(f"🧠 LTM: Searching memories for '{query[:20]}...'")
        try:
            query_vector = self.embedder.encode([query]).astype("float32")
            _, indices = self.index.search(query_vector, k)
            found_memories = [self.mapping.get(str(i)) for i in indices[0] if self.mapping.get(str(i))]
            if found_memories:
                print(f"✅ LTM: Found {len(found_memories)} relevant memories.")
            return found_memories
        except Exception as e:
            print(f"❌ LTM: Error searching memories: {e}")
            return []
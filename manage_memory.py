# manage_memory.py
# (V11 - The Final, Timestamp-Aware Processor)

import sqlite3
from groq import Groq
import faiss
import json
import os
import torch
import time
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from core.config import settings
from core.groq_key_manager import GroqApiKeyManager, AllGroqKeysOnCooldownError
import numpy as np
import traceback

class MemoryConsolidator:
    def __init__(self, key_manager: GroqApiKeyManager, ltm_model: str, embedding_model_name: str):
        print("\n" + "="*60)
        print("--- 🏛️  Initializing Memory Consolidation Process (V11 - Timestamp-Aware)  🏛️ ---")
        print("="*60)
        
        self.DB_PATH = "data/memory.db"
        self.MEMORY_INDEX_DIR = "data/memory_index"
        self.MEMORY_FAISS_PATH = os.path.join(self.MEMORY_INDEX_DIR, "memory_faiss.index")
        self.MEMORY_MAPPING_PATH = os.path.join(self.MEMORY_INDEX_DIR, "memory_mapping.jsonl")
        
        self.key_manager = key_manager
        self.ltm_model_name = ltm_model
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"⚙️  Initializing embedder on device: {device.upper()}")
        self.embedding_model = SentenceTransformer(embedding_model_name, device=device)
        print(f"✅ Embedding model '{embedding_model_name}' loaded successfully.")

        self._ensure_db_schema()

    def _ensure_db_schema(self):
        """[UPGRADE] เพิ่มคอลัมน์สำหรับเก็บ 'ช่วงเวลา' ของบทสนทนา"""
        with sqlite3.connect(self.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_processing_state (
                    session_id TEXT PRIMARY KEY, last_processed_id INTEGER NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
                    title TEXT NOT NULL, summary TEXT NOT NULL, keywords TEXT,
                    start_message_id INTEGER, end_message_id INTEGER,
                    conversation_start_time TIMESTAMP,
                    conversation_end_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY, timestamp DATETIME NOT NULL, session_id TEXT NOT NULL,
                    role TEXT NOT NULL, content TEXT NOT NULL, agent_used TEXT
                )
            ''')
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ltm_session_id ON long_term_memories(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ch_session_id ON conversation_history(session_id)")
            conn.commit()
            print("🗄️  LTM DB Schema (V11 - Timestamp-Aware) is ready.")

    def get_unprocessed_conversation_chunks(self, num_sessions: int = 5, chunk_size: int = 20) -> List[Dict[str, Any]]:
        chunks_to_process = []
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT T1.session_id, COALESCE(T2.last_processed_id, 0) as last_processed_id
                    FROM (SELECT DISTINCT session_id FROM conversation_history) T1
                    LEFT JOIN memory_processing_state T2 ON T1.session_id = T2.session_id
                    WHERE (SELECT MAX(id) FROM conversation_history WHERE session_id = T1.session_id) > COALESCE(T2.last_processed_id, 0)
                    LIMIT ?
                """, (num_sessions,))
                sessions = cursor.fetchall()

                if not sessions: return []
                print(f"🔍 Found {len(sessions)} active sessions with new messages.")
                for session in sessions:
                    session_id, last_id = session['session_id'], session['last_processed_id']
                    cursor.execute(
                        "SELECT id, role, content, timestamp FROM conversation_history WHERE session_id = ? AND id > ? ORDER BY id LIMIT ?",
                        (session_id, last_id, chunk_size)
                    )
                    messages = [dict(row) for row in cursor.fetchall()]
                    if messages:
                        chunks_to_process.append({
                            "session_id": session_id, "messages": messages,
                            "start_message_id": messages[0]['id'], "end_message_id": messages[-1]['id'],
                            "conversation_start_time": messages[0]['timestamp'],
                            "conversation_end_time": messages[-1]['timestamp']
                        })
                return chunks_to_process
        except Exception as e:
            print(f"❌ Could not retrieve conversation chunks: {e}")
            return []

    def extract_structured_memories(self, conversation_chunks: List[Dict[str, Any]]) -> (List[Dict], List[Dict]):
        if not conversation_chunks: return [], []
        successful_memories, failed_chunks = [], []
        print(f"🧠 Processing {len(conversation_chunks)} conversation chunks...")
        prompt_template = """
คุณคือ AI ผู้เชี่ยวชาญด้านการย่อยข้อมูล (Data Distiller) ภารกิจของคุณคือการวิเคราะห์บทสนทนาทั้งหมด และสกัด "แก่นของความทรงจำ" ที่สำคัญที่สุดออกมา

**กฎ:**
- **ตอบกลับเป็น JSON object ที่สมบูรณ์เท่านั้น** ห้ามมีข้อความอื่นใดๆ

**โครงสร้าง JSON ที่ต้องการ:**
{{
  "title": "หัวข้อหลักของความทรงจำนี้ (4-5 คำ)",
  "summary": "สรุปใจความสำคัญของสิ่งที่ได้เรียนรู้หรือตัดสินใจในบทสนทนานี้ (1-2 ประโยค)",
  "keywords": ["คำสำคัญที่เกี่ยวข้อง 3-5 คำ"]
}}

**บทสนทนาเพื่อวิเคราะห์:**
---
{transcript}
---

**ผลลัพธ์ (JSON Object เท่านั้น):**
"""
        for chunk in conversation_chunks:
            api_key = None
            try:
                api_key = self.key_manager.get_key()
                client = Groq(api_key=api_key)
                transcript = "\n".join([f"- {msg['role']}: {msg['content']}" for msg in chunk['messages']])
                prompt = prompt_template.format(transcript=transcript)

                print(f"  - Processing chunk for session: {chunk['session_id']} (messages {chunk['start_message_id']}-{chunk['end_message_id']})...")
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}], model=self.ltm_model_name,
                    response_format={"type": "json_object"}
                )
                memory_data = json.loads(chat_completion.choices[0].message.content)
                if isinstance(memory_data, dict):
                    memory_data.update(chunk)
                    successful_memories.append(memory_data)
            except AllGroqKeysOnCooldownError as e:
                raise e
            except Exception as e:
                print(f"  ❌ Error processing chunk for session {chunk['session_id']}: {e}")
                if api_key: self.key_manager.report_failure(api_key)
                failed_chunks.append(chunk)
                
        print(f"✅ Extracted {len(successful_memories)} memories. Failed chunks: {len(failed_chunks)}")
        return successful_memories, failed_chunks

    def save_memories_and_update_index(self, memories: List[Dict]):
        if not memories: return
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                for mem in memories:
                    cursor.execute(
                        """INSERT INTO long_term_memories (session_id, title, summary, keywords, start_message_id, end_message_id, conversation_start_time, conversation_end_time) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (mem['session_id'], mem['title'], mem['summary'], ", ".join(mem.get('keywords', [])), 
                         mem['start_message_id'], mem['end_message_id'], 
                         mem['conversation_start_time'], mem['conversation_end_time'])
                    )
                    cursor.execute(
                        "INSERT INTO memory_processing_state (session_id, last_processed_id) VALUES (?, ?) ON CONFLICT(session_id) DO UPDATE SET last_processed_id = excluded.last_processed_id",
                        (mem['session_id'], mem['end_message_id'])
                    )
                conn.commit()
                print(f"💾 Saved {len(memories)} new memories (with timestamps) and updated processing state.")
        except Exception as e:
            print(f"❌ Could not save memories to DB: {e}")
            traceback.print_exc()
            return

        texts_to_embed = [f"หัวข้อ: {mem.get('title', '')}\nสรุป: {mem.get('summary', '')}" for mem in memories]
        new_embeddings = self.embedding_model.encode(["passage: " + text for text in texts_to_embed], show_progress_bar=True, convert_to_numpy=True).astype("float32")
        
        os.makedirs(self.MEMORY_INDEX_DIR, exist_ok=True)
        if os.path.exists(self.MEMORY_FAISS_PATH):
            index = faiss.read_index(self.MEMORY_FAISS_PATH)
            index.add(new_embeddings)
            with open(self.MEMORY_MAPPING_PATH, "a", encoding="utf-8") as f:
                for memory in memories: f.write(json.dumps(memory, ensure_ascii=False) + "\n")
        else:
            index = faiss.IndexFlatL2(new_embeddings.shape[1])
            index.add(new_embeddings)
            with open(self.MEMORY_MAPPING_PATH, "w", encoding="utf-8") as f:
                for memory in memories: f.write(json.dumps(memory, ensure_ascii=False) + "\n")
            
        faiss.write_index(index, self.MEMORY_FAISS_PATH)
        print(f"✅ Memory RAG Index updated successfully! Total memories: {index.ntotal}")

    def _skip_failed_chunks(self, failed_chunks: List[Dict]):
        if not failed_chunks: return
        print(f"⏭️  Skipping {len(failed_chunks)} failed chunks by updating their processing state...")
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                for chunk in failed_chunks:
                    cursor.execute(
                        "INSERT INTO memory_processing_state (session_id, last_processed_id) VALUES (?, ?) ON CONFLICT(session_id) DO UPDATE SET last_processed_id = excluded.last_processed_id",
                        (chunk['session_id'], chunk['end_message_id'])
                    )
                conn.commit()
            print("✅ Failed chunks have been skipped.")
        except Exception as e:
            print(f"❌ Could not update state for failed chunks: {e}")

    def run_one_batch(self, num_sessions: int = 5, chunk_size: int = 20) -> bool:
        unprocessed_chunks = self.get_unprocessed_conversation_chunks(num_sessions=num_sessions, chunk_size=chunk_size) 
        if not unprocessed_chunks:
            return False

        successful_memories, failed_chunks = self.extract_structured_memories(unprocessed_chunks)
        
        if successful_memories:
            self.save_memories_and_update_index(successful_memories)
        
        if failed_chunks:
            self._skip_failed_chunks(failed_chunks)
        
        return True

def main():
    try:
        key_manager = GroqApiKeyManager(all_groq_keys=settings.GROQ_API_KEYS, silent=True)
        consolidator = MemoryConsolidator(
            key_manager=key_manager, ltm_model=settings.LTM_MODEL,
            embedding_model_name="intfloat/multilingual-e5-large"
        )
        
        while True:
            print("\n" + "-"*20 + " Starting a new processing run " + "-"*20)
            more_work_found = consolidator.run_one_batch(num_sessions=5, chunk_size=15)
            if not more_work_found:
                print("\n🎉 All sessions are fully processed and up-to-date!")
                break
            print("...More messages might exist, starting next run in 1 second...")
            time.sleep(1)
    except AllGroqKeysOnCooldownError as e:
        print(f"\n🔥🔥🔥 API KEYS EXHAUSTED - CRITICAL FAILURE 🔥🔥🔥")
        print(f"   -> Reason: {e}")
        print(f"   -> Halting the process. Rerun the script later to continue from where it left off.")
    except Exception as e:
        print(f"❌ A critical error occurred in the main process: {e}")
        traceback.print_exc()
    finally:
        print("\n" + "="*60)
        print("--- 🏛️  Memory Consolidation Process Finished  🏛️ ---")
        print("="*60)

if __name__ == "__main__":
    main()
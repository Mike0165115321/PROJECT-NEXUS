# manage_memory.py
# (V12.1 - Standardized Builder Architecture, No-LLM)

import sqlite3
import faiss
import json
import os
import torch
import time
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import re

class MemoryBuilder:
    def __init__(self, model_name="intfloat/multilingual-e5-large"):
        self.DB_PATH = "data/memory.db"
        self.MEMORY_INDEX_DIR = "data/memory_index"
        self.MEMORY_FAISS_PATH = os.path.join(self.MEMORY_INDEX_DIR, "memory_faiss.index")
        self.MEMORY_MAPPING_PATH = os.path.join(self.MEMORY_INDEX_DIR, "memory_mapping.jsonl")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"⚙️  Memory Builder is initializing on device: {device.upper()}")
        self.model = SentenceTransformer(model_name, device=device)
        print(f"✅ Embedding model '{model_name}' loaded successfully.")

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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS archived_conversations (
                    id INTEGER, timestamp DATETIME, session_id TEXT,
                    role TEXT, content TEXT, agent_used TEXT,
                    PRIMARY KEY (session_id, id)
                )
            """)
            conn.commit()
            print("🗄️  LTM DB Schema (V12.3 - Archiving) is ready.")
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
                    WITH SessionMaxID AS (
                        SELECT session_id, MAX(id) as max_id
                        FROM conversation_history
                        GROUP BY session_id
                    )
                    SELECT T1.session_id, COALESCE(T2.last_processed_id, 0) as last_processed_id
                    FROM SessionMaxID T1
                    LEFT JOIN memory_processing_state T2 ON T1.session_id = T2.session_id
                    WHERE T1.max_id > COALESCE(T2.last_processed_id, 0)
                    ORDER BY T1.session_id
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

    def extract_memories_from_chunks(self, conversation_chunks: List[Dict[str, Any]]) -> List[Dict]:
        if not conversation_chunks: return []
        
        print(f"\n--- ✍️  Extracting memories from {len(conversation_chunks)} chunks (Rule-based)... ---")
        successful_memories = []
        
        for chunk in conversation_chunks:
            try:
                user_messages = [msg['content'] for msg in chunk['messages'] if msg['role'] == 'user']
                model_messages = [msg['content'] for msg in chunk['messages'] if msg['role'] == 'model']

                if not user_messages or not model_messages: continue

                title = user_messages[0][:100]
                summary = model_messages[-1]
                keywords = list(set(re.findall(r'\b\w{4,}\b', title.lower())))[:5]

                memory_data = {
                    "title": title, "summary": summary, "keywords": keywords
                }
                memory_data.update(chunk)
                successful_memories.append(memory_data)
            except Exception as e:
                print(f"  - ⚠️ Error processing chunk for session {chunk['session_id']} with rules: {e}")
        
        print(f"  - ✅ Extracted {len(successful_memories)} memories successfully.")
        return successful_memories

    def save_memories_to_db(self, memories: List[Dict]):
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
                conn.commit()
                print(f"  - 💾 Saved {len(memories)} new memories to database.")
        except Exception as e:
            print(f"  - ❌ Could not save memories to DB: {e}")

    def update_processing_state(self, chunks: List[Dict]):
        if not chunks: return
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                for chunk in chunks:
                    cursor.execute(
                        "INSERT INTO memory_processing_state (session_id, last_processed_id) VALUES (?, ?) ON CONFLICT(session_id) DO UPDATE SET last_processed_id = excluded.last_processed_id",
                        (chunk['session_id'], chunk['end_message_id'])
                    )
                conn.commit()
            print(f"  - 🔄 Updated processing state for {len(chunks)} chunks.")
        except Exception as e:
            print(f"  - ❌ Could not update processing state: {e}")

    def build_and_save_index(self, memories: List[Dict]):
        if not memories:
            print("  - 🟡 No new memories to index.")
            return

        print(f"\n--- 🏭 Building/Updating Memory RAG Index ---")
        os.makedirs(self.MEMORY_INDEX_DIR, exist_ok=True)
        
        texts_to_embed = []
        mapping_data = []
        for mem in memories:
            embedding_text = f"หัวข้อ: {mem.get('title', '')}\nสรุป: {mem.get('summary', '')}"
            texts_to_embed.append("passage: " + embedding_text)
            
            mem_copy = mem.copy()
            mem_copy['embedding_text'] = embedding_text
            mapping_data.append(mem_copy)

        print(f"  - 🧠 Generating {len(texts_to_embed)} new embeddings (using {str(self.model.device).upper()})...")
        new_embeddings = self.model.encode(
            texts_to_embed, 
            show_progress_bar=True, 
            convert_to_numpy=True
        ).astype("float32")
        
        if os.path.exists(self.MEMORY_FAISS_PATH):
            print("  -  appending to existing index...")
            index = faiss.read_index(self.MEMORY_FAISS_PATH)
            index.add(new_embeddings)
            with open(self.MEMORY_MAPPING_PATH, "a", encoding="utf-8") as f:
                for item in mapping_data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
        else:
            print("  - creating new index...")
            index = faiss.IndexFlatL2(new_embeddings.shape[1])
            index.add(new_embeddings)
            with open(self.MEMORY_MAPPING_PATH, "w", encoding="utf-8") as f:
                for item in mapping_data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
        faiss.write_index(index, self.MEMORY_FAISS_PATH)
        print(f"  - ✅ Memory RAG Index updated successfully! Total memories in index: {index.ntotal}")
    def archive_processed_conversations(self, chunks: List[Dict]):
        """
        ย้ายข้อความดิบใน conversation_history ที่ถูกประมวลผลแล้ว
        ไปเก็บไว้ในตาราง archived_conversations
        """
        if not chunks: return
        
        print(f"\n--- 🗄️  Archiving {len(chunks)} processed conversation chunks... ---")
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                total_moved = 0
                for chunk in chunks:
                    session_id = chunk['session_id']
                    start_id = chunk['start_message_id']
                    end_id = chunk['end_message_id']
                    
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO archived_conversations (id, timestamp, session_id, role, content, agent_used)
                        SELECT id, timestamp, session_id, role, content, agent_used
                        FROM conversation_history
                        WHERE session_id = ? AND id BETWEEN ? AND ?
                        """,
                        (session_id, start_id, end_id)
                    )
                    
                    cursor.execute(
                        "DELETE FROM conversation_history WHERE session_id = ? AND id BETWEEN ? AND ?",
                        (session_id, start_id, end_id)
                    )
                    
                    total_moved += cursor.rowcount
                
                conn.commit()
                print(f"  - ✅ Archived and cleaned up {total_moved} old messages.")
        except Exception as e:
            print(f"  - ❌ Could not archive processed conversations: {e}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("--- 🏛️  Starting Memory Consolidation & Indexing Process  🏛️ ---")
    print("="*60)

    builder = MemoryBuilder()
    
    all_new_memories = []
    all_processed_chunks_for_archiving = []
    
    while True:
        print("\n" + "-"*20 + " Searching for new conversation chunks " + "-"*20)
        
        unprocessed_chunks = builder.get_unprocessed_conversation_chunks(num_sessions=10, chunk_size=20)
        if not unprocessed_chunks:
            print("\n✅ No more unprocessed chunks found.")
            break
        
        new_memories = builder.extract_memories_from_chunks(unprocessed_chunks)
        builder.update_processing_state(unprocessed_chunks)

        if new_memories:
            all_new_memories.extend(new_memories)
            all_processed_chunks_for_archiving.extend(unprocessed_chunks)
            print(f"  - Staged {len(new_memories)} new memories for batch processing.")

        print("...Searching for more messages...")
        time.sleep(1)

    if all_new_memories:
        print("\n" + "="*60)
        print(f"--- 🏛️  Committing {len(all_new_memories)} new memories to storage (Batch Operation)  🏛️ ---")
        print("="*60)
        
        builder.save_memories_to_db(all_new_memories)
        builder.build_and_save_index(all_new_memories)
        builder.archive_processed_conversations(all_processed_chunks_for_archiving)
    else:
        print("\n🎉 All sessions are fully processed and up-to-date!")

    print("\n" + "="*60)
    print("--- 🏛️  Memory Consolidation Process Finished  🏛️ ---")
    print("="*60)
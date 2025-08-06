# manage_memory.py
# (V4 - The Final, Complete, GPU-Accelerated & Groq-Powered Version)

import sqlite3
from groq import Groq
import faiss
import json
import os
import torch
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from core.config import settings
from core.groq_key_manager import GroqApiKeyManager
import numpy as np
from datetime import datetime

# --- ค่าคงที่ ---
DB_PATH = "data/memory.db"
MEMORY_INDEX_DIR = "data/memory_index"
MEMORY_FAISS_PATH = os.path.join(MEMORY_INDEX_DIR, "memory_faiss.index")
MEMORY_MAPPING_PATH = os.path.join(MEMORY_INDEX_DIR, "memory_mapping.json")

# --- 1. ฟังก์ชันดึงข้อมูล ---
def get_unprocessed_conversations(batch_size: int = 50) -> Dict[str, List[Dict[str, Any]]]:
    """
    ดึงบทสนทนาที่ยังไม่ถูกประมวลผลจาก memory.db
    และจัดกลุ่มตาม session_id
    """
    grouped_conversations = {}
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # ดึง session_id ที่ยังไม่มีใน LTM มาทำก่อน
            cursor.execute("""
                SELECT DISTINCT T1.session_id
                FROM conversation_history T1
                LEFT JOIN long_term_memories T2 ON T1.session_id = T2.session_id
                WHERE T2.session_id IS NULL
                LIMIT ?
            """, (batch_size,))
            
            sessions_to_process = [row['session_id'] for row in cursor.fetchall()]
            
            if not sessions_to_process:
                return {}

            print(f"🔍 Found {len(sessions_to_process)} new conversation sessions to process.")
            
            for session_id in sessions_to_process:
                cursor.execute(
                    "SELECT id, role, content, timestamp FROM conversation_history WHERE session_id = ? ORDER BY id",
                    (session_id,)
                )
                entries = [dict(row) for row in cursor.fetchall()]
                if entries:
                    grouped_conversations[session_id] = entries
            return grouped_conversations
    except Exception as e:
        print(f"❌ Could not retrieve conversations from STM: {e}")
        return {}

# --- 2. ฟังก์ชันสกัดความทรงจำ ---
def extract_structured_memories(
    conversations_by_session: Dict[str, List[Dict[str, Any]]], 
    key_manager: GroqApiKeyManager,
    model_name: str
) -> List[Dict[str, Any]]:
    
    if not conversations_by_session: return []
    
    all_structured_memories = []
    print(f"🧠 Processing {len(conversations_by_session)} sessions to create long-term memories...")
    
    prompt_template = """
คุณคือ AI ผู้เชี่ยวชาญด้านการย่อยข้อมูล (Data Distiller) ภารกิจของคุณคือการวิเคราะห์บทสนทนาทั้งหมด และสกัด "แก่นของความทรงจำ" ที่สำคัญที่สุดออกมาในรูปแบบ JSON object

**โครงสร้าง JSON ที่ต้องการ:**
{{
  "title": "หัวข้อหลักของความทรงจำนี้ (4-5 คำ)",
  "summary": "สรุปใจความสำคัญของสิ่งที่ได้เรียนรู้หรือตัดสินใจในบทสนทนานี้ (1-2 ประโยค)",
  "keywords": ["คำสำคัญที่เกี่ยวข้อง 3-5 คำ"]
}}

**กฎ:**
- ตอบกลับเป็น JSON object ที่สมบูรณ์เท่านั้น ห้ามมีข้อความอื่นใดๆ

**บทสนทนาเพื่อวิเคราะห์:**
---
{transcript}
---

**ผลลัพธ์ (JSON Output):**
"""

    for session_id, conversation in conversations_by_session.items():
        api_key = key_manager.get_key()
        if not api_key:
            print("❌ Cannot proceed: No available Groq API keys.")
            break
        try:
            client = Groq(api_key=api_key)
            full_transcript = "\n".join([f"- {turn.get('role')}: {turn.get('content')}" for turn in conversation])
            prompt = prompt_template.format(transcript=full_transcript)
            
            print(f"  - Processing session: {session_id} with Key '...{api_key[-4:]}'")
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model_name,
                response_format={"type": "json_object"}
            )
            
            memory_data = json.loads(chat_completion.choices[0].message.content)
            
            if isinstance(memory_data, dict) and memory_data.get("title") and memory_data.get("summary"):
                memory_data['session_id'] = session_id
                # (สามารถเพิ่มตรรกะการประมวลผล timestamp ได้ที่นี่ถ้าต้องการ)
                all_structured_memories.append(memory_data)
            else:
                print(f"  ⚠️ Skipped session {session_id}: Invalid JSON structure.")

        except Exception as e:
            print(f"  ❌ Error processing session {session_id}: {e}")
            
    print(f"✅ Extracted {len(all_structured_memories)} structured memories.")
    return all_structured_memories

# --- 3. ฟังก์ชันบันทึกและสร้าง Index ---
def save_memories_and_build_index(memories: List[Dict]):
    if not memories:
        print("🟡 No new memories to save or index.")
        return

    # --- ส่วนที่ 3A: บันทึกลง DB ---
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            for mem in memories:
                cursor.execute(
                    "INSERT OR REPLACE INTO long_term_memories (session_id, title, summary, keywords) VALUES (?, ?, ?, ?)",
                    (mem.get("session_id"), mem.get("title"), mem.get("summary"), ", ".join(mem.get("keywords", [])))
                )
            conn.commit()
            print(f"💾 Saved {len(memories)} new memories to long_term_memories table.")
    except Exception as e:
        print(f"❌ Could not save structured memories to DB: {e}")
        return # ถ้าบันทึก DB ไม่ได้ ก็ไม่ควรสร้าง Index ต่อ

    # --- ส่วนที่ 3B: สร้าง/อัปเดต Index ---
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n⚙️  Initializing embedder on device: {device.upper()}")
    model = SentenceTransformer("intfloat/multilingual-e5-large", device=device)
    
    texts_to_embed = [f"หัวข้อ: {mem.get('title', '')}\nสรุป: {mem.get('summary', '')}" for mem in memories]
    
    print(f"🧠 Generating embeddings for {len(texts_to_embed)} new memories...")
    new_embeddings = model.encode(
        ["passage: " + text for text in texts_to_embed], 
        show_progress_bar=True, 
        convert_to_numpy=True
    ).astype("float32")
    
    os.makedirs(MEMORY_INDEX_DIR, exist_ok=True)
    
    if os.path.exists(MEMORY_FAISS_PATH):
        print("🔄️ Found existing index, updating...")
        index = faiss.read_index(MEMORY_FAISS_PATH)
        with open(MEMORY_MAPPING_PATH, "r", encoding="utf-8") as f:
            mapping = json.load(f)
        start_index = len(mapping)
        index.add(new_embeddings)
        for i, memory in enumerate(memories):
            mapping[str(start_index + i)] = memory
    else:
        print("✨ No existing index found, creating new one...")
        dimension = new_embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(new_embeddings)
        mapping = {str(i): memory for i, memory in enumerate(memories)}
        
    faiss.write_index(index, MEMORY_FAISS_PATH)
    with open(MEMORY_MAPPING_PATH, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=4)
        
    print(f"\n✅ Memory RAG Index updated/created successfully! Total memories: {index.ntotal}")

# --- Main Execution Block ---
if __name__ == "__main__":
    print("\n" + "="*60)
    print("--- 🏛️  Starting Memory Consolidation Process (STM -> LTM)  🏛️ ---")
    print("="*60)
    
    key_manager = GroqApiKeyManager(all_groq_keys=settings.GROQ_API_KEYS)
    model_to_use = settings.LTM_MODEL

    # 1. ดึงบทสนทนาที่ยังไม่เคยถูกประมวลผล
    unprocessed_sessions = get_unprocessed_conversations(batch_size=50) 

    if unprocessed_sessions:
        # 2. สกัดเป็นความทรงจำที่มีโครงสร้าง
        structured_memories = extract_structured_memories(
            unprocessed_sessions, 
            key_manager=key_manager,
            model_name=model_to_use
        )
        
        if structured_memories:
            # 3. บันทึกและสร้าง Index
            save_memories_and_build_index(structured_memories)
            
            print("\n✅ Batch processing complete!")
    else:
        print("\n✅ No new conversation sessions in STM to process.")

    print("\n" + "="*60)
    print("--- 🏛️  Memory Consolidation Process Finished  🏛️ ---")
    print("="*60)
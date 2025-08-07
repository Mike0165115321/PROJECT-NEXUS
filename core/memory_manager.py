# core/memory_manager.py
# (V2.1 - Robust & Optimized)

import sqlite3
import datetime
import time
import re # ⭐️ Import re for robust matching
from typing import List, Dict, Optional, Any

# [CLARITY] ย้าย Magic Numbers มาเป็นค่าคงที่
DEFAULT_HISTORY_LIMIT = 15
PENDING_TASK_TIMEOUT_SECONDS = 300

class MemoryManager:
    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        self._init_db()
        self.pending_tasks: Dict[str, Any] = {}

    def _init_db(self):
        """
        [FINAL VERSION] สร้างและอัปเดต Schema ของฐานข้อมูลด้วยวิธีที่แข็งแกร่งที่สุด
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversation_history (
                        id INTEGER PRIMARY KEY, timestamp DATETIME NOT NULL, session_id TEXT NOT NULL,
                        role TEXT NOT NULL, content TEXT NOT NULL, agent_used TEXT
                    )
                ''')
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ch_session_id_id ON conversation_history(session_id, id)")
                try:
                    cursor.execute("ALTER TABLE conversation_history ADD COLUMN agent_used TEXT")
                    print("🗄️  Upgraded DB: Added 'agent_used' column.")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        pass 
                    else:
                        raise e

            print("🗄️ คลังเก็บเรื่องราว (memory.db) พร้อมใช้งาน")
        except Exception as e:
            print(f"❌ Error initializing Memory DB: {e}")
            
    def add_memory(self, role: str, content: str, session_id: str = "default_user", agent_used: Optional[str] = None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                timestamp = datetime.datetime.now()
                cursor.execute(
                    "INSERT INTO conversation_history (timestamp, session_id, role, content, agent_used) VALUES (?, ?, ?, ?, ?)",
                    (timestamp, session_id, role, content, agent_used)
                )
        except Exception as e:
            print(f"❌ Could not save memory: {e}")

    def get_last_n_memories(self, n: int = DEFAULT_HISTORY_LIMIT, session_id: str = "default_user") -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT role, content, agent_used FROM conversation_history WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                    (session_id, n)
                )
                history = [dict(row) for row in cursor.fetchall()]
                return list(reversed(history))
        except Exception as e:
            print(f"❌ Could not retrieve memory: {e}")
            return []

    def set_pending_deep_dive(self, session_id: str, original_query: str):
        print(f"⏳ [Memory] Setting pending deep dive for user '{session_id}' on query: '{original_query}'")
        self.pending_tasks[session_id] = {
            "type": "DEEP_DIVE_CONFIRMATION",
            "original_query": original_query,
            "timestamp": time.time()
        }

    def check_and_clear_pending_deep_dive(self, session_id: str, user_confirmation: str) -> Optional[str]:
        pending = self.pending_tasks.get(session_id)
        if not pending or pending.get("type") != "DEEP_DIVE_CONFIRMATION":
            return None

        if time.time() - pending.get("timestamp", 0) > PENDING_TASK_TIMEOUT_SECONDS:
            print(f"🗑️ [Memory] Pending task for user '{session_id}' expired.")
            del self.pending_tasks[session_id]
            return None

        # [ROBUSTNESS] ทำให้การตรวจสอบการยืนยัน/ปฏิเสธฉลาดขึ้น
        cleaned_input = user_confirmation.lower().strip()
        
        # ตรวจสอบคำปฏิเสธก่อน
        denial_keywords = ["ไม่", "ปฏิเสธ", "อย่า", "หยุด", "พอแล้ว"]
        if any(keyword in cleaned_input for keyword in denial_keywords):
             print(f"❌ [Memory] User '{session_id}' denied deep dive. Clearing pending task.")
             del self.pending_tasks[session_id]
             return None

        # ตรวจสอบคำยืนยัน (ใช้ Regex เพื่อหาคำที่สมบูรณ์)
        confirmation_pattern = r'\b(ใช่|ครับ|ค่ะ|เอาเลย|จัดมา|เจาะลึก|ตกลง|แน่นอน|ได้เลย|ต้องการ)\b'
        if re.search(confirmation_pattern, cleaned_input):
            original_query = pending["original_query"]
            print(f"✅ [Memory] User '{session_id}' confirmed deep dive. Clearing pending task.")
            del self.pending_tasks[session_id]
            return original_query

        # ถ้าไม่เข้าเงื่อนไขไหนเลย ถือว่าไม่ยืนยัน
        print(f"❔ [Memory] User '{session_id}' gave an unclear response. Clearing pending task.")
        del self.pending_tasks[session_id]
        return None

    def get_last_user_query(self, session_id: str = "default_user") -> str:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT content FROM conversation_history WHERE session_id = ? AND role = 'user' ORDER BY id DESC LIMIT 1",
                    (session_id,)
                )
                row = cursor.fetchone()
                return row['content'] if row else "(ไม่พบคำถามล่าสุด)"
        except Exception as e:
            print(f"❌ Could not retrieve last user query: {e}")
            return "(เกิดข้อผิดพลาดในการดึงคำถามล่าสุด)"
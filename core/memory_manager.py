# core/memory_manager.py
# (V2 - Stateful & Proactive Flow Support)

import sqlite3
import datetime
import time
from typing import List, Dict, Optional, Any

class MemoryManager:
    """
    จัดการประวัติการสนทนา (Long-term, DB-based) และ "สถานะ" ของการสนทนา
    ที่ต่อเนื่อง (Short-term, in-memory) เพื่อรองรับ Flow การทำงานแบบ Proactive Offer
    """
    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        self._init_db()
        
        # --------------------------------------------------------------------
        # 🧠 "ความจำระยะสั้นมาก" (In-Memory State Storage)
        # --------------------------------------------------------------------
        # ตัวแปรนี้จะถูกเก็บไว้ใน RAM เท่านั้น และจะถูกรีเซ็ตทุกครั้งที่เซิร์ฟเวอร์เริ่มใหม่
        # เหมาะสำหรับเก็บสถานะชั่วคราว เช่น "กำลังรอการยืนยันจากผู้ใช้"
        # ไม่จำเป็นต้องมีไฟล์สำหรับพักข้อมูล เพราะข้อมูลนี้ไม่มีค่าเมื่อโปรแกรมปิดตัวลง
        self.pending_tasks: Dict[str, Any] = {}
        # --------------------------------------------------------------------

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversation_history (
                        id INTEGER PRIMARY KEY, timestamp DATETIME NOT NULL, session_id TEXT NOT NULL,
                        role TEXT NOT NULL, content TEXT NOT NULL, agent_used TEXT
                    )
                ''')
                cursor.execute("PRAGMA table_info(conversation_history)")
                columns = [column[1] for column in cursor.fetchall()]
                if 'agent_used' not in columns:
                    cursor.execute("ALTER TABLE conversation_history ADD COLUMN agent_used TEXT")
                    print("🗄️  Upgraded DB: Added 'agent_used' column.")
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

    def get_last_n_memories(self, n: int = 15, session_id: str = "default_user") -> List[Dict]:
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
        """
        บันทึก "สถานะ" (ใน RAM) ว่าตอนนี้กำลังรอการยืนยันจากผู้ใช้สำหรับคำถามนี้
        """
        print(f"⏳ [Memory] Setting pending deep dive for user '{session_id}' on query: '{original_query}'")
        self.pending_tasks[session_id] = {
            "type": "DEEP_DIVE_CONFIRMATION",
            "original_query": original_query,
            "timestamp": time.time()
        }

    def check_and_clear_pending_deep_dive(self, session_id: str, user_confirmation: str) -> Optional[str]:
        """
        ตรวจสอบว่าผู้ใช้ตอบรับข้อเสนอหรือไม่ และล้างสถานะที่รออยู่
        """
        pending = self.pending_tasks.get(session_id)
        if not pending or pending.get("type") != "DEEP_DIVE_CONFIRMATION":
            return None

        if time.time() - pending.get("timestamp", 0) > 300:
            print(f"🗑️ [Memory] Pending task for user '{session_id}' expired.")
            del self.pending_tasks[session_id]
            return None

        confirmation_keywords = ["ใช่", "ครับ", "ค่ะ", "เอาเลย", "จัดมา", "เจาะลึก", "ตกลง", "แน่นอน", "ได้เลย", "ต้องการครับ"]
        if any(keyword in user_confirmation.lower() for keyword in confirmation_keywords):
            original_query = pending["original_query"]
            print(f"✅ [Memory] User '{session_id}' confirmed deep dive. Clearing pending task.")
            del self.pending_tasks[session_id]
            return original_query

        print(f"❌ [Memory] User '{session_id}' did not confirm. Clearing pending task.")
        del self.pending_tasks[session_id]
        return None

    def get_last_user_query(self, session_id: str = "default_user") -> str:
        """
        ดึง "คำถามล่าสุด" ของผู้ใช้จากฐานข้อมูล (DB) เพื่อใช้ใน FormatterAgent
        """
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
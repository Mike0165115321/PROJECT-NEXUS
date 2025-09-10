# agents/memory_mode/memory_agent.py
# (V3 - The LLM-Powered Archivist - Corrected)

from typing import Dict, Optional
from groq import Groq
import sqlite3
import datetime

class MemoryAgent:
    """
    Agent ผู้เชี่ยวชาญด้านการตอบคำถามเชิงข้อเท็จจริงเกี่ยวกับประวัติการสนทนา (V3)
    - ใช้ LLM ในการวิเคราะห์เจตนาภายใน (Internal Triage) เพื่อความยืดหยุ่นสูงสุด
    """
    def __init__(self, key_manager, model_name: str, memory_manager, persona_prompt: str):
        self.key_manager = key_manager
        self.model_name = model_name
        self.memory_manager = memory_manager
        self.persona_prompt = persona_prompt
        self.internal_triage_prompt = """
คุณคือ AI สมองส่วนหน้าของ "บรรณารักษ์ความทรงจำ" ภารกิจของคุณคือวิเคราะห์ "คำถามของผู้ใช้" และตัดสินใจว่าบรรณารักษ์ควรจะทำภารกิจ (TASK) ใดต่อไปนี้

**รายการภารกิจ (TASK) ที่สามารถเลือกได้:**
- `RECALL_FIRST_MEMORY`: เมื่อผู้ใช้ถามเกี่ยวกับ "ข้อความแรกสุด", "จุดเริ่มต้น", "คำถามแรก" ของการสนทนา
- `CALCULATE_STATS`: เมื่อผู้ใช้ถามเกี่ยวกับ "สถิติ", "จำนวนข้อความ", "คุยกันไปนานแค่ไหนแล้ว"
- `SUMMARIZE_RECENT`: เมื่อผู้ใช้ถามเกี่ยวกับสิ่งที่ "เพิ่งคุยกันไป", "เมื่อกี้", "เมื่อวาน", "ล่าสุด", หรือขอ "บทสรุป" การสนทนา
- `NO_MATCH`: ถ้าคำถามไม่ตรงกับภารกิจใดๆ ข้างต้นเลย

**คำสั่ง:**
อ่าน "คำถามของผู้ใช้" แล้วตอบกลับเป็นชื่อ TASK ที่เหมาะสมที่สุดเพียงหนึ่งเดียวเท่านั้น ห้ามมีข้อความอื่นปน

**ตัวอย่าง:**
- คำถาม: "เราเริ่มคุยกันเรื่องอะไรเป็นเรื่องแรก" -> ผลลัพธ์: RECALL_FIRST_MEMORY
- คำถาม: "สรุปเรื่องที่เราคุยกันเมื่อกี้ให้หน่อย" -> ผลลัพธ์: SUMMARIZE_RECENT
- คำถาม: "เธอจำได้ไหมว่าฉันชอบหนังสือแนวไหน" -> ผลลัพธ์: NO_MATCH

**คำถามของผู้ใช้:** "{query}"
**ผลลัพธ์:**
"""
        self.base_prompt_template = self.persona_prompt + """
**ภารกิจ: บรรณารักษ์ผู้รอบรู้**

**คำสั่ง:**
คุณคือ "ฟางซิน" ในบทบาทบรรณารักษ์ผู้เชี่ยวชาญด้านความทรงจำ ให้อ่าน "ข้อมูลข้อเท็จจริง" ที่ได้รับมา และเรียบเรียงเป็นคำตอบที่สุภาพ เป็นธรรมชาติ และตรงกับคำถามของผู้ใช้

**ข้อมูลข้อเท็จจริง:**
{data_context}

**คำถามของผู้ใช้:** "{query}"
**คำตอบของฟางซิน (ในบทบาทบรรณารักษ์):**
"""
        
        self.task_handlers = {
            "RECALL_FIRST_MEMORY": self._answer_first_memory_question,
            "CALCULATE_STATS": self._answer_stats_question,
            "SUMMARIZE_RECENT": self._answer_recent_summary_question
        }
        
        print("🧠 Memory Agent (V3 - The LLM-Powered Archivist) is online.")

    def _generate_response(self, data_context: str, query: str) -> str:
        api_key = self.key_manager.get_key()
        if not api_key:
            return "ขออภัยค่ะ ตอนนี้ฉันไม่สามารถเข้าถึงความทรงจำได้"

        try:
            client = Groq(api_key=api_key)
            prompt = self.base_prompt_template.format(data_context=data_context, query=query)
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ MemoryAgent LLM Error: {e}")
            if api_key: self.key_manager.report_failure(api_key)
            return "ขออภัยค่ะ เกิดข้อผิดพลาดขณะค้นหาความทรงจำ"

    def _answer_first_memory_question(self, query: str) -> str:
        """ตอบคำถามเกี่ยวกับข้อความแรกสุด"""
        print("  - 🧠 [Memory Agent] Task: Recalling first memory...")
        first_memory = self.memory_manager.find_absolute_first_user_memory()
        
        if not first_memory:
            context = "ไม่พบข้อมูลการสนทนาแรกสุดค่ะ"
        else:
            try:
                dt_object = datetime.datetime.fromisoformat(first_memory['timestamp'])
                formatted_date = dt_object.strftime("%d %B %Y")
            except:
                formatted_date = first_memory['timestamp'].split(" ")[0]
            
            context = f"จากบันทึกของเรา คำถามแรกสุดที่คุณถามคือ '{first_memory['content']}' ค่ะ ซึ่งเกิดขึ้นเมื่อวันที่ {formatted_date}"
            
        return self._generate_response(context, query)
    
    def find_absolute_first_user_memory(self, session_id: str = "default_user") -> Optional[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
            
                cursor.execute(
                "SELECT content, timestamp FROM archived_conversations WHERE session_id = ? AND role = 'user' ORDER BY id ASC LIMIT 1",
                (session_id,)
                )
                row = cursor.fetchone()
                if row: return dict(row)

                cursor.execute(
                "SELECT content, timestamp FROM conversation_history WHERE session_id = ? AND role = 'user' ORDER BY id ASC LIMIT 1",
                (session_id,)
            )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception:
            return self.get_first_user_memory(session_id)
        
    def _answer_stats_question(self, query: str) -> str:
        """ตอบคำถามเกี่ยวกับสถิติการสนทนา"""
        print("  - 🧠 [Memory Agent] Task: Calculating conversation stats...")
        stats = self.memory_manager.get_conversation_stats()
        
        if stats.get("error"):
            context = f"ไม่สามารถดึงข้อมูลสถิติได้เนื่องจาก: {stats['error']}"
        else:
            context = (
                "นี่คือข้อมูลภาพรวมการสนทนาของเราค่ะ:\n"
                f"- เราเริ่มคุยกันครั้งแรกเมื่อ: {stats.get('first_message_time', 'N/A')}\n"
                f"- มีข้อความทั้งหมดในประวัติ: {stats.get('total_messages', 0)} ข้อความ\n"
                f"- เป็นข้อความของคุณ: {stats.get('user_messages', 0)} ข้อความ\n"
                f"- เป็นข้อความของฉัน: {stats.get('model_messages', 0)} ข้อความ"
            )
        return self._generate_response(context, query)

    def _answer_recent_summary_question(self, query: str) -> str:
        """ตอบคำถามเกี่ยวกับบทสรุปของเรื่องที่คุยกันล่าสุด"""
        print("  - 🧠 [Memory Agent] Task: Summarizing recent topics...")
        summaries = self.memory_manager.get_last_session_summary(hours_ago=24)
        
        if not summaries:
            print("  - 🟡 No long-term summary found, checking short-term memory...")
            short_term_history = self.memory_manager.get_last_n_memories(n=10)
            if not short_term_history:
                context = "ยังไม่มีข้อมูลการสนทนาล่าสุดค่ะ"
            else:
                context = "เรายังไม่มีบทสรุปอย่างเป็นทางการ แต่เรื่องล่าสุดที่เราคุยกันคือ:\n"
                conversation_flow = "\n".join([f"- {mem['role']}: {mem['content'][:80]}..." for mem in short_term_history])
                context += conversation_flow
        else:
            context = "นี่คือหัวข้อที่เราคุยกันล่าสุดในช่วง 24 ชั่วโมงที่ผ่านมาค่ะ:\n"
            context += "\n".join([f"- {s['title']}" for s in summaries])
        
        return self._generate_response(context, query)
    
    def handle(self, query: str) -> Optional[str]:
        """
        เมธอดหลักที่ถูกยกเครื่องใหม่ทั้งหมด
        1. ใช้ LLM เพื่อวิเคราะห์เจตนาภายใน (Internal Triage)
        2. เรียกใช้ Handler ที่ถูกต้องตามผลลัพธ์
        """
        print(f"  - 🧠 [Memory Agent] Performing internal triage on: '{query[:30]}...'")
        
        api_key = self.key_manager.get_key()
        if not api_key: return "ขออภัยค่ะ ฉันไม่สามารถวิเคราะห์คำถามเกี่ยวกับความทรงจำได้ในตอนนี้"

        try:
            client = Groq(api_key=api_key)
            triage_prompt = self.internal_triage_prompt.format(query=query)
            
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": triage_prompt}],
                model=self.model_name,
                temperature=0.0
            )
            
            task_name = completion.choices[0].message.content.strip()
            print(f"  - ✅ Internal Triage decided task: {task_name}")

            handler_function = self.task_handlers.get(task_name)
            
            if handler_function:
                return handler_function(query)
            else:
                print(f"  - 🟡 [Memory Agent] Query does not match any known memory task (Task: {task_name}).")
                return None

        except Exception as e:
            print(f"❌ MemoryAgent Internal Triage Error: {e}")
            if api_key: self.key_manager.report_failure(api_key)
            return "ขออภัยค่ะ เกิดข้อผิดพลาดในการทำความเข้าใจคำถามเกี่ยวกับความทรงจำ"
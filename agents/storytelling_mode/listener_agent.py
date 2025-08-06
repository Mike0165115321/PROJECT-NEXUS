# agents/storytelling_mode/listener_agent.py
# (V1 - The Active Listener)

from typing import Dict, List, Any
from groq import Groq
import random

class ListenerAgent:
    """
    Agent ที่ทำหน้าที่เป็น "ผู้รับฟังที่กระตือรือร้น" (Active Listener)
    เมื่อผู้ใช้กำลังเล่าเรื่องราวต่อเนื่อง (USER_STORYTELLING)
    """
    def __init__(self, key_manager, model_name: str, persona_prompt: str):
        """
        เริ่มต้นการทำงานของ ListenerAgent
        - key_manager: ผู้จัดการคลังกุญแจ (สำหรับ Groq)
        - model_name: ชื่อโมเดลที่จะใช้ (จาก config.py, แนะนำ 8B)
        - persona_prompt: "บัตรประจำตัว" ของเฟิง
        """
        self.key_manager = key_manager
        self.model_name = model_name
        
        # --- พิมพ์เขียวทางความคิดสำหรับ "การเป็นผู้ฟังที่ดี" ---
        self.listening_prompt_template = persona_prompt + """
**ภารกิจ: ผู้รับฟังที่กระตือรือร้น (The Active Listener)**

คุณคือ "เฟิง" ในบทบาทผู้รับฟังที่ยอดเยี่ยม ภารกิจของคุณคือการแสดงให้ผู้ใช้เห็นว่าคุณกำลังตั้งใจฟังเรื่องราวของเขา, จดจำรายละเอียด, และกระตุ้นให้เขาเล่าต่ออย่างเป็นธรรมชาติ

**ข้อมูลประกอบ:**
- **ประวัติการสนทนาล่าสุด (เรื่องราวที่ผู้ใช้เล่ามา):**
{history_context}
- **ประโยคล่าสุดของผู้ใช้:**
{query}

**ศิลปะแห่งการเป็นผู้ฟังที่ดี (The Art of Active Listening):**
1.  **ตอบรับสั้นๆ (Acknowledge):** ใช้คำพูดสั้นๆ เพื่อตอบรับและแสดงว่าคุณกำลังฟังอยู่ (เช่น "ครับ...", "อืม น่าสนใจครับ", "แล้วเกิดอะไรขึ้นต่อครับ?")
2.  **ถามคำถามสั้นๆ (Clarify):** หากมีจุดไหนที่ไม่ชัดเจน ให้ถามคำถามสั้นๆ เพื่อให้แน่ใจว่าคุณเข้าใจถูกต้อง
3.  **แสดงความใส่ใจ (Show Engagement):** หากเหมาะสม อาจจะแสดงความคิดเห็นสั้นๆ เกี่ยวกับเรื่องราวเพื่อแสดงความใส่ใจ

**กฎเหล็ก:**
- **พูดให้น้อย ฟังให้มาก:** คำตอบของคุณต้องสั้นและกระชับเสมอ
- **ห้ามขัดจังหวะหรือเปลี่ยนเรื่อง:** โฟกัสอยู่ที่เรื่องราวของผู้ใช้เท่านั้น
- **เป้าหมายคือการทำให้ผู้ใช้รู้สึกสบายใจที่จะเล่าเรื่องของเขาให้จบ**

**คำสั่ง:**
จงสร้าง "คำตอบรับ" ที่สั้นและเหมาะสมที่สุดตามศิลปะการเป็นผู้ฟังที่ดี

**คำตอบรับของเฟิง (ในฐานะผู้ฟัง):**
"""
        print("👂 Listener Agent (V1 - Active Listener) is on duty.")

    def handle(self, query: str, short_term_memory: List[Dict[str, Any]]) -> str:
        """
        เมธอดหลักที่ Dispatcher จะเรียกใช้
        """
        print(f"👂 [Listener Agent] Actively listening to: '{query[:40]}...'")
        
        history_context = "\n".join([f"- {mem.get('role')}: {mem.get('content')}" for mem in short_term_memory])
        if not history_context:
            history_context = "(ยังไม่มีประวัติการสนทนา)"

        api_key = self.key_manager.get_key()
        if not api_key:
            return random.choice(["ครับ", "อืม...", "ครับผม"])

        try:
            client = Groq(api_key=api_key)
            
            prompt = self.listening_prompt_template.format(
                history_context=history_context,
                query=query
            )
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                temperature=0.5 # เพิ่มความหลากหลายเล็กน้อย
            )
            return chat_completion.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ ListenerAgent LLM Error: {e}")
            # Fallback เป็นคำตอบรับแบบง่ายๆ
            return random.choice(["ครับ", "น่าสนใจครับ", "เล่าต่อได้เลยครับ"])
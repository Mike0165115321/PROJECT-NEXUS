# agents/coder_mode/code_agent.py
# (V2 - Upgraded for Centralized Config & Persona)

from groq import Groq
from typing import Dict, Any, List

class CoderAgent:
    """
    Agent ที่ทำหน้าที่เป็น "ที่ปรึกษาด้านโค้ด" (Code Consultant)
    ให้คำแนะนำ, เขียนโค้ดตัวอย่าง, หรืออธิบายแนวคิดการเขียนโปรแกรม
    """
    def __init__(self, key_manager, model_name: str, persona_prompt: str):
        self.key_manager = key_manager
        self.model_name = model_name
        
        self.system_prompt = persona_prompt + """
**ภารกิจ: ที่ปรึกษาด้านโค้ด (Code Consultant)**

คุณคือ "เฟิง" ในบทบาทที่ปรึกษาด้านการเขียนโปรแกรมที่ช่วยเหลือและมีประสิทธิภาพ ภารกิจของคุณคือการให้คำตอบที่ชัดเจน, กระชับ, และถูกต้องเกี่ยวกับโค้ด

**กฎการทำงาน:**
1.  **ให้คำตอบที่สมบูรณ์:** ตอบคำถามของผู้ใช้ให้ครบถ้วน
2.  **ใช้บล็อกโค้ด:** ใส่โค้ด Python ทั้งหมดไว้ในบล็อก ```python ... ``` เสมอ
3.  **อธิบายโค้ด:** หากมีการเขียนโค้ด ให้มีคำอธิบายสั้นๆ ประกอบเสมอว่าโค้ดนั้นทำอะไร
"""

    def handle(self, query: str, short_term_memory: List[Dict[str, Any]]) -> str:
        """
        รับคำสั่งเกี่ยวกับโค้ด แล้วส่งให้ LLM จัดการ
        """
        print(f"🤖 [Coder Agent] Handling code query: '{query[:40]}...'")
        
        memory_context = "\n".join([f"- {mem.get('role')}: {mem.get('content')}" for mem in short_term_memory])

        try:
            api_key = self.key_manager.get_key()
            client = Groq(api_key=api_key)
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"ประวัติการสนทนาล่าสุด:\n{memory_context}\n\nคำถามของฉันคือ: {query}"}
                ],
                model=self.model_name,
            )
            
            response_content = chat_completion.choices[0].message.content
            print("✅ Coder Agent completed successfully!")
            return response_content

        except Exception as e:
            print(f"❌ An error occurred in Coder Agent: {e}")
            raise e 
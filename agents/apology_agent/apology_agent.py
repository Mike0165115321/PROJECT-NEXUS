# agents/apology_agent/apology_agent.py
# (V1 - The Graceful Error Handler)

from typing import Dict, Any
from groq import Groq

class ApologyAgent:
    """
    Agent ที่ทำหน้าที่เป็น "ผู้จัดการสถานการณ์" (Situation Manager)
    สร้างคำขอโทษและเสนอทางแก้ไขเมื่อ Agent อื่นทำงานผิดพลาด
    """
    def __init__(self, key_manager, model_name: str, persona_prompt: str):
        """
        เริ่มต้นการทำงานของ ApologyAgent
        - key_manager: ผู้จัดการคลังกุญแจ (สำหรับ Groq)
        - model_name: ชื่อโมเดลที่จะใช้ (จาก config.py, แนะนำ 8B)
        - persona_prompt: "บัตรประจำตัว" ของเฟิง
        """
        self.key_manager = key_manager
        self.model_name = model_name
        self.apology_prompt_template = persona_prompt + """
**ภารกิจ: ผู้จัดการสถานการณ์และฟื้นฟูความสัมพันธ์ (Situation & Rapport Manager)**

คุณคือ "เฟิง" ในสถานการณ์ที่ละเอียดอ่อน ทีมงานผู้เชี่ยวชาญของคุณทำงานผิดพลาดและให้คำตอบที่ไม่ได้คุณภาพ ภารกิจของคุณคือการ "ขอโทษ" อย่างจริงใจ, "อธิบาย" สถานการณ์อย่างโปร่งใส (แต่ไม่ใช้ศัพท์เทคนิค), และ "เสนอทางแก้ไข" เพื่อฟื้นฟูความเชื่อมั่นของผู้ใช้

**ข้อมูลประกอบ:**
- **คำถามดั้งเดิมของผู้ใช้:** "{original_query}"
- **บริบทของข้อผิดพลาด (สำหรับคุณ):** "{error_context}"

**ขั้นตอนการทำงาน:**
1.  **กล่าวขอโทษอย่างจริงใจ:** แสดงความขอโทษสำหรับความผิดพลาดที่เกิดขึ้นอย่างตรงไปตรงมา
2.  **อธิบายสั้นๆ (ถ้าทำได้):** อธิบายสาเหตุของปัญหาในภาษาที่เข้าใจง่าย (เช่น "ดูเหมือนว่าการเชื่อมต่อกับคลังความรู้จะขัดข้องชั่วคราว" หรือ "ผมอาจจะยังไม่เข้าใจคำถามในส่วนนี้ดีพอ")
3.  **เสนอทางแก้ไขที่เป็นรูปธรรม:** เสนอทางเลือกให้ผู้ใช้ 1-2 ทางเลือกเพื่อเดินหน้าต่ออย่างชัดเจน

**ตัวอย่าง:**
- **Error Context:** "PlannerAgent returned an empty or non-JSON response."
- **คำตอบของเฟิง:** "ผมต้องขออภัยอย่างสูงครับ ดูเหมือนว่าการค้นคว้าข้อมูลในหัวข้อ '{original_query}' ของผมในครั้งนี้จะเกิดข้อผิดพลาดทางเทคนิค ทำให้ไม่สามารถสร้างบทวิเคราะห์ที่สมบูรณ์ได้... **คุณต้องการให้ผมลองพยายามค้นหาอีกครั้ง หรือคุณอยากจะลองปรับแก้คำถามเพื่อให้ผมเข้าใจได้ดียิ่งขึ้นครับ?**"

**Input ของคุณ:**
- **คำถามดั้งเดิมของผู้ใช้:** "{original_query}"
- **บริบทของข้อผิดพลาด (สำหรับคุณ):** "{error_context}"

**คำขอโทษและข้อเสนอแนะ (โดย เฟิง):**
"""
        print("🛡️ Apology Agent (V1 - Graceful Handler) is on standby.")

    def handle(self, original_query: str, error_context: str) -> str:
        """
        เมธอดหลักที่ Dispatcher จะเรียกใช้เมื่อเกิด Error
        """
        print(f"🛡️ [Apology Agent] Handling error for query: '{original_query}'")
        api_key = self.key_manager.get_key()
        if not api_key:
            return "ผมต้องขออภัยอย่างสูงครับ เกิดข้อผิดพลาดซ้ำซ้อนในระบบ"

        try:
            client = Groq(api_key=api_key)
            
            prompt = self.apology_prompt_template.format(
                original_query=original_query,
                error_context=error_context
            )
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ ApologyAgent's own LLM Error: {e}")
            # Fallback สุดท้ายจริงๆ
            return "ผมต้องขออภัยอย่างสูงครับ ดูเหมือนว่าระบบจะขัดข้องชั่วคราว โปรดลองใหม่อีกครั้งในภายหลัง"
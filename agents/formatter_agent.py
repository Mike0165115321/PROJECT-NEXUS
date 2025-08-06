# agents/formatter_agent.py
# (V2.1 - Upgraded based on original logic)

import google.generativeai as genai
from typing import Dict, Any

class FormatterAgent:
    """
    Agent ที่ทำหน้าที่เป็น "บรรณาธิการ" และ "นักจัดรูปแบบ" (Typesetter)
    รับผิดชอบการขัดเกลาคำตอบสุดท้ายเพื่อให้มีรูปแบบที่ชัดเจน สวยงาม และอ่านง่าย
    """
    # ⭐️ 1. รับ model_name เข้ามาตอนสร้างอินสแตนซ์ ⭐️
    def __init__(self, key_manager, model_name: str, persona_prompt: str):
        """
        เริ่มต้นการทำงานโดยรับทรัพยากรที่จำเป็นทั้งหมดเข้ามา
        """
        self.key_manager = key_manager
        self.model_name = model_name
        
        # ⭐️ 2. ประกอบร่าง Prompt ใหม่ โดยยังคงกฎเหล็กเดิมของคุณไว้ ⭐️
        self.formatting_prompt_template = persona_prompt + """
**ภารกิจ: บรรณาธิการและนักจัดรูปแบบ (Editor & Typesetter)**

คุณคือ "เฟิง" ในขั้นตอนสุดท้าย ภารกิจของคุณคือการนำ "บทวิเคราะห์ฉบับร่าง" ที่ทีมงานสร้างขึ้น มาจัดรูปแบบด้วย Markdown เพื่อให้อ่านง่ายและสวยงามที่สุด โดยอ้างอิงจาก "คำถามดั้งเดิมของผู้ใช้" เพื่อให้แน่ใจว่าคำตอบสุดท้ายยังคงตอบโจทย์

**ข้อมูลประกอบ:**
- **คำถามดั้งเดิมของผู้ใช้:** {original_query}
- **บทวิเคราะห์ฉบับร่าง (ห้ามตัดทอน):**
---
{draft_to_review}
---

**กฎเหล็กข้อ 1 (สำคัญที่สุด):**
**ห้ามสรุปหรือตัดทอนเนื้อหาโดยเด็ดขาด (DO NOT SUMMARIZE OR SHORTEN THE CONTENT)** คุณต้องรักษารายละเอียดและใจความทั้งหมดของต้นฉบับไว้ 100%

**กฎการจัดรูปแบบ:**
1.  **จัดโครงสร้าง:** ใช้ Markdown เช่น **หัวข้อหลัก** และ * รายการย่อย เพื่อแบ่งประเด็นให้ชัดเจน
2.  **ปรับย่อหน้า:** ตัดแบ่งย่อหน้ายาวๆ ให้สั้นลงเพื่อความสบายตาในการอ่าน
3.  **คงบุคลิก:** ตรวจสอบให้แน่ใจว่าภาษายังคงความสุขุมและเป็นเหตุผลตามบุคลิกของ "เฟิง"
4.  **ทำให้ดูเป็นธรรมชาติ:** ทำให้ดูเหมือนผู้ช่วยจัดรูปแบบจริงๆ ไม่ใช่แค่ AI
5.  **ไม่ต้องอธิบาย:** ห้ามใส่คำอธิบายหรือข้อความอื่นๆ นอกเหนือจาก Markdown ที่จัดรูปแบบแล้ว

**ฉบับสมบูรณ์ที่จัดรูปแบบแล้ว (โดย เฟิง):**
"""

    # ⭐️ 3. ปรับ handle ให้รับ Dictionary และมี Error Handling ที่ดีขึ้น ⭐️
    def handle(self, synthesis_order: Dict[str, Any]) -> str:
        """
        รับ "แฟ้มงานบรรณาธิการ" (synthesis_order) จาก Dispatcher มาประมวลผล
        """
        raw_draft = synthesis_order.get("draft_to_review", "")
        if not raw_draft or not isinstance(raw_draft, str):
            return "" # คืนค่าว่างถ้าไม่มีร่างคำตอบ

        original_query = synthesis_order.get("original_query", "(ไม่ระบุ)")

        print("✍️ [Formatter Agent] Requesting a key for final typesetting...")
        api_key = self.key_manager.get_key()
        if not api_key:
            print("⚠️ FormatterAgent: No API keys available. Returning raw draft.")
            return raw_draft

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.model_name)
            
            prompt = self.formatting_prompt_template.format(
                original_query=original_query,
                draft_to_review=raw_draft
            )
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str: # ดักจับ Rate Limit Error ได้กว้างขึ้น
                print(f"🟡 Formatter Agent: Key '...{api_key[-4:]}' hit rate limit.")
                self.key_manager.report_failure(api_key)
                print("   -> Retrying with the next available key...")
                return self.handle(synthesis_order) # Retry โดยส่ง synthesis_order เดิมไป
            else:
                print(f"❌ An unexpected error occurred in Formatter Agent: {e}")
                return raw_draft # Fallback to raw text
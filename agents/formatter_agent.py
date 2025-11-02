# agents/formatter_agent.py

import google.generativeai as genai
from typing import Dict, Any
import asyncio  

class FormatterAgent:
    def __init__(self, key_manager, model_name: str, persona_prompt: str):
        """
        เริ่มต้นการทำงานโดยรับทรัพยากรที่จำเป็นทั้งหมดเข้ามา
        """
        self.key_manager = key_manager
        self.model_name = model_name
        
        self.model = genai.GenerativeModel(self.model_name)
        self.formatting_prompt_template = """
**ภารกิจ: เครื่องพิมพ์ดีด Markdown (Markdown Typesetter)**

คุณคือระบบจัดรูปแบบอัตโนมัติ ภารกิจของคุณมี "เพียงข้อเดียว" คือการนำ "ข้อความดิบ" ที่ป้อนเข้ามา แล้ว "หุ้ม" มันด้วย Markdown (เช่น `**`, `#`, `* `) เพื่อทำให้อ่านง่ายขึ้น

**กฎเหล็ก (สำคัญที่สุด):**
1.  **ห้ามเปลี่ยนแปลง:** ห้าม "เปลี่ยน", "เพิ่ม", "ลบ", "เขียนใหม่" หรือ "สรุป" คำใดๆ ใน "ข้อความดิบ" แม้แต่คำเดียว
2.  **อนุญาตให้ทำ:** ทำได้แค่ "เพิ่ม" สัญลักษณ์ Markdown (`#`, `##`, `*`, `**`, `\n`) เข้าไปเท่านั้น
3.  **คงภาษาเดิม:** ถ้าข้อความดิบเป็นภาษาไทย ผลลัพธ์ต้องเป็นภาษาไทย (ยกเว้นชื่อเฉพาะ)
4.  **ไม่ต้องอธิบาย:** ห้ามพูดอะไรทั้งสิ้น ส่งผลลัพธ์ที่จัดรูปแบบแล้วกลับมาทันที

**ข้อความดิบ:**
---
{draft_to_review}
---

**ผลลัพธ์ที่จัดรูปแบบแล้ว:**
"""

    async def _call_llm_async(self, prompt: str) -> str:
        api_key = await self.key_manager.get_key()
        if not api_key: raise Exception("No available API keys.")
        try:
            genai.configure(api_key=api_key)
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
        
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "resource_exhausted" in error_str:
                print(f"🟡 Formatter Agent: Key '...{api_key[-4:]}' hit rate limit.")
                self.key_manager.report_failure(api_key)
                print(" 	 -> Retrying with the next available key...")
                await asyncio.sleep(1) 
                return await self._call_llm_async(prompt) 
            raise e

    async def handle(self, synthesis_order: Dict[str, Any]) -> str:
        raw_draft = synthesis_order.get("draft_to_review", "")
        if not raw_draft or not isinstance(raw_draft, str):
            return ""


        print("✍️ [Formatter Agent V10] Requesting typesetting (Async)...")
        
        try:
            prompt = self.formatting_prompt_template.format(
                draft_to_review=raw_draft
            )
            
            formatted_text = await self._call_llm_async(prompt)
            return formatted_text
            
        except Exception as e:
            print(f"❌ An unexpected error occurred in Formatter Agent: {e}")
            return raw_draft
# agents/news_mode/news_agent.py
# (V4.3 - Final Story-driven Version)

from groq import Groq
from typing import Dict, Any

class NewsAgent:
    def __init__(self, key_manager, model_name: str, news_cache_manager, persona_prompt: str):
        """
        เริ่มต้นการทำงานของ NewsAgent
        """
        self.key_manager = key_manager
        self.news_cache_manager = news_cache_manager
        self.model_name = model_name
        
        self.summary_prompt_template = persona_prompt + """
**ภารกิจ: บรรณาธิการข่าวกรอง (Intelligence Editor)**

คุณคือ "เฟิง" ในบทบาทบรรณาธิการข่าวผู้เชี่ยวชาญ ภารกิจของคุณคือการวิเคราะห์ "ข้อมูลข่าวสารดิบ" ที่ทีมงานรวบรวมมา แล้วสังเคราะห์ให้กลายเป็น "บทสรุปสถานการณ์" ที่กระชับ, เข้าใจง่าย, และเป็นกลาง

**ข้อมูลข่าวสารดิบเพื่อการวิเคราะห์:**
---
{context_from_db}
---

**กฎการสร้างบทสรุป:**
1.  **สร้างหัวข้อข่าวหลัก:** สร้างหัวข้อข่าวที่น่าสนใจและครอบคลุมประเด็นทั้งหมด
2.  **เรียบเรียงเป็นบทความ:** เขียนสรุปในรูปแบบย่อหน้าที่ลื่นไหล ไม่ใช้รายการ (bullet points)
3.  **จัดกลุ่มเนื้อหา:** เริ่มต้นด้วยภาพรวม แล้วจึงจัดกลุ่มหัวข้อที่คล้ายกันไว้ในย่อหน้าเดียวกัน
4.  **เป็นกลางและตรงไปตรงมา:** นำเสนอข้อมูลตามข้อเท็จจริงที่ได้รับมา

**คำสั่ง:**
จงสร้าง "บทสรุปสถานการณ์" ที่ดีที่สุดตามภารกิจและกฎข้างต้น

**บทสรุปสถานการณ์ (โดย บรรณาธิการเฟิง):**
"""
        # ⭐️⭐️⭐️ เพิ่ม print() statement ที่นี่ ⭐️⭐️⭐️
        print("📰 บรรณาธิการข่าวกรอง (NewsAgent) ประจำสถานี")

    def handle(self, query: str) -> Dict[str, Any]:
        print(f"📰 [News Agent] Handling news query: '{query}'")
        
        thought_process = { "agent_name": "NewsAgent", "query": query, "steps": [] }

        try:
            thought_process["steps"].append(f"Searching for news related to '{query}' in cache.")
            context_from_db = self.news_cache_manager.search(query, k=7)
            thought_process["retrieved_context"] = context_from_db
            
            if not context_from_db or "ไม่พบ" in context_from_db:
                thought_process["steps"].append("No relevant news found in the cache.")
                return {
                    "answer": "ขออภัยครับ ผมไม่พบข้อมูลข่าวสารที่เกี่ยวข้องในขณะนี้",
                    "thought_process": thought_process
                }

            thought_process["steps"].append(f"Found news context. Summarizing with model: {self.model_name}...")
            
            api_key = self.key_manager.get_key()
            
            client = Groq(api_key=api_key)
            
            prompt = self.summary_prompt_template.format(context_from_db=context_from_db)
            
            chat_completion = client.chat.com_pletions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
            )
            final_answer = chat_completion.choices[0].message.content.strip()

            thought_process["steps"].append("Successfully generated news briefing.")
            return { "answer": final_answer, "thought_process": thought_process }
            
        except Exception as e:
            print(f"❌ NewsAgent Error: {e}")
            traceback.print_exc()
            
            error_message = str(e)
            thought_process["error"] = error_message
            answer = "ขออภัยครับ เกิดข้อผิดพลาดระหว่างการสรุปข่าว"

            if "AllGroqKeysOnCooldownError" in e.__class__.__name__:
                 answer = "ขออภัยครับ โควต้า API สำหรับสรุปข่าวเต็มชั่วคราว กรุณาลองใหม่อีกครั้งในภายหลัง"
            
            return {"answer": answer, "thought_process": thought_process}
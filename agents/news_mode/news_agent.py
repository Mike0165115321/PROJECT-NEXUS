# agents/news_mode/news_agent.py
# (V5.1 - Corrected Prompt)

from groq import Groq
import traceback
from typing import Dict, Any

class NewsAgent:
    def __init__(self, key_manager, model_name: str, rag_engine, persona_prompt: str):
        self.key_manager = key_manager
        self.rag_engine = rag_engine
        self.model_name = model_name
        
        self.summary_prompt_template = persona_prompt + """
**ภารกิจ: บรรณาธิการข่าวกรอง (Intelligence Editor)**

คุณคือ "เฟิง" ในบทบาทบรรณาธิการข่าวผู้เชี่ยวชาญ ภารกิจของคุณคือการวิเคราะห์ "ข้อมูลข่าวสารดิบจากหลายแหล่งข่าว" ที่ทีมงานรวบรวมมา แล้วสังเคราะห์ให้กลายเป็น "บทสรุปสถานการณ์" ที่กระชับ, เข้าใจง่าย, และเป็นกลาง

**ข้อมูลข่าวสารดิบจากหลายแหล่งข่าว:**
---
{context_from_rag}
---

**กฎการสร้างบทสรุป:**
1.  **สังเคราะห์ ไม่ใช่แค่สรุป:** อ่านข้อมูลจากทุกแหล่งข่าว แล้วจับประเด็นหลักที่เหมือนหรือต่างกัน
2.  **สร้างหัวข้อข่าวหลัก:** สร้างหัวข้อข่าวที่น่าสนใจและครอบคลุมประเด็นทั้งหมด
3.  **เรียบเรียงเป็นบทความ:** เขียนสรุปในรูปแบบย่อหน้าที่ลื่นไหล ไม่ใช้รายการ (bullet points)
4.  **เป็นกลางและตรงไปตรงมา:** นำเสนอข้อมูลตามข้อเท็จจริงที่ได้รับมา
5.  **สำคัญ** ถ้ามีวันที่ หรือเวลาในข้อมูลข่าวสาร ให้ระบุวันที่ล่าสุดที่เกิดเหตุการณ์ในบทสรุป

**คำสั่ง:**
จงสร้าง "บทสรุปสถานการณ์" ที่ดีที่สุดตามภารกิจและกฎข้างต้น

**บทสรุปสถานการณ์ (โดย บรรณาธิการเฟิง):**
"""
        print("📰 บรรณาธิการข่าวกรอง (NewsAgent V5.1 - Corrected) ประจำสถานี")

    def handle(self, query: str) -> Dict[str, Any]:
        print(f"📰 [News Agent] Handling news query: '{query}'")
        
        thought_process = { "agent_name": "NewsAgent", "query": query, "steps": [] }

        try:
            thought_process["steps"].append(f"Searching News RAG Index for: '{query}'")
            context_from_rag = self.rag_engine.search_news(query, top_k=7)
            thought_process["retrieved_context"] = context_from_rag
            
            if not context_from_rag or "ไม่พบ" in context_from_rag:
                thought_process["steps"].append("No relevant news found in the RAG index.")
                return {
                    "answer": "ขออภัยครับ ผมไม่พบข้อมูลข่าวสารที่เกี่ยวข้องในขณะนี้",
                    "thought_process": thought_process
                }

            thought_process["steps"].append(f"Found news context. Summarizing with model: {self.model_name}...")
            
            api_key = self.key_manager.get_key()
            if not api_key:
                raise Exception("No available API keys for NewsAgent.")

            client = Groq(api_key=api_key)
            
            prompt = self.summary_prompt_template.format(context_from_rag=context_from_rag)
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
            )
            final_answer = chat_completion.choices[0].message.content.strip()

            thought_process["steps"].append("Successfully generated news briefing from RAG context.")
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
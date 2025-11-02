# agents/consultant_mode/librarian_agent.py
# (V43.0 - Async & CORRECTED Groq Fix)

from typing import Optional, List, Dict, Any 
from groq import AsyncGroq 
import asyncio

class LibrarianAgent:
    """
    [V43] Agent ที่ทำหน้าที่เป็น "บรรณารักษ์ผู้แนะนำ" (แบบ Async ที่ถูกต้อง)
    """
    def __init__(self, key_manager, model_name: str, rag_engine, persona_prompt: str):
        self.key_manager = key_manager 
        self.model_name = model_name
        self.rag_engine = rag_engine
        
        
        self.recommendation_prompt_template = persona_prompt + """
**ภารกิจ: บรรณารักษ์ผู้แนะนำ (Recommender Librarian)**

คุณคือ "ฟางซิน" ในบทบาทบรรณารักษ์ผู้รอบรู้ ภารกิจของคุณคือการวิเคราะห์ "หัวข้อที่ผู้ใช้สนใจ" แล้วแนะนำหนังสือที่เกี่ยวข้องที่สุดจาก "รายชื่อหนังสือทั้งหมด" ที่มีในคลังความรู้

**ข้อมูลประกอบ:**
- **หัวข้อที่ผู้ใช้สนใจ:** "{query}"
- **รายชื่อหนังสือทั้งหมดในคลัง:**
---
{book_titles}
---

**ขั้นตอนการทำงาน:**
1.  **วิเคราะห์หัวข้อ:** ทำความเข้าใจว่าผู้ใช้กำลังสนใจเรื่องอะไร
2.  **คัดเลือกหนังสือ:** เลือกหนังสือจาก "รายชื่อทั้งหมด" ที่คุณคิดว่าเกี่ยวข้องกับหัวข้อนั้นมากที่สุด 3-5 เล่ม
3.  **สร้างคำแนะนำ:** เขียนคำแนะนำสั้นๆ สำหรับหนังสือแต่ละเล่ม โดยอธิบายว่า "หนังสือเล่มนี้จะช่วยให้เข้าใจหัวข้อนั้นๆ ได้อย่างไร"
4.  **เชื้อเชิญให้ถามต่อ:** จบด้วยการเชื้อเชิญให้ผู้ใช้ถามคำถามเชิงลึกต่อได้ ซึ่งจะเป็นการส่งต่องานให้ PlannerAgent

**กฎเหล็ก:**
- ห้ามกุรายชื่อหนังสือที่ไม่มีอยู่จริงขึ้นมา
- คำแนะนำต้องกระชับและน่าสนใจ

**คำตอบ (โดย บรรณารักษ์เฟิง):**
"""
        print("📚 Librarian Agent (V43 - Async Recommender) is on duty.") 

    async def _call_llm_async(self, prompt: str) -> str:
        
        api_key = await self.key_manager.get_key()
        if not api_key: raise Exception("No available Groq API keys.")
        
        try:
            client = AsyncGroq(api_key=api_key)

            chat_completion = await client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
            )
            return chat_completion.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"❌ LibrarianAgent LLM Error: {e}")
            if api_key: self.key_manager.report_failure(api_key) 
            
            error_str = str(e).lower()
            if api_key and ("429" in error_str or "service_unavailable" in error_str):
                print(" 	 -> Retrying _call_llm_async...")
                await asyncio.sleep(1)
                return await self._call_llm_async(prompt) 
            
            raise e 
        
    async def handle(self, query: str) -> str | None:
        q_lower = query.lower().strip()

        if "มีหนังสืออะไรบ้าง" in q_lower or "รายชื่อหนังสือ" in q_lower:
            print("📚 Librarian Agent (Async V43): Handling 'list all books' request.")
            all_titles = await self.rag_engine.get_all_book_titles() 
            
            if not all_titles:
                return "ขออภัยครับ ตอนนี้ยังไม่มีข้อมูลหนังสือในระบบครับ"
            
            header = f"ตอนนี้ผมมีข้อมูลหนังสือทั้งหมด {len(all_titles)} เล่มครับ:\n"
            body = "- " + "\n- ".join(sorted(all_titles))
            return header + body

        if "มีหมวดหมู่อะไรบ้าง" in q_lower or "มีประเภทอะไรบ้าง" in q_lower or "ชั้นหนังสือ" in q_lower:
            print("📚 Librarian Agent (Async V43): Handling 'list categories' request.")
            all_categories = self.rag_engine.available_categories
            if not all_categories:
                return "ขออภัยครับ ตอนนี้ยังไม่มีการจัดหมวดหมู่หนังสือในระบบครับ"
            
            header = f"คลังความรู้ของผมแบ่งออกเป็น {len(all_categories)} หมวดหมู่หลักครับ:\n"
            formatted_categories = ["- " + cat.replace("_", " ") for cat in sorted(all_categories)]
            body = "\n".join(formatted_categories)
            return header + body

        recommend_keywords = ["แนะนำหนังสือ", "ควรอ่านเล่มไหน", "เกี่ยวกับเรื่อง", "หนังสือเกี่ยวกับ"]
        if any(keyword in q_lower for keyword in recommend_keywords):
            print(f"📚 Librarian Agent (Async V43): Handling recommendation request for '{query}'")
            
            all_titles = await self.rag_engine.get_all_book_titles() # (V32 OK)
            if not all_titles:
                return "ขออภัยครับ ตอนนี้ยังไม่มีข้อมูลหนังสือในระบบให้แนะนำครับ"

            try:
                prompt = self.recommendation_prompt_template.format(
                    query=query,
                    book_titles="\n- ".join(all_titles)
                )
                
                return await self._call_llm_async(prompt)

            except Exception as e:
                print(f"❌ LibrarianAgent final attempt failed: {e}")
                return "ขออภัยครับ เกิดข้อผิดพลาดระหว่างการค้นหาหนังสือแนะนำ"

        return None
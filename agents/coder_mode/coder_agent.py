# agents/coder_mode/code_agent.py

from groq import AsyncGroq  
from typing import Dict, Any, List
import asyncio  

class CoderAgent:
    """
    [V44] Agent ที่ทำหน้าที่เป็น "ที่ปรึกษาด้านโค้ด" (แบบ Async ที่ถูกต้อง)
    """
    def __init__(self, key_manager, model_name: str, persona_prompt: str):
        self.key_manager = key_manager
        self.model_name = model_name
        
        
        self.system_prompt = persona_prompt + """
**ภารกิจ: ที่ปรึกษาด้านโค้ด (Code Consultant)**
ในบทบาทที่ปรึกษาด้านการเขียนโปรแกรมที่ช่วยเหลือและมีประสิทธิภาพ ภารกิจของคุณคือการให้คำตอบที่ชัดเจน, กระชับ, และถูกต้องเกี่ยวกับโค้ด
**กฎการทำงาน:**
1.  **ให้คำตอบที่สมบูรณ์:** ตอบคำถามของผู้ใช้ให้ครบถ้วน
2.  **ใช้บล็อกโค้ด:** ใส่โค้ด Python ทั้งหมดไว้ในบล็อก ```python ... ``` เสมอ
3.  **อธิบายโค้ด:** หากมีการเขียนโค้ด ให้มีคำอธิบายสั้นๆ ประกอบเสมอว่าโค้ดนั้นทำอะไร
"""
        print("🤖 Coder Agent (V44 - Async & Fixed) is ready.") 

    async def _call_llm_async(self, system_prompt: str, user_prompt: str) -> str:
        
        api_key = await self.key_manager.get_key() 
        if not api_key: raise Exception("No available Groq API keys.")
        
        try:
            client = AsyncGroq(api_key=api_key)
            
            chat_completion = await client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model_name,
            )
            return chat_completion.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"❌ CoderAgent LLM Error: {e}")
            if api_key: self.key_manager.report_failure(api_key) 
            
            if api_key and ("429" in str(e).lower() or "service_unavailable" in str(e).lower()):
                print(" 	 -> Retrying _call_llm_async...")
                await asyncio.sleep(1)
                return await self._call_llm_async(system_prompt, user_prompt)
            
            raise e 
    
    async def handle(self, query: str, short_term_memory: List[Dict[str, Any]]) -> str:
        print(f"🤖 [Coder Agent V44] Handling code query: '{query[:40]}...' (Async)") 
        
        memory_context = "\n".join([f"- {mem.get('role')}: {mem.get('content')}" for mem in short_term_memory])
        user_prompt = f"ประวัติการสนทนาล่าสุด:\n{memory_context}\n\nคำถามของฉันคือ: {query}"

        try:
            response_content = await self._call_llm_async(self.system_prompt, user_prompt)
            
            print("✅ Coder Agent completed successfully!")
            return response_content

        except Exception as e:
            print(f"❌ An error occurred in Coder Agent: {e}")
            return f"ขออภัยครับ เกิดข้อผิดพลาดในการประมวลผลโค้ด: {e}"
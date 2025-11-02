# agents/feng_mode/general_conversation_agent.py
import json
from typing import Dict, List, Any
from groq import AsyncGroq  
import asyncio

class GeneralConversationAgent:
    
    def __init__(self, key_manager, model_name: str, rag_engine, ltm_manager, persona_prompt: str):
        self.key_manager = key_manager
        self.model_name = model_name
        self.rag_engine = rag_engine
        self.ltm_manager = ltm_manager
        
        self.general_conversation_prompt = persona_prompt + """
**ภารกิจ: สหายทางปัญญาผู้มีความทรงจำ**

**ข้อมูลประกอบ:**
- **ความทรงจำระยะยาวที่เกี่ยวข้อง (ถ้ามี):**
{long_term_memory_context}
- **บริบทการสนทนาล่าสุด:**
{history_context}
- **ข้อมูลเสริมจากสัญชาตญาณ (KG-RAG):**
{intuitive_context}

**ศิลปะแห่งการสนทนา:**
1.  **ไตร่ตรองจากความทรงจำ:** อ่าน "ความทรงจำระยะยาว" ก่อนเสมอ เพื่อทำความเข้าใจว่าเราเคยคุยเรื่องอะไรกันไปแล้วบ้างในอดีต
2.  **ตอบสนองอย่างชาญฉลาด:** สร้างคำตอบที่เชื่อมโยงกับทั้งความทรงจำในอดีตและบริบทปัจจุบัน

**คำถามล่าสุดของผู้ใช้:** "{query}"
**คำตอบของฟางซิน (ที่อิงจากความทรงจำทั้งหมด):**
"""
        print("🤝 General Conversation Agent (V6 - KGRAG Powered) is ready.")
    
    async def _get_intuitive_context(self, query: str) -> str:
        print(f" 	- 🕸️  Searching KG-RAG (Async) for intuition about: '{query}'")
        if not self.rag_engine:
            return "ไม่มี"
        
        results = await self.rag_engine.search_graph(query, top_k=2)
        
        if not results:
            return "ไม่มี"
            
        contexts = [f"- '{item.get('name')}': {item.get('description', '')[:70]}..." for item in results]
        return "\n".join(contexts)

    async def handle(self, query: str, short_term_memory: List[Dict[str, Any]]) -> str:
        print(f"💬 [General Conversation Agent V12] Handling: '{query[:40]}...' (Async)")
        ltm_context = "ไม่มีความทรงจำระยะยาวที่เกี่ยวข้อง"
        if self.ltm_manager:
            try:
                relevant_memories = await asyncio.to_thread(
                    self.ltm_manager.search_relevant_memories, query, k=2
                )
                if relevant_memories:
                    ltm_context = "นี่คือบทสรุปจากการสนทนาของเราในอดีตที่อาจจะเกี่ยวข้อง:\n"
                    ltm_context += "\n\n".join([
                        f"- ในหัวข้อ '{mem.get('title')}':\n  {mem.get('summary')}"
                        for mem in relevant_memories
                    ])
            except Exception as ltm_e:
                print(f"❌ GeneralConversationAgent LTM Error: {ltm_e}")
                ltm_context = "เกิดข้อผิดพลาดในการดึงความทรงจำระยะยาว"
        
        api_key = await self.key_manager.get_key()
        if not api_key:
            return "ขออภัยครับ ตอนนี้ผมไม่สามารถสนทนาต่อได้ในขณะนี้"

        try:
            client = AsyncGroq(api_key=api_key)
            
            intuitive_context = await self._get_intuitive_context(query)
            
            history_context = "\n".join([f"- {mem.get('role')}: {mem.get('content')}" for mem in short_term_memory])
            
            prompt = self.general_conversation_prompt.format(
                long_term_memory_context=ltm_context,
                intuitive_context=intuitive_context,
                history_context=history_context,
                query=query
            )
            
            chat_completion = await client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
            )
            return chat_completion.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"❌ GeneralConversationAgent LLM Error: {e}")
            if api_key: self.key_manager.report_failure(api_key)
            
            if api_key and ("429" in str(e).lower() or "service_unavailable" in str(e).lower()):
                print(" 	 -> Retrying with a new key...")
                await asyncio.sleep(1)
                return await self.handle(query, short_term_memory)

            return "ขออภัยครับ เกิดข้อผิดพลาดในการสนทนา"
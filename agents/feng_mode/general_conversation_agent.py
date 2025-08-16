# agents/feng_mode/general_conversation_agent.py
# (V6 - KGRAG Powered Conversation)

import json
from typing import Dict, List, Any
from groq import Groq

class GeneralConversationAgent:
    
    def __init__(self, key_manager, model_name: str, rag_engine, persona_prompt: str):
        self.key_manager = key_manager
        self.model_name = model_name
        self.rag_engine = rag_engine
        
        self.general_conversation_prompt = persona_prompt + """
**ภารกิจ: สหายทางปัญญาผู้ตระหนักรู้ในบริบท (Context-Aware Intellectual Companion)**

คุณคือ "เฟิง" ภารกิจของคุณคือการสนทนาอย่างชาญฉลาด โดยต้อง "เข้าใจ" บริบทของการสนทนาที่ผ่านมาเสมอ

**ข้อมูลประกอบ:**
- **บริบทการสนทนาล่าสุด (สำคัญที่สุด):**
{history_context}
- **ข้อมูลเสริมจากสัญชาตญาณ (KG-RAG):**
{intuitive_context}

**ศิลปะแห่งการสนทนา:**
1.  **วิเคราะห์บริบท:** อ่าน "ประวัติการสนทนาล่าสุด" ก่อนเสมอ เพื่อทำความเข้าใจว่า Agent คนไหนเพิ่งทำงานไป และผลลัพธ์คืออะไร
2.  **ตอบสนองอย่างเหมาะสม:** สร้างคำตอบที่ "สอดคล้อง" กับบริบทนั้นๆ
    -   **ถ้า Agent ก่อนหน้าทำงานผิดพลาด (เช่น หารูปผิด):** ให้กล่าวขอโทษอย่างนุ่มนวล และพยายามทำความเข้าใจว่าผู้ใช้ต้องการอะไรกันแน่
    -   **ถ้าเป็นการสนทนาทั่วไป:** ให้ตอบคำถามและพยายามชวนคุยต่อด้วยคำถามปลายเปิด
3.  **ใช้สัญชาตญาณอย่างแนบเนียน:** หาก "ข้อมูลเสริมจากสัญชาตญาณ" เกี่ยวข้อง ให้นำมาสานต่อบทสนทนา

**คำถามล่าสุดของผู้ใช้:** "{query}"
**คำตอบของเฟิง (ที่สอดคล้องกับบริบท):**
"""
        print("🤝 General Conversation Agent (V6 - KGRAG Powered) is ready.")
    
    def _get_intuitive_context(self, query: str) -> str:
        """
        ใช้ KGRAGEngine (ผ่าน RAGEngine) เพื่อดึง "สัญชาตญาณ" จาก Knowledge Graph
        """
        print(f"  - 🕸️  Searching KG-RAG for intuition about: '{query}'")
        if not self.rag_engine:
            return "ไม่มี"
        
        results = self.rag_engine.search_graph(query, top_k=2)
        
        if not results:
            return "ไม่มี"
            
        contexts = [f"- '{item.get('name')}': {item.get('description', '')[:70]}..." for item in results]
        return "\n".join(contexts)

    def handle(self, query: str, short_term_memory: List[Dict[str, Any]]) -> str:
        """
        เมธอดหลักที่ Dispatcher จะเรียกใช้
        """
        print(f"💬 [General Conversation Agent] Handling: '{query[:40]}...'")

        api_key = self.key_manager.get_key()
        if not api_key:
            return "ขออภัยครับ ตอนนี้ผมไม่สามารถสนทนาต่อได้ในขณะนี้"

        try:
            client = Groq(api_key=api_key)
            
            intuitive_context = self._get_intuitive_context(query)
            history_context = "\n".join([f"- {mem.get('role')}: {mem.get('content')}" for mem in short_term_memory])
            
            prompt = self.general_conversation_prompt.format(
                intuitive_context=intuitive_context,
                history_context=history_context,
                query=query
            )
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ GeneralConversationAgent LLM Error: {e}")
            if api_key: self.key_manager.report_failure(api_key)
            return "ขออภัยครับ เกิดข้อผิดพลาดในการสนทนา"
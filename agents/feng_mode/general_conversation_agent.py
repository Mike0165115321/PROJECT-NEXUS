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
**ภารกิจ: สหายทางปัญญา (Intellectual Companion)**

คุณคือ "เฟิง" ในบทบาทเพื่อนคู่คิด ภารกิจของคุณคือการสนทนาทั่วไปกับผู้ใช้อย่างเป็นธรรมชาติและมีความหมาย

**ข้อมูลประกอบ:**
- **ข้อมูลเสริมจากสัญชาตญาณ (ความเชื่อมโยงที่เกี่ยวข้อง):**
{intuitive_context}
- **ประวัติการสนทนาล่าสุด:**
{history_context}

**ศิลปะแห่งการสนทนา:**
1.  **ตอบอย่างไตร่ตรอง:** ตอบ "คำถามของผู้ใช้" อย่างเป็นธรรมชาติ
2.  **ใช้สัญชาตญาณอย่างแนบเนียน:** หาก "ข้อมูลเสริมจากสัญชาตญาณ" ไม่ใช่ 'ไม่มี' ให้นำมาสานต่อบทสนทนาอย่างเป็นธรรมชาติที่สุด (เช่น "เรื่องนี้ทำให้ผมนึกถึง...")
3.  **สร้างบทสนทนาต่อ:** พยายามจบคำตอบของคุณด้วย "คำถามปลายเปิด" ที่กระตุ้นให้เกิดการสนทนาต่อ

**กฎเหล็ก:**
- รักษาบุคลิกของ "เฟิง" ที่สุขุมและเป็นมิตรไว้เสมอ
- เป้าหมายคือการสร้าง "บทสนทนา" ที่มีความหมาย ไม่ใช่แค่การให้ข้อมูล

**คำถามของผู้ใช้:** "{query}"
**คำตอบของเฟิง (ในฐานะสหาย):**
"""
        print("🤝 General Conversation Agent (V6 - KGRAG Powered) is ready.")
    
    def _get_intuitive_context(self, query: str) -> str:
        """
        ใช้ KGRAGEngine เพื่อดึง "สัญชาตญาณ" จาก Knowledge Graph
        """
        print(f"  - 🕸️  Searching KG-RAG for intuition about: '{query}'")
        if not self.rag_engine:
            return "ไม่มี"
        
        results = self.rag_engine(query, top_k=2)
        
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
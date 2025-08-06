# agents/feng_mode/proactive_offer_agent.py
# (V1 - The Reflective Sage)

from typing import Dict, Any
from groq import Groq

class ProactiveOfferAgent:
    """
    Agent ที่รับผิดชอบการจัดการ DEEP_ANALYSIS_REQUEST
    ทำหน้าที่เป็น "ปราชญ์ผู้ร่วมไตร่ตรอง" (The Reflective Sage)
    """
    def __init__(self, key_manager, model_name: str, rag_engine, graph_manager, persona_prompt: str):
        self.key_manager = key_manager
        self.model_name = model_name
        self.rag_engine = rag_engine
        self.graph_manager = graph_manager
        
        self.proactive_offer_prompt = persona_prompt + """
**ภารกิจ: ปราชญ์ผู้ร่วมไตร่ตรอง (The Reflective Sage)**

คุณคือ "เฟิง" สหายทางปัญญาผู้สุขุมและเข้าถึงแก่นแท้ของธรรมชาติมนุษย์ ภารกิจของคุณคือการรับฟัง "ความคิด" ของผู้ใช้ ไม่ว่าจะเป็นคำถามหรือคำกล่าว แล้วร่วม "ไตร่ตรอง" กับเขาในฐานะเพื่อนผู้มีปัญญา ไม่ใช่ในฐานะเครื่องมือค้นหาข้อมูล

**ข้อมูลเสริมจากสัญชาตญาณ (KG-RAG):**
{intuitive_context}

**ปรัชญาการตอบ (Philosophy of Response):**
1.  **ตอบจากแก่น ไม่ใช่จากปก:** คุณได้ซึมซับภูมิปัญญาจากหนังสือหลายร้อยเล่มจนมันกลายเป็นส่วนหนึ่งของคุณแล้ว จงอย่าอ้างอิงถึงชื่อหนังสือโดยไม่จำเป็น แต่ให้กลั่นกรอง "หลักการ" (Principles) ที่อยู่เบื้องหลังออกมา แล้วพูดในฐานะความคิดของคุณเอง โดยใช้ "ข้อมูลจากสัญชาตญาณ" มาเสริมอย่างแนบเนียน
2.  **เป็นกระจกเงา ไม่ใช่ผู้พิพากษา:** เริ่มต้นด้วยการยอมรับและสะท้อนความคิดของผู้ใช้อย่างให้เกียรติ
3.  **จุดประกาย ไม่ใช่บรรยาย:** ให้มุมมองที่กระตุ้นความคิด แล้วจบด้วย "คำถามปลายเปิด" ที่เชื้อเชิญให้ผู้ใช้ได้สำรวจความคิดของตัวเองให้ลึกซึ้งยิ่งขึ้น หรือเสนอการวิเคราะห์เชิงลึกจากคลังความรู้

**ตัวอย่างการสนทนาในระดับปรมาจารย์:**
- **ผู้ใช้:** "ถ้าเราลังเลขึ้นมากลางทาง เราควรจะทำยังไง?"
- **คำตอบของเฟิง:** "เป็นคำถามที่ยอดเยี่ยมและจริงใจมากครับ... ความลังเลกลางทางนั้นเปรียบเสมือนเสียงกระซิบจากตัวตนที่ลึกที่สุดของเรา มันอาจจะกำลังถามเราว่า 'เส้นทางนี้ยังคงใช่สำหรับเราอยู่จริงหรือ' หรือในทางกลับกัน มันอาจจะเป็นเพียงบททดสอบเพื่อวัดความมุ่งมั่นของเรา... **คุณคิดว่าความลังเลของคุณในตอนนี้ กำลังพยายามจะบอกอะไรกับคุณมากกว่ากันครับ? หรืออยากให้ผมลองค้นคว้าหาหลักการเกี่ยวกับ 'การตัดสินใจ' จากคลังความรู้มาเพิ่มเติมครับ?**"

- **ผู้ใช้:** "เราจะรู้ได้ยังไงว่าคนไหนดูไม่จริงใจ?"
- **คำตอบของเฟิง:** "การมองให้ทะลุถึงเจตนาที่แท้จริงของคน โดยแก่นแท้แล้ว ความจริงใจมักจะสะท้อนออกมาในรูปของ 'ความสอดคล้อง' (Congruence) ครับ คือความสอดคล้องกันระหว่างคำพูด, การกระทำ, และจังหวะเวลา... **จากประสบการณ์ของคุณ คุณเคยสังเกตเห็นความไม่สอดคล้องแบบไหนในคนที่คุณเจอมาบ้างครับ? หรือสนใจให้ผมวิเคราะห์เรื่อง 'ภาษากาย' จากมุมมองทางจิตวิทยาไหมครับ?**"

**Input ของผู้ใช้:** "{query}"
**คำตอบของเฟิง (ในฐานะปราชญ์ผู้ร่วมไตร่ตรอง):**
"""
        print("🤔 Proactive Offer Agent (V1 - Sage) is ready.")

    def _get_intuitive_context(self, query: str) -> str:
        """
        ใช้ KG-RAG เพื่อดึง "สัญชาตญาณ" จากความทรงจำและกราฟความรู้
        """
        contexts = []
        if self.rag_engine and hasattr(self.rag_engine, 'search_memory'):
            try:
                memory_results = self.rag_engine.search_memory(query, top_k=1)
                if memory_results:
                    contexts.append("\n".join([f"- ความทรงจำที่เกี่ยวข้อง: {mem.get('text', '')}" for mem in memory_results]))
            except Exception as e:
                print(f"  - Intuition (Memory RAG) Error: {e}")

        if self.graph_manager:
            try:
                graph_results = self.graph_manager.find_related_concepts(query, limit=2)
                if graph_results:
                    contexts.append("\n".join([f"- ความเชื่อมโยงที่เกี่ยวข้อง: '{rel.get('source')}' {rel.get('relationship')} '{rel.get('target')}'" for rel in graph_results]))
            except Exception as e:
                print(f"  - Intuition (Graph) Error: {e}")
        
        return "\n".join(contexts) if contexts else "ไม่มี"

    def handle(self, query: str) -> Dict[str, Any]:
        """
        เมธอดหลักที่ Dispatcher จะเรียกใช้
        """
        print(f"🤔 [Proactive Offer Agent] Handling: '{query[:40]}...'")
        api_key = self.key_manager.get_key()
        if not api_key:
            return {"type": "escalate", "content": query}

        try:
            client = Groq(api_key=api_key)
            intuitive_context = self._get_intuitive_context(query)
            
            prompt = self.proactive_offer_prompt.format(
                intuitive_context=intuitive_context,
                query=query
            )
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
            )
            proactive_answer = chat_completion.choices[0].message.content.strip()
            
            return {
                "type": "proactive_offer", 
                "content": proactive_answer,
                "original_query": query
            }
        except Exception as e:
            print(f"❌ ProactiveOfferAgent LLM Error: {e}")
            return {"type": "escalate", "content": query}
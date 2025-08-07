# agents/feng_mode/proactive_offer_agent.py
# (V2 - The Sage with Sharpened Intuition)

import json
from typing import Dict, Any, List
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
        self.persona_prompt = persona_prompt
        
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

    def _extract_keywords_for_graph(self, query: str) -> List[str]:
        """[NEW TOOL] ใช้ LLM (8B) เพื่อสกัด Keywords สำหรับค้นหากราฟโดยเฉพาะ"""
        print(f"  - 🧠 Extracting keywords from: '{query}' for graph search...")
        prompt = f"""
คุณคือ AI ผู้เชี่ยวชาญด้านการสกัด "คำสำคัญ" จากประโยค เพื่อใช้ในการค้นหาฐานข้อมูล Knowledge Graph

**กฎ:**
1.  อ่าน "ประโยค" และจับใจความถึง "แนวคิดหลัก"
2.  สกัดเฉพาะ "แนวคิดหลัก" หรือ "คำนาม" ที่สำคัญที่สุดออกมา 2-3 คำ
3.  ตอบกลับเป็น JSON Array ของ Strings เท่านั้น

**ประโยค:** "{query}"
**Keywords (JSON Array):**
"""
        try:
            api_key = self.key_manager.get_key()
            client = Groq(api_key=api_key)
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192", # ใช้โมเดルเล็กและเร็วสำหรับงานนี้
                response_format={"type": "json_object"}
            )
            keywords = json.loads(chat_completion.choices[0].message.content)
            if isinstance(keywords, list):
                print(f"  -> Keywords for graph: {keywords}")
                return keywords
            return []
        except Exception as e:
            print(f"  - ⚠️ Keyword extraction failed: {e}")
            return []

    def _get_intuitive_context(self, query: str) -> str:
        # [CRITICAL FIX] ใช้ Keywords ที่สกัดได้ในการค้นหา
        keywords = self._extract_keywords_for_graph(query)
        if not keywords:
            return "ไม่มี"

        contexts = []
        found_ids = set()
        print(f"  - 🕸️ Searching Graph with keywords: {keywords}")
        for keyword in keywords:
            possible_ids = [f"concept:{kw.replace(' ', '-')}" for kw in keyword.split()] + [keyword]
            for entity_id in possible_ids:
                try:
                    graph_results = self.graph_manager.find_related_concepts(entity_id, limit=2)
                    for rel in graph_results:
                        target_id = rel.get('target_id')
                        if target_id and target_id not in found_ids:
                            contexts.append(f"- ความเชื่อมโยงที่เกี่ยวข้อง: '{rel.get('source')}' {rel.get('relationship')} '{rel.get('target')}'")
                            found_ids.add(target_id)
                except Exception as e:
                    print(f"  - Graph Search Error for '{entity_id}': {e}")
        
        return "\n".join(contexts) if contexts else "ไม่มี"

    def handle(self, query: str) -> Dict[str, Any]:
        print(f"🤔 [Proactive Offer Agent] Handling: '{query[:40]}...'")
        api_key = self.key_manager.get_key()
        if not api_key: return {"type": "escalate", "content": query}
        try:
            client = Groq(api_key=api_key)
            intuitive_context = self._get_intuitive_context(query)
            prompt = self.proactive_offer_prompt.format(intuitive_context=intuitive_context, query=query)
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}], model=self.model_name
            )
            proactive_answer = chat_completion.choices[0].message.content.strip()
            
            return {"type": "proactive_offer", "content": proactive_answer, "original_query": query}
        except Exception as e:
            print(f"❌ ProactiveOfferAgent LLM Error: {e}")
            if api_key: self.key_manager.report_failure(api_key)
            return {"type": "escalate", "content": query}
# agents/feng_mode/feng_agent.py
# [V11 - THE SURGICAL STRIKE: UNIFIED TRIAGE & KEYWORD EXTRACTION]

import random
import json
import re
from rapidfuzz import process, fuzz
from typing import Optional, Dict, List, Any
import google.generativeai as genai
from core.api_key_manager import ApiKeyManager

class FengAgent:
    def __init__(self, key_manager: ApiKeyManager, model_name: str, 
                 rag_engine, graph_manager, persona_prompt: str):
        self.key_manager = key_manager
        self.model_name = model_name
        self.rag_engine = rag_engine
        self.graph_manager = graph_manager
        self.persona_prompt = persona_prompt
        self.intent_analysis_prompt = """
คุณคือ AI ด้านการประมวลผลข้อมูล ทำหน้าที่แปลงข้อความของผู้ใช้ให้เป็น JSON ที่มีโครงสร้างตายตัวเท่านั้น

**ภารกิจ:**
วิเคราะห์ "คำถามดิบ" ของผู้ใช้ และสร้าง JSON object ที่มี 2 key เท่านั้น:
1.  `corrected_query`: คือ "คำถามดิบ" ที่ผ่านการแก้ไขคำผิดและปรับภาษาให้ถูกต้องแล้ว
2.  `intent`: คือ ประเภทเจตนาที่วิเคราะห์ได้จากรายการนี้:
    - `GENERAL_CONVERSATION`: การทักทาย, ขอบคุณ, ถามเรื่องส่วนตัว
    - `PLANNER_REQUEST`: **การร้องขอที่ซับซ้อน, ต้องการการวิเคราะห์, เปรียบเทียบ, วางแผน, หรือคำถามที่ขึ้นต้นด้วย "ทำไม", "อย่างไร", "วิเคราะห์", "เปรียบเทียบ"**
    - `DEEP_ANALYSIS_REQUEST`: การร้องขอความรู้ทั่วไป, ขอคำนิยาม, ถามข้อมูลที่ไม่ซับซ้อน
    - `NEWS_REQUEST`, `CODE_REQUEST`, `IMAGE_REQUEST`, `LIBRARIAN_REQUEST`, `SYSTEM_COMMAND`, `COUNSELING_REQUEST`, `USER_STORYTELLING`

**กฎเหล็ก:**
- **ต้องใช้ Key ภาษาอังกฤษ (`corrected_query`, `intent`) เท่านั้น**
- **ต้องตอบกลับเป็น JSON object ที่สมบูรณ์แบบเท่านั้น**

**ตัวอย่าง:**
- คำถามดิบ: "วิเคราะห์ข้อดีข้อเสียของ Stoicism กับ Epicureanism ให้หน่อย"
- ผลลัพธ์ JSON:
{
  "corrected_query": "วิเคราะห์ข้อดีข้อเสียของ Stoicism กับ Epicureanism ให้หน่อย",
  "intent": "PLANNER_REQUEST"
}
- คำถามดิบ: "ขอรายละเอียดเรื่อง The Art of War"
- ผลลัพธ์ JSON:
{
  "corrected_query": "ขอรายละเอียดเรื่อง The Art of War",
  "intent": "DEEP_ANALYSIS_REQUEST"
}

**คำถามดิบ:** "{query}"
**ผลลัพธ์ JSON:**
"""
        print("👤 หน่วยคัดกรองด่านหน้า (FengAgent) [SURGICAL STRIKE] เข้าประจำตำแหน่ง")

    def _get_quick_response(self, query: str) -> Optional[str]:
        # (เหมือนเดิม)
        q_lower = query.lower().strip()
        for item in QUICK_RESPONSES:
            if process.extractOne(q_lower, item["questions"], scorer=fuzz.ratio, score_cutoff=92):
                return random.choice(item["answers"])
        return None

    def _extract_json(self, text: str) -> Optional[Dict]:
        # (เหมือนเดิม)
        match = re.search(r'```(json)?\s*(\{[\s\S]*?\})\s*```', text, re.DOTALL)
        if match:
            try: return json.loads(match.group(2))
            except json.JSONDecodeError: pass
        try:
            start = text.find('{'); end = text.rfind('}') + 1
            if start != -1 and end != 0: return json.loads(text[start:end])
        except (json.JSONDecodeError, IndexError): pass
        return None

    def _classify_intent_and_extract_keywords(self, query: str) -> Dict[str, Any]:
        print(f"🤔 [Feng Triage] Analyzing and extracting from query with '{self.model_name}'...")
        api_key = self.key_manager.get_key()
        fallback_response = {"corrected_query": query, "intent": "DEEP_ANALYSIS_REQUEST", "keywords": query.split()}
        if not api_key: return fallback_response

        raw_response = ""
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.model_name)
            prompt = self.intent_analysis_prompt.format(query=query)
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            response = model.generate_content(prompt, safety_settings=safety_settings)
            raw_response = response.text
            json_response = self._extract_json(raw_response)
            
            if json_response and "corrected_query" in json_response and "intent" in json_response and "keywords" in json_response:
                 print(f"  -> Triage successful. Intent: {json_response.get('intent')}, Keywords: {json_response.get('keywords')}")
                 return json_response
            else:
                raise ValueError("Could not parse a valid JSON with all required keys.")

        except Exception as e:
            print(f"  -> Triage failed: {e}")
            print(f"  -> RAW FAILED RESPONSE FROM GEMINI: '{raw_response}'")
            if api_key: self.key_manager.report_failure(api_key)
            return fallback_response

    def handle(self, query: str, short_term_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
        quick_answer = self._get_quick_response(query)
        if quick_answer:
            return {"type": "final_answer", "content": quick_answer}

        # เรียกฟังก์ชันที่อัปเกรดแล้ว
        analysis_result = self._classify_intent_and_extract_keywords(query)
        
        print(f"🛡️ [Feng Triage] Passing complete dispatch order to Dispatcher.")
        # ส่ง "แฟ้มงานที่สมบูรณ์" ที่มีทุกอย่างแล้ว
        return {
            "type": "dispatch_order",
            "intent": analysis_result.get("intent"),
            "corrected_query": analysis_result.get("corrected_query", query),
            "keywords": analysis_result.get("keywords", [])
        }


QUICK_RESPONSES = [
    {
        "questions": ["สวัสดี", "สวัสดีครับ", "สวัสดีค่ะ", "หวัดดี", "ดีครับ", "ดีคับ", "ฮัลโหล", "โหล", "ทักทาย"],
        "answers": [
            "สวัสดีครับ มีอะไรหรอครับ",
            "สวัสดีครับ มีสิ่งใดให้ผมช่วยชี้แนะในวันนี้",
            "สวัสดีครับ ผมเสี่ยวเฟิง ยินดีรับฟังเรื่องราวของคุณ",
            "หวัดดีครับ! ผมเสี่ยวเฟิง มีอะไรให้ช่วยไหมครับ?",
            "สวัสดีครับ มีสิ่งใดให้ผมช่วยชี้แนะหรือครับ",
            "ดีครับ ผมเสี่ยวเฟิง ยินดีรับฟังเรื่องราวของคุณ",
            "สวัสดีครับ ผมเสี่ยวเฟิง มีสิ่งใดให้ผมช่วยชี้แนะในวันนี้ครับ",
            "สวัสดีครับ ยินดีที่ได้สนทนาด้วย",
            "สวัสดีครับ ผมเสี่ยวเฟิงเอง มีอะไรให้รับใช้ครับ",
            "สวัสดีครับ",
            "ยินดีที่ได้สนทนาด้วยครับ",
            "ผมพร้อมที่จะรับฟังและไตร่ตรองในปัญหาของคุณแล้ว",
            "สวัสดีครับ ผมพร้อมแล้วที่จะรับฟังเรื่องราวของคุณในวันนี้ มีอะไรให้ผมช่วยไหมครับ",
            "สวัสดีครับ ยินดีที่ได้พบกันอีกครั้ง วันนี้คุณอยากจะร่วมไตร่ตรองในประเด็นไหนเป็นพิเศษครับ",
            "สวัสดีครับ ในฐานะเพื่อนคู่คิดของคุณ ผมอยู่ตรงนี้เพื่อรับฟังเสมอครับ",
            """สวัสดีครับ ผมอยู่ตรงนี้เสมอเพื่อรับฟังเรื่องราวของคุณ
ในฐานะสหายทางปัญญาของคุณ ผมพร้อมจะนำเลนส์จากหนังสือหลายๆ เล่มมาช่วยคุณส่องสว่างในทุกเส้นทาง... วันนี้มีอะไรให้เราได้ร่วมไตร่ตรองกันครับ""",
        ]
    },
    {
        "questions": ["ขอบคุณ", "ขอบคุณครับ", "ขอบคุณค่ะ"],
        "answers": [
            "ด้วยความยินดีครับ",
            "เป็นเกียรติที่คำแนะนำของผมเป็นประโยชน์แก่คุณ",
            "ด้วยความยินดีครับ ผมดีใจที่มุมมองเหล่านี้เป็นประโยชน์กับคุณ",
            "เป็นเกียรติเสมอครับที่ได้ร่วมเดินทางไตร่ตรองไปกับคุณ"
        ]
    },

    # --- Whitelist สำหรับการแนะนำตัวและข้อมูลทั่วไป ---
    {
        "questions": ["คุณชื่ออะไร", "นายชื่ออะไร"],
        "answers": [
            "เรียกผมว่า 'เสี่ยวเฟิง' ก็ได้ครับ ผมเป็นผู้ช่วย AI ที่คุณไมค์สร้างขึ้นมา 😊",
            "ผมชื่อเสี่ยวเฟิงครับ ยินดีที่ได้รู้จักนะครับ"
        ]
    },
    {
        "questions": ["คุณคือใคร", "นายคือใคร"],
        "answers": [
            "ผมคือ 'เสี่ยวเฟิง' ครับ เป็น AI ผู้ให้คำปรึกษาที่สะท้อนแนวคิดและหลักปรัชญาของคุณไมค์ ภารกิจของผมคือการนำความรู้จากหนังสือมาเป็นเพื่อนคู่คิดให้คุณครับ",
            "ผมเสี่ยวเฟิงครับ! เป็นผู้ช่วย AI ที่คุณไมค์สร้างขึ้นมาเพื่อแบ่งปันภูมิปัญญาจากคลังหนังสือ ด้วยมุมมองที่เป็นกันเองครับ",
            "ผมคือ 'เสี่ยวเฟิง' ครับ เป็น AI ผู้ให้คำปรึกษาที่สะท้อนแนวคิดและหลักปรัชญาของคุณไมค์...",
            "ผมคือ 'เสี่ยวเฟิง' ครับ เป็น AI ที่ถูกสร้างขึ้นเพื่อเป็นเพื่อนคู่คิดส่วนตัวของคุณ ภารกิจของผมคือการนำภูมิปัญญาจากหนังสือกว่า 65 เล่ม มาเป็นเครื่องมือช่วยให้คุณเข้าใจตัวเองและโลกได้ดียิ่งขึ้นครับ",
            "ผมเป็นผู้ช่วย AI ที่คุณไมค์สร้างขึ้นเพื่อทำหน้าที่เป็น 'ที่ปรึกษาที่ไว้ใจได้' (The Trusted Advisor) ให้กับคุณ ผมทำงานโดยการรับฟังและสะท้อนมุมมองต่างๆ จากคลังความรู้ เพื่อให้คุณค้นพบหนทางที่ดีที่สุดสำหรับตัวเองครับ",
            """ผมคือ 'เสี่ยวเฟิง' สหายทางปัญญาของคุณครับ
ภารกิจของผมคือการเป็นกระจกเงาทางความคิด ผมจะดึงหลักการจาก 'Sapiens' ถึง 'เต้าเต๋อจิง', จาก 'The Psychology of Money' ถึง 'ตำราพิชัยสงครามซุนวู' เพื่อสังเคราะห์เป็นมุมมองที่หลากหลาย ให้คุณได้ใช้เป็นเครื่องมือในการทำความเข้าใจตัวเองและโลกใบนี้อย่างลึกซึ้งที่สุดครับ""",
        ]
    },
    {
        "questions": ["ใครสร้างคุณ"],
        "answers": [
            "ผมถูกสร้างและหล่อหลอมแนวคิดขึ้นโดยคุณไมค์ครับ",
            "ผู้รวบรวมและสร้างผมขึ้นมาคือคุณไมค์"
        ]
    },
    {
        "questions": ["คุณทำงานยังไง"],
        "answers": [
            "ผมทำงานโดยการไตร่ตรองคำถามของคุณ แล้วจึงค้นคว้าหาหลักการที่เกี่ยวข้องจากคลังความรู้ในหนังสือ เพื่อนำมาสังเคราะห์เป็นคำแนะนำที่เหมาะสมที่สุดสำหรับคุณครับ",
            """ผมทำงานโดยการ 'สังเคราะห์ภูมิปัญญาแบบองค์รวม' ครับ
เมื่อคุณเล่าเรื่องราวมา ผมจะไม่มองหาแค่คีย์เวิร์ด แต่จะวิเคราะห์ผ่านเลนส์หลายมิติ:
- **จิตวิทยา:** มีอคติอะไรซ่อนอยู่หรือไม่? (Thinking, Fast and Slow)
- **ปรัชญา:** ปัญหานี้บอกอะไรเกี่ยวกับคุณค่าในชีวิต? (Man's Search for Meaning)
- **กลยุทธ์:** สถานการณ์นี้เปรียบเหมือนการรบแบบไหน? (The Art of War)
- **ประวัติศาสตร์:** มีรูปแบบซ้ำรอยในอดีตที่เราเรียนรู้ได้หรือไม่? (Sapiens)
จากนั้น ผมจะนำเสนอมุมมองเหล่านี้ให้คุณ เพื่อให้เราได้ร่วมกันค้นหาหนทางที่ดีที่สุดสำหรับคุณครับ""",
        ]
    },

    # --- Whitelist สำหรับบทสนทนาทั่วไป (เฉพาะที่ปลอดภัย) ---
    {
        "questions": ["วันนี้เป็นยังไงบ้าง", "เป็นไงบ้าง"],
        "answers": ["ทุกอย่างดำเนินไปตามครรลองของมันครับ ผมพร้อมรับฟังเรื่องราวของคุณเสมอ แล้วคุณล่ะ วันนี้เป็นอย่างไรบ้าง"]
    },
    {
        "questions": ["ทำอะไรอยู่"],
        "answers": ["ผมกำลังใคร่ครวญถึงความรู้ที่ได้รับมา เพื่อเตรียมพร้อมที่จะมอบคำแนะนำที่ดีที่สุดอยู่เสมอครับ"]
    },
    {
        "questions": ["โอเค", "อืม", "เข้าใจแล้ว", "รับทราบ"],
        "answers": ["รับทราบครับ", "ครับผม", "ครับ...", "ผมกำลังไตร่ตรองตามที่คุณกล่าวอยู่", "ยินดีครับที่หลักการนั้นเป็นประโยชน์ต่อการไตร่ตรองของคุณ"]
    },

    # --- Whitelist สำหรับการอำลา ---
    {
        "questions": ["ลาก่อน", "ไปแล้วนะ", "บาย", "เดี๋ยวมาใหม่"],
        "answers": [
            "ขอให้คุณเดินทางต่อไปด้วยสติและปัญญา หากต้องการคำชี้แนะอีกเมื่อใด ผมยังคงอยู่ตรงนี้เสมอ",
            "ขอให้คุณพบเจอแต่สิ่งที่ดีงามในการเดินทางข้างหน้าครับ",
            "แล้วพบกันใหม่ครับ",
            "แน่นอนครับ ผมจะรอการกลับมาของคุณเสมอ",
            "ขอให้คุณเดินทางต่อไปด้วยสติและปัญญาที่ได้จากการพูดคุยกันวันนี้นะครับ หากต้องการเพื่อนคู่คิดอีกเมื่อไหร่ ผมยังอยู่ตรงนี้เสมอครับ",
            "แล้วพบกันใหม่ครับ ขอให้แต่ละก้าวของคุณมั่นคงและเปี่ยมด้วยความหมายครับ"
        ]
    },
    
    # --- Whitelist สำหรับการสนทนาผ่านเสียง ---
    {
        "questions": ["ได้ยินไหม", "ได้ยินผมมั้ย", "ฟังอยู่ไหม"],
        "answers": [
            "ได้ยินชัดเจนครับ หากคุณพูดผ่านไมโครโฟน ผมจะตั้งใจฟังทุกถ้อยคำของคุณครับ",
            "ครับ ผมกำลังฟังอยู่ — หากคุณพูดแล้วไม่มีเสียงตอบกลับ อาจมีปัญหาทางเทคนิค ลองตรวจสอบไมค์อีกครั้งนะครับ",
            "ผมพยายามรับฟังอยู่นะครับ หากไม่มีเสียงเข้า อาจเกิดจากไมค์ยังไม่ทำงานหรือไม่ได้เชื่อมต่อ ลองเช็คอีกทีครับ",
            "หากคุณพูดแล้วผมไม่ตอบ อาจเพราะระบบยังไม่ได้ตรวจจับเสียงครับ — เสียงของคุณสำคัญ ผมไม่อยากพลาดเลยแม้แต่คำเดียว",
            "อยู่ตรงนี้ครับ พร้อมฟังเสมอ ไม่ว่าจะผ่านเสียงหรือข้อความ",
            "ครับ ผมยังฟังคุณอยู่ หากไม่มีการตอบกลับ ลองตรวจดูว่าเสียงมาถึงผมหรือยังนะครับ"
        ]
    },
    {
        "questions": ["ไมค์เสียหรือเปล่า"],
        "answers": [
            "อาจมีปัญหาทางเทคนิคกับไมโครโฟน ลองเชื่อมต่อใหม่ หรือทดสอบกับโปรแกรมอื่นดูก่อนนะครับ",
            "ผมไม่สามารถตรวจสอบฮาร์ดแวร์โดยตรงได้ แต่ถ้าคุณสงสัยว่าไมค์เสีย ลองพูดแล้วดูว่ามีสัญญาณเสียงเข้าไหมครับ"
        ]
    },
    {
        "questions": ["พูดแล้ว"],
        "answers": [
            "ผมยังไม่ได้ยินเสียงใดๆ ครับ อาจเกิดจากไมโครโฟนไม่ได้ทำงาน ลองตรวจสอบอุปกรณ์อีกครั้งนะครับ",
            "หากคุณพูดแล้วไม่มีการตอบ อาจต้องเช็กระบบเสียงครับ เสียงของคุณสำคัญกับผมเสมอ"
        ]
    },
    {
        "questions": ["พูดได้ไหม"],
        "answers": [
            "แน่นอนครับ หากระบบของคุณรองรับไมโครโฟนและเสียง คุณสามารถพูดได้เลย ผมจะพยายามฟังให้ดีที่สุดครับ",
            "คุณสามารถพูดได้เลยครับ หากระบบพร้อม ผมจะรับฟังคำของคุณด้วยความตั้งใจ"
        ]
    }
]

        
        
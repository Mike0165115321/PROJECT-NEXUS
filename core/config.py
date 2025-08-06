# core/config.py
# (V4.1 - Final & Fully Documented)
# นี่คือ "แผงควบคุมหลัก" ของ PROJECT NEXUS
# ทำหน้าที่โหลดข้อมูลลับและกำหนดค่าการทำงานทั้งหมดของระบบจากที่เดียว

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GOOGLE_API_KEYS = [key.strip() for key in os.getenv("GOOGLE_API_KEYS", "").split(',') if key.strip()]
    GROQ_API_KEYS = [key.strip() for key in os.getenv("GROQ_API_KEYS", "").split(',') if key.strip()]

    # โมเดลต่างๆ ที่ใช้ในระบบ
    # >> ใช้ใน `knowledge_extractor.py` (ทางเลือกสำหรับหนังสือที่ซับซ้อน) ⭐️ สับสวิตช์มาที่นี่ ⭐️
    #KNOWLEDGE_EXTRACTOR_MODEL = os.getenv("KNOWLEDGE_EXTRACTOR_MODEL", "gemini-1.5-flash-latest")
    KNOWLEDGE_EXTRACTOR_MODEL = os.getenv("KNOWLEDGE_EXTRACTOR_MODEL", "llama3-70b-8192")

    # >> ใช้ใน `agents/planning_mode/planner_agent.py`
    PLANNER_AGENT_MODEL = os.getenv("PLANNER_AGENT_MODEL", "gemini-1.5-flash-latest")
    
    # >> ใช้ใน `agents/formatter_agent.py`
    FORMATTER_AGENT_MODEL = os.getenv("FORMATTER_AGENT_MODEL", "gemini-1.5-flash-latest")
    
    # >> ใช้ใน `agents/counseling_mode/counselor_agent.py`
    COUNSELOR_AGENT_MODEL = os.getenv("COUNSELOR_AGENT_MODEL", "gemini-1.5-flash-latest")

    # --- 🚀 สังกัด Groq: Llama 3 (สำหรับความเร็วและความฉลาดที่สมดุล) ---

    # >> โมเดลหลักสำหรับ "เฟิง" (สนทนา, เสนอ) และ "นักข่าว"
    # >> ใช้ใน `agents/feng_mode/*_agent.py` และ `agents/news_mode/news_agent.py`
    FENG_PRIMARY_MODEL = os.getenv("FENG_PRIMARY_MODEL", "llama3-70b-8192")
    NEWS_AGENT_MODEL = os.getenv("NEWS_AGENT_MODEL", "llama3-70b-8192")
    
    # >> โมเดลรองสำหรับ "เฟิง" (วิเคราะห์เจตนา)
    # >> ใช้ใน `agents/feng_mode/feng_agent.py`
    FENG_SECONDARY_MODEL = os.getenv("FENG_SECONDARY_MODEL", "llama3-8b-8192")
    
    # >> โมเดลเริ่มต้นสำหรับเครื่องมือและงานเบื้องหลังทั้งหมด
    DEFAULT_UTILITY_MODEL = "llama3-8b-8192"
    
    # >> ใช้ใน `agents/coder_mode/code_interpreter_agent.py`
    CODE_AGENT_MODEL = os.getenv("CODE_AGENT_MODEL", DEFAULT_UTILITY_MODEL)
    
    # >> ใช้ใน `agents/consultant_mode/librarian_agent.py`
    LIBRARIAN_AGENT_MODEL = os.getenv("LIBRARIAN_AGENT_MODEL", DEFAULT_UTILITY_MODEL)
    
    # >> ใช้ใน `core/long_term_memory_manager.py`
    LTM_MODEL = os.getenv("LTM_MODEL", DEFAULT_UTILITY_MODEL)

    # >> ใช้ใน `agents/storytelling_mode/listener_agent.py`
    LISTENER_AGENT_MODEL = os.getenv("LISTENER_AGENT_MODEL", DEFAULT_UTILITY_MODEL)

    # >> ใช้ใน `agents/utility_mode/apology_agent.py`
    APOLOGY_AGENT_MODEL = os.getenv("APOLOGY_AGENT_MODEL", DEFAULT_UTILITY_MODEL)

    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

settings = Settings()
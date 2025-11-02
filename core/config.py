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
    
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
    PRIMARY_GEMINI_MODEL = "gemini-2.5-flash"
    PRIMARY_GROQ_MODEL = "llama-3.3-70b-versatile"
    SECONDARY_GROQ_MODEL = "llama-3.1-8b-instant"

    IMAGE_AGENT_MODEL = os.getenv("IMAGE_AGENT_MODEL", PRIMARY_GROQ_MODEL)

    KNOWLEDGE_EXTRACTOR_MODEL = os.getenv("KNOWLEDGE_EXTRACTOR_MODEL", PRIMARY_GEMINI_MODEL)

    PLANNER_AGENT_MODEL = os.getenv("PLANNER_AGENT_MODEL", PRIMARY_GEMINI_MODEL)

    FORMATTER_AGENT_MODEL = os.getenv("FORMATTER_AGENT_MODEL", PRIMARY_GEMINI_MODEL)

    COUNSELOR_AGENT_MODEL = os.getenv("COUNSELOR_AGENT_MODEL", PRIMARY_GEMINI_MODEL)

    FENG_PRIMARY_MODEL = os.getenv("FENG_PRIMARY_MODEL", PRIMARY_GROQ_MODEL)

    FENG_SECONDARY_MODEL = os.getenv("FENG_SECONDARY_MODEL", PRIMARY_GROQ_MODEL)

    NEWS_AGENT_MODEL = os.getenv("NEWS_AGENT_MODEL", PRIMARY_GEMINI_MODEL)

    DEFAULT_UTILITY_MODEL = SECONDARY_GROQ_MODEL

    CODE_AGENT_MODEL = os.getenv("CODE_AGENT_MODEL", DEFAULT_UTILITY_MODEL)

    LIBRARIAN_AGENT_MODEL = os.getenv("LIBRARIAN_AGENT_MODEL", DEFAULT_UTILITY_MODEL)

    LTM_MODEL = os.getenv("LTM_MODEL", DEFAULT_UTILITY_MODEL)

    LISTENER_AGENT_MODEL = os.getenv("LISTENER_AGENT_MODEL", DEFAULT_UTILITY_MODEL)

    APOLOGY_AGENT_MODEL = os.getenv("APOLOGY_AGENT_MODEL", DEFAULT_UTILITY_MODEL)

    MEMORY_AGENT_MODEL = os.getenv("MEMORY_AGENT_MODEL", PRIMARY_GROQ_MODEL)

    NEWS_KEY = os.getenv("NEWS_API_KEY")

    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

settings = Settings()
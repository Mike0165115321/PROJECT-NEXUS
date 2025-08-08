# 🧠 PROJECT NEXUS: An Advanced AI Intellectual Companion

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![Models](https://img.shields.io/badge/Models-Gemini%20%7C%20Llama%203-purple.svg)](https://deepmind.google/technologies/gemini/)
[![Database](https://img.shields.io/badge/Database-Neo4j%20%7C%20FAISS-orange.svg)](https://neo4j.com/)

**Project Nexus** คือ "สหายทางปัญญา" (Intellectual Companion) ที่ถูกสร้างขึ้นบนสถาปัตยกรรม **"Dispatcher-Centric Mixture of Experts & Models"** ที่ซับซ้อนและทรงพลัง มันไม่ได้เป็นเพียง AI ตัวเดียว แต่เป็น "ระบบนิเวศ" ของผู้เชี่ยวชาญเฉพาะทางที่ทำงานร่วมกันภายใต้การบัญชาการของ "ผู้ควบคุมวงออร์เคสตรา" กลาง เพื่อมอบประสบการณ์การสนทนาที่ลึกซึ้ง, มีเหตุผล, และเข้าใจในอารมณ์

---

## 🏛️ สถาปัตยกรรมหลัก: The Layered Architectural Blend

Project Nexus ไม่ได้ใช้สถาปัตยกรรมเพียงหนึ่งเดียว แต่เป็นการ "หลอมรวมสถาปัตยกรรมหลายชั้น" ที่ทำงานร่วมกันอย่างเป็นระบบ:

### 1. สถาปัตยกรรมระดับ AI และการตัดสินใจ (AI & Decision-Making)
- **Dispatcher-Centric Mixture of Experts (MoE):** หัวใจของระบบคือ `Dispatcher` ที่ทำหน้าที่เป็น "ผู้ควบคุมวง" รับ "แฟ้มงาน" ที่ผ่านการคัดกรองจาก `FengAgent` แล้วบัญชาการมอบหมายภารกิจให้ "ผู้เชี่ยวชาญ" (Agent) ที่เหมาะสมที่สุด
- **Hybrid Model Strategy (Mixture of Models):** ผสมผสานจุดแข็งของโมเดลจากหลายสังกัด:
  - **Google Gemini 1.5 Flash:** สำหรับงานที่ต้องการคุณภาพ, ความลึกซึ้ง, และการให้เหตุผลเชิงอารมณ์
  - **Groq (Llama 3 8B & 70B):** สำหรับงานที่ต้องการความเร็วสูงและความฉลาดที่สมดุล เช่น การสนทนาโต้ตอบ, การคัดกรอง, และการสรุปผล
- **Advanced RAG & KG-RAG:** กระดูกสันหลังของการค้นหาความรู้เชิงลึก โดยใช้เทคนิค `Plan-Retrieve-Synthesize` และการดึงข้อมูลจาก Knowledge Graph (Neo4j) และ Vector Store (FAISS) พร้อมกันเพื่อสร้าง "สัญชาตญาณ" ให้กับ AI

### 2. สถาปัตยกรรมระดับแอปพลิเคชันและบริการ (Application & Service)
- **Service-Oriented & API-Driven:** ออกแบบภายในแบบแยกส่วนอย่างชัดเจน โดยมี `main.py` (FastAPI) ทำหน้าที่เป็น Gateway กลาง ให้บริการ API Endpoints ทำให้พร้อมที่จะถูกแยกเป็น Microservices ในอนาคต

### 3. สถาปัตยกรรมระดับข้อมูลและซอฟต์แวร์ (Data & Software)
- **ETL Pipelines:** มี "โรงงานข้อมูล" แยกต่างหาก (`knowledge_extractor_*.py`, `manage_data.py`) สำหรับบำรุงรักษาคลังความรู้
- **Modular Architecture & Dependency Injection:** โครงสร้างโปรเจกต์ถูกออกแบบเป็นโมดูล (core, agents) และใช้หลักการ Dependency Injection อย่างสมบูรณ์ ทำให้โค้ดสะอาด, ทดสอบง่าย, และง่ายต่อการบำรุงรักษา

---

## ✨ คุณสมบัติหลัก (Key Features)

- **ทีมผู้เชี่ยวชาญเฉพาะทาง (Multi-Agent Expertise):**
  - **Counselor:** ให้คำปรึกษาและพื้นที่ปลอดภัยเชิงอารมณ์
  - **Coder & Interpreter:** ให้คำแนะนำ, เขียน, และรันโค้ดใน Sandbox
  - **Librarian:** ให้ข้อมูลและแนะนำหนังสือจากฐานความรู้
  - **News Editor:** สรุปข่าวสารล่าสุดจากแหล่งข้อมูลออนไลน์
  - **Listener:** กระตุ้นและรับฟังเรื่องราวจากผู้ใช้
  - **Formatter:** บรรณาธิการใหญ่ที่ขัดเกลาคำตอบสุดท้ายให้สละสลวย
- **หน่วยคัดกรองอัจฉริยะ (`FengAgent`):** ทำหน้าที่เป็นประตูบานแรกในการแก้ไขคำผิดและวิเคราะห์เจตนาของผู้ใช้ก่อนส่งต่อภารกิจ
- **ความทรงจำหลายมิติ (Multi-faceted Memory):**
  - **Short-Term:** ความจำระยะสั้นสำหรับการสนทนา (SQLite)
  - **Long-Term:** ความจำระยะยาวที่สามารถค้นหาได้ (Vector Store)
  - **Structural:** ความเข้าใจเชิงโครงสร้างความสัมพันธ์ (Knowledge Graph - Neo4j)
- **Web Interface:** หน้าเว็บสำหรับโต้ตอบกับ AI พร้อมระบบแสดงผล Knowledge Graph แบบ Interactive

---

## 🚀 การติดตั้งและใช้งาน (Installation & Usage)

**Prerequisites:**
- Python 3.12+
- Git
- Neo4j Desktop (หรือ AuraDB)

**1. Clone Repository:**
```
git clone https://github.com/Mike0165115321/PROJECT-NEXUS.git
cd PROJECT-NEXUS
```
2. สร้างและเปิดใช้งาน Virtual Environment:
```
pip install -r requirements.txt
```
3. ติดตั้ง Dependencies:
```
pip install -r requirements.txt
```
4. ตั้งค่า Environment Variables:
สร้างไฟล์ชื่อ .env ในโฟลเดอร์หลักของโปรเจกต์
เพิ่ม API Keys และข้อมูลการเชื่อมต่อของคุณลงในไฟล์ .env ดังนี้:
```
# AI Model Keys
GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
GROQ_API_KEY="YOUR_GROQ_API_KEY_HERE"

# Neo4j Database Credentials
NEO4J_URI="bolt://localhost:7687"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="YOUR_NEO4J_PASSWORD"
```
5. เตรียมฐานข้อมูลและคลังความรู้:
รันสคริปต์ ETL เพื่อประมวลผลข้อมูลดิบและสร้างฐานข้อมูลความรู้ทั้งหมด:
```
# สร้าง Vector Index สำหรับหนังสือ
python manage_data.py

# (ตัวเลือก) สกัด Knowledge Graph จากข้อมูล
python knowledge_extractor_gemini.py
```
6. รันแอปพลิเคชัน:
```
uvicorn main:app --reload
เปิดเว็บเบราว์เซอร์แล้วไปที่ http://127.0.0.1:8000
```

🌊 โฟลว์การทำงาน: The Conductor Architecture
กระบวนการทั้งหมดถูกควบคุมโดย dispatcher.py ซึ่งเปรียบเสมือน "ผู้ควบคุมวงออร์เคสตรา" (The Conductor) ที่ทำหน้าที่บัญชาการ "ทีมผู้เชี่ยวชาญ" ทั้งหมดตามลำดับขั้นตอนที่ชัดเจน:
Flow 0: Continuing Mission
หน้าที่: ตรวจสอบภารกิจต่อเนื่อง
กระบวนการ: Dispatcher จะตรวจสอบเป็นอันดับแรกว่าผู้ใช้กำลังตอบรับ "ข้อเสนอ" การวิเคราะห์เชิงลึกจากภารกิจก่อนหน้าหรือไม่ หากใช่ จะดึงคำถามดั้งเดิมออกมาและข้ามไปยัง Flow 2 ทันที
Flow 1: Intelligent Triage
ผู้รับผิดชอบ: FengAgent (หน่วยคัดกรองอัจฉริยะ)
กระบวนการ: FengAgent จะรับ Query เข้ามา หากเป็นคำถามพื้นฐาน (ทักทาย/อำลา) จะตอบกลับทันที หากไม่ใช่ จะทำการ "แก้ไขคำผิด" และ "วิเคราะห์เจตนา" ของผู้ใช้ แล้วสร้างเป็น "แฟ้มงาน (Dispatch Order)" ส่งกลับไปให้ Dispatcher
Flow 2: Intent-based Delegation
ผู้รับผิดชอบ: Dispatcher
กระบวนการ: Dispatcher รับ "แฟ้มงาน" จาก FengAgent แล้วใช้ intent_to_agent_map เพื่อเลือก "ผู้เชี่ยวชาญ (Agent)" ที่เหมาะสมที่สุดสำหรับภารกิจนั้นๆ ก่อนจะส่งมอบงานต่อไป
Flow 3: Finalization & Memory
ผู้รับผิดชอบ: Dispatcher และ FormatterAgent
กระบวนการ: Dispatcher รับผลลัพธ์จาก Agent ผู้ปฏิบัติการ, ส่งต่อให้ FormatterAgent ทำการขัดเกลาภาษา (ถ้าจำเป็น), บันทึกบทสนทนาลงใน "ความทรงจำ (Memory)", และสุดท้ายจึงสร้างเป็น FinalResponse ส่งกลับไปให้ผู้ใช้
🛡️ Safety Net
ผู้รับผิดชอบ: ApologyAgent
กระบวนการ: หากเกิดข้อผิดพลาดร้ายแรง (Exception) ใน Flow ใดๆ ก็ตาม Dispatcher จะดักจับ Error นั้นไว้และเรียกใช้ ApologyAgent เพื่อสร้างคำขอโทษที่เหมาะสมและจัดการสถานการณ์อย่างนุ่มนวล
💡 ปรัชญาของโปรเจกต์: จาก "โปรแกรม" สู่ "สหายทางปัญญา"
การเดินทางของโปรเจกต์นี้เริ่มต้นจากการแก้ไขปัญหาทางเทคนิค แต่ได้นำไปสู่การ "ปฏิวัติสถาปัตยกรรม" ครั้งสำคัญ:
จาก All-in-One สู่ Mixture of Experts:
เราได้แยกส่วนความสามารถที่ซับซ้อนออกมาเป็น "ทีมผู้เชี่ยวชาญ" ที่มีหน้าที่ชัดเจน (Planner, Counselor, Listener, Formatter)
จาก Agent-Centric สู่ Dispatcher-Centric:
เราได้เปลี่ยน Dispatcher จากแค่ "ผู้จ่ายงาน" ให้กลายเป็น "ผู้ควบคุมวงออร์เคสตรา" ที่ชาญฉลาด ทำให้การทำงานร่วมกันของ Agent ทั้งหมดเป็นไปอย่างมีระบบ
จากค่ายเดียวสู่ทีมผสม:
เราได้ทำการ "สรรหาบุคลากร" จากหลายสังกัด โดยนำความ "เร็ว" ของ Groq (Llama 3) มาเสริมทัพความ "ลึกซึ้ง" ของ Google (Gemini) สร้างเป็นทีม AI ที่มีความสามารถรอบด้าน
การหลอมรวม "จิตวิญญาณ":
ท้ายที่สุด เราได้สร้าง "จิตวิญญาณ" ให้กับ AI ผ่านการออกแบบ Prompt อย่างละเอียดลึกซึ้ง
ทำให้ PROJECT NEXUS ไม่ใช่แค่ "โปรแกรม" อีกต่อไป แต่มันคือ "ระบบนิเวศ AI ที่มีชีวิต" ที่พร้อมจะเป็น "สหาย" ร่วมไตร่ตรองไปกับผู้ใช้


📄 License
โปรเจกต์นี้อยู่ภายใต้ลิขสิทธิ์ของ MIT License.
```

#### **ขั้นตอนที่ 3: บันทึกและอัปโหลดขึ้น GitHub**

หลังจากที่คุณวางเนื้อหาและ **Save** ไฟล์ `README.md` เรียบร้อยแล้ว ให้กลับไปที่ **Terminal** แล้วรัน 3 คำสั่งสุดท้ายนี้:

```bash
# 1. เตรียมไฟล์ README.md ที่แก้ไข
git add README.md

# 2. บันทึกการเปลี่ยนแปลง
git commit -m "docs: Create comprehensive, architecturally-driven README"

# 3. อัปเดตขึ้น GitHub
git push
```


<!-- THAI VERSION -->
# 🧠 PROJECT NEXUS: The Unified Engine Architecture

> **"สหายทางปัญญา" (Intellectual Companion)** ที่ถูกสร้างขึ้นบนสถาปัตยกรรมแบบผสมผสาน (Hybrid Architecture) ที่ซับซ้อนและทรงพลัง โดยมี **Dispatcher** ทำหน้าที่เป็น "ผู้ควบคุมวงออร์เคสตรา" ของ **"ทีมผู้เชี่ยวชาญ" (Mixture of Experts)** ที่ใช้ขุมพลังจาก **"โมเดลหลายสังกัด" (Mixture of Models)** การตัดสินใจทั้งหมดขับเคลื่อนด้วยตรรกะ **Chain of Thought** และความสามารถในการให้เหตุผลขั้นสูงจากเทคนิค **Advanced RAG** และ **Unified RAG Engine Architecture** ทั้งหมดนี้ถูกให้บริการผ่านสถาปัตยกรรม **API-Driven** ที่ทันสมัย, ยืดหยุ่น, และพร้อมสำหรับการขยายขนาดในอนาคต

[![Python Version](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<div align="right">
  <a href="#-project-nexus-the-unified-engine-architecture-english-version"><strong>English Version</strong></a>
</div>

---

**PROJECT NEXUS** ไม่ใช่แค่ Chatbot แต่คือ **"ระบบนิเวศ AI ที่มีชีวิต"** ที่วิวัฒนาการจากโปรแกรมธรรมดามาสู่ "สหาย" ที่พร้อมจะร่วมไตร่ตรองและค้นคว้าไปกับผู้ใช้ โปรเจกต์นี้ไม่ได้ใช้สถาปัตยกรรมเพียงหนึ่งเดียว แต่เป็นการ **"หลอมรวมสถาปัตยกรรมหลายชั้น" (Layered Architectural Blend)** ที่ทำงานร่วมกันอย่างเป็นระบบ เพื่อสร้าง AI ที่มีความสามารถหลากหลาย, เข้าใจบริบทเชิงลึก, และมีบุคลิกภาพที่สอดคล้องกันภายใต้ตัวตนของ "เฟิง"

## 🏛️ สถาปัตยกรรมหลัก: 3 ระดับแห่งความอัจฉริยะ

Project Nexus ถูกสร้างขึ้นบนสถาปัตยกรรม 3 ระดับที่ทำงานร่วมกันอย่างสมบูรณ์:

### 1. ระดับ AI และการตัดสินใจ (The AI & Decision-Making Layer)
*   **หัวใจ - Dispatcher-Centric Mixture of Experts (MoE):** `Dispatcher` ทำหน้าที่เป็น "ผู้ควบคุมวงออร์เคสตรา" รับ "แฟ้มงาน" ที่ผ่านการคัดกรองจาก `FengAgent` แล้วบัญชาการมอบหมายภารกิจให้ "ทีมผู้เชี่ยวชาญ" (Agents) ที่เหมาะสมที่สุด ทำให้ระบบตัดสินใจได้อย่างซับซ้อนและเป็นระบบ
*   **ขุมพลัง - Hybrid Model Strategy:** ผสมผสานจุดแข็งของโมเดลจากหลายสังกัดอย่างมีกลยุทธ์:
    *   **Google Gemini 1.5 Flash:** สำหรับงานที่ต้องการ "คุณภาพและความลึกซึ้ง" (การวางแผน, ให้คำปรึกษา, ขัดเกลาภาษา)
    *   **Groq (Llama 3 70B & 8B):** สำหรับงานที่ต้องการ "ความเร็วและความฉลาดที่สมดุล" (การสนทนา, สรุปข่าว, เขียนโค้ด)
*   **กระดูกสันหลัง - Advanced & Unified RAG:**
    *   **Plan-Retrieve-Synthesize:** กระบวนการค้นหาความรู้เชิงลึกแบบ 3 ขั้นตอนที่ `PlannerAgent` ใช้ในการสร้างบทวิเคราะห์คุณภาพสูง
    *   **Unified RAG Engine Architecture:** "คลังแสงข้อมูล" ที่มี Engine เฉพาะทาง 3 ตัว (Book, KG, News) เพื่อความแม่นยำสูงสุด

### 2. ระดับแอปพลิเคชันและบริการ (The Application & Service Layer)
*   **Service-Oriented & API-Driven:** `main.py` (FastAPI) ทำหน้าที่เป็น API Gateway กลาง ทำให้ Backend และ Frontend แยกจากกันอย่างสมบูรณ์ และพร้อมที่จะถูกแยกเป็น Microservices ในอนาคต
*   **Client-Server Architecture:** `web/` ทำหน้าที่เป็น Client ที่ส่ง Request ไปยัง `main.py` ซึ่งเป็น Server ประมวลผล

### 3. ระดับข้อมูลและซอฟต์แวร์ (The Data & Software Layer)
*   **ETL Pipelines:** "โรงงานข้อมูล" ที่มีสคริปต์แยกต่างหาก (`manage_*.py`, `knowledge_extractor_*.py`) สำหรับการสร้างและบำรุงรักษาคลังความรู้ทั้งหมด
*   **Modular Architecture & Dependency Injection:** โครงสร้างโปรเจกต์ถูกแบ่งเป็นโมดูล (core, agents, data) และใช้หลักการ Dependency Injection ใน `main.py` เพื่อโค้ดที่สะอาด, ทดสอบง่าย, และบำรุงรักษาได้ในระยะยาว

---

## 🌊 การไหลของตรรกะ: จากคำถามสู่ภูมิปัญญา

กระบวนการทำงานทั้งหมดถูกควบคุมโดย `dispatcher.py` อย่างสง่างาม:

1.  **Flow 0: ภารกิจต่อเนื่อง (Continuing Mission):** ระบบสามารถจดจำ "ข้อเสนอ" การวิเคราะห์เชิงลึก และดำเนินการต่อได้ทันทีเมื่อผู้ใช้ตอบรับ ทำให้เกิดการสนทนาแบบหลายขั้นตอน (Multi-turn) ที่ราบรื่น
2.  **Flow 1: การคัดกรองอัจฉริยะ (Intelligent Triage):** `FengAgent` ทำหน้าที่เป็นประตูบานแรก ตอบคำถามง่ายๆ ทันทีด้วย Whitelist และใช้ LLM วิเคราะห์เจตนา (Intent) ของคำถามที่ซับซ้อน ก่อนสร้าง "แฟ้มงาน" ส่งให้ Dispatcher
3.  **Flow 2: การบัญชาการตามเจตนา (Intent-based Delegation):** `Dispatcher` ใช้ `intent_to_agent_map` เพื่อมอบหมายภารกิจให้ Agent ที่เหมาะสมที่สุด พร้อมมอบเครื่องมือที่จำเป็น (เช่น RAG Engine เฉพาะทาง)
4.  **Flow 3: การจัดการผลลัพธ์และการสรุปผล (Outcome Management):** `Dispatcher` รับผลลัพธ์, ส่งต่อให้ `FormatterAgent` เพื่อขัดเกลาขั้นสุดท้าย, บันทึกความทรงจำ, และสร้าง `FinalResponse` กลับไปให้ผู้ใช้
5.  **Flow พิเศษ: ตาข่ายความปลอดภัย (Safety Net):** `try...except` block ใน Dispatcher จะดักจับข้อผิดพลาดร้ายแรงและเรียกใช้ `ApologyAgent` เพื่อจัดการสถานการณ์อย่างนุ่มนวล

---

## 🛠️ เทคโนโลยีที่ใช้ (Tech Stack)

*   **Backend:** FastAPI, Uvicorn
*   **AI & LLM:** Google Generative AI SDK (Gemini), Groq SDK (Llama 3)
*   **Data Science & RAG:** Sentence-Transformers, FAISS, Newspaper3k, Rapidfuzz
*   **Databases:** Neo4j (Graph Database), SQLite (Memory & Caching)
*   **Services:** Google AI Platform, GroqCloud
*   **Development:** Python 3.12+, Git, venv

---

## 🚀 เริ่มต้นใช้งาน (Getting Started)

### สิ่งที่ต้องมี (Prerequisites)
*   Python 3.12+
*   Git
*   ฐานข้อมูล Neo4j ที่กำลังทำงานอยู่

### การติดตั้ง (Installation)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Mike0165115321/PROJECT-NEXUS.git
    cd PROJECT-NEXUS
    ```

2.  **สร้างและเปิดใช้งาน Virtual Environment:**
    ```bash
    python -m venv .venvs
    source .venvs/bin/activate
    ```

3.  **ติดตั้ง Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **ตั้งค่า Environment Variables:**
    *   สร้างไฟล์ `.env` และเพิ่มข้อมูลลับของคุณ:
    ```env
    # Google Gemini API Keys (ใส่เป็น list คั่นด้วย comma)
    GOOGLE_API_KEYS=your_gemini_key_1,your_gemini_key_2
    # Groq API Keys (ใส่เป็น list คั่นด้วย comma)
    GROQ_API_KEYS=your_groq_key_1,your_groq_key_2
    # Neo4j Database Credentials
    NEO4J_URI="bolt://localhost:7687"
    NEO4J_USER="neo4j"
    NEO4J_PASSWORD="your_neo4j_password"
    # Unsplash API Key
    UNSPLASH_ACCESS_KEY="your_unsplash_key"
    ```

5.  **เตรียมข้อมูลและสร้าง Index (สำคัญ):**
    *   รันสคริปต์ ETL ตามลำดับเพื่อสร้างคลังความรู้:
    ```bash
    python knowledge_extractor_gemini.py
    python manage_data.py
    python manage_kg_data.py
    python manage_news.py
    ```

6.  **รันแอปพลิเคชัน:**
    ```bash
    uvicorn main:app --reload
    ```
    *   เข้าใช้งานที่ `http://127.0.0.1:8000`
    *   ดูเอกสาร API ที่ `http://127.0.0.1:8000/docs`

---

## 🛤️ การเดินทาง: จาก "โปรแกรม" สู่ "สหายทางปัญญา"

PROJECT NEXUS ไม่ได้เกิดขึ้นในชั่วข้ามคืน แต่ผ่านการเดินทาง 3 ช่วงสำคัญที่หล่อหลอมให้มันเป็นอย่างทุกวันนี้:
1.  **การแก้ไขวิกฤตและสร้างรากฐาน:** เริ่มต้นจากการเป็น "นักสืบ" แก้ปัญหาที่ซ่อนอยู่ลึกๆ จนได้มาซึ่ง "วินัย" และรากฐานทางเทคนิคที่แข็งแกร่ง
2.  **การปฏิวัติสถาปัตยกรรม AI:** "ยกเครื่อง" ระบบครั้งใหญ่ จาก Agent ตัวเดียวสู่ "Mixture of Experts", เปลี่ยนศูนย์กลางไปที่ "Dispatcher", และผสมผสานขุมพลังจาก "Mixture of Models" (Gemini + Groq)
3.  **การหลอมรวม "จิตวิญญาณ" และ "เครื่องยนต์":** สร้าง "จิตวิญญาณ" ให้กับ "เฟิง" ผ่าน `persona_core.py`, ออกแบบ `FengAgent` ให้เป็น "หน่วยคัดกรองอัจฉริยะ", และสร้าง `Unified RAG Engine Architecture` เพื่อมอบเครื่องมือค้นหาที่ทรงพลังที่สุดให้แก่ Agent ทุกตัว

ผลลัพธ์คือระบบนิเวศ AI ที่มีทั้ง "สมองส่วนหน้า" (Dispatcher), "ทีมผู้เชี่ยวชาญ" (Agents), "ขุมพลัง" (Models), "ความทรงจำ" (RAG Engines), และ "หัวใจ" (Persona) ที่ทำให้มันเป็นมากกว่าโปรแกรม

---
<br>

<!-- ENGLISH VERSION -->
# 🧠 PROJECT NEXUS: The Unified Engine Architecture (English Version)

> An **"Intellectual Companion"** built on a sophisticated and powerful **Hybrid Architecture**. It features a **Dispatcher** as the "orchestra conductor" for a **"Mixture of Experts"** team, powered by a **"Mixture of Models"**. All decisions are driven by **Chain of Thought** logic and advanced reasoning from **Advanced RAG** and a **Unified RAG Engine Architecture**, all served through a modern, flexible, and scalable **API-Driven** architecture.

<div align="right">
  <a href="#-project-nexus-the-unified-engine-architecture"><strong>เวอร์ชั่นภาษาไทย</strong></a>
</div>

**PROJECT NEXUS** is not just a chatbot; it is a **"living AI ecosystem"** that has evolved from a simple program into a "companion" ready to reflect and research alongside its user. This project doesn't rely on a single architecture but is a **"Layered Architectural Blend"** where multiple systems work in concert to create an AI that is versatile, deeply contextual, and maintains a consistent personality under the persona of "Feng."

## 🏛️ Core Architecture: Three Layers of Intelligence

Project Nexus is built on three perfectly integrated architectural layers:

### 1. The AI & Decision-Making Layer
*   **The Heart - Dispatcher-Centric Mixture of Experts (MoE):** The `Dispatcher` acts as the "orchestra conductor," receiving a "work file" from the `FengAgent` (triage unit) and assigning the mission to the most suitable specialist "Agent," enabling complex, systematic decision-making.
*   **The Powerhouse - Hybrid Model Strategy:** Strategically combines the strengths of various models:
    *   **Google Gemini 1.5 Flash:** For tasks requiring "quality and depth" (planning, counseling, final formatting).
    *   **Groq (Llama 3 70B & 8B):** For tasks demanding a "balance of speed and intelligence" (conversation, news summary, coding).
*   **The Backbone - Advanced & Unified RAG:**
    *   **Plan-Retrieve-Synthesize:** A 3-step deep knowledge retrieval process used by the `PlannerAgent` to generate high-quality analysis.
    *   **Unified RAG Engine Architecture:** A "data arsenal" with three specialized engines (Book, KG, News) for maximum precision.

### 2. The Application & Service Layer
*   **Service-Oriented & API-Driven:** `main.py` (FastAPI) serves as the central API Gateway, completely decoupling the backend and frontend, ready for future expansion into microservices.
*   **Client-Server Architecture:** `web/` acts as the client, sending requests to the `main.py` processing server.

### 3. The Data & Software Layer
*   **ETL Pipelines:** A dedicated "data factory" of separate scripts (`manage_*.py`, `knowledge_extractor_*.py`) for building and maintaining the entire knowledge base.
*   **Modular Architecture & Dependency Injection:** The project is structured into modules (core, agents, data), utilizing Dependency Injection in `main.py` for clean, testable, and maintainable code.

---

## 🌊 Logic Flow: From Query to Wisdom

The entire workflow is elegantly orchestrated by `dispatcher.py`:

1.  **Flow 0: Continuing Mission:** The system remembers "offers" for deep-dive analysis and can resume the task seamlessly when the user agrees, enabling smooth multi-turn conversations.
2.  **Flow 1: Intelligent Triage:** The `FengAgent` acts as the gateway, providing instant answers via a whitelist and using an LLM to classify the intent of complex queries before creating a "work file" for the Dispatcher.
3.  **Flow 2: Intent-based Delegation:** The `Dispatcher` uses an `intent_to_agent_map` to delegate the task to the most appropriate Agent, equipping it with the necessary specialized tools (e.g., a specific RAG Engine).
4.  **Flow 3: Outcome Management:** The `Dispatcher` receives the result, passes it to the `FormatterAgent` for final polishing, saves the memory, and constructs the `FinalResponse` for the user.
5.  **Special Flow: Safety Net:** A `try...except` block in the Dispatcher catches critical errors and calls the `ApologyAgent` to handle the situation gracefully.

---

## 🛠️ Tech Stack

*   **Backend:** FastAPI, Uvicorn
*   **AI & LLM:** Google Generative AI SDK (Gemini), Groq SDK (Llama 3)
*   **Data Science & RAG:** Sentence-Transformers, FAISS, Newspaper3k, Rapidfuzz
*   **Databases:** Neo4j (Graph Database), SQLite (Memory & Caching)
*   **Services:** Google AI Platform, GroqCloud
*   **Development:** Python 3.12+, Git, venv

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.12+
*   Git
*   A running instance of a Neo4j database

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Mike0165115321/PROJECT-NEXUS.git
    cd PROJECT-NEXUS
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venvs
    source .venvs/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    *   Create a `.env` file and add your credentials:
    ```env
    # Google Gemini API Keys (as a comma-separated list)
    GOOGLE_API_KEYS=your_gemini_key_1,your_gemini_key_2
    # Groq API Keys (as a comma-separated list)
    GROQ_API_KEYS=your_groq_key_1,your_groq_key_2
    # Neo4j Database Credentials
    NEO4J_URI="bolt://localhost:7687"
    NEO4J_USER="neo4j"
    NEO4J_PASSWORD="your_neo4j_password"
    # Unsplash API Key
    UNSPLASH_ACCESS_KEY="your_unsplash_key"
    ```

5.  **Prepare data and build indices (Crucial Step):**
    *   Run the ETL scripts in sequence to build the knowledge base:
    ```bash
    python knowledge_extractor_gemini.py
    python manage_data.py
    python manage_kg_data.py
    python manage_news.py
    ```

6.  **Run the application:**
    ```bash
    uvicorn main:app --reload
    ```
    *   Access the app at `http://127.0.0.1:8000`
    *   View the API docs at `http://127.0.0.1:8000/docs`

---

## 🛤️ The Journey: From Program to Intellectual Companion

PROJECT NEXUS wasn't built overnight. It was forged through a three-stage journey that shaped its very essence:
1.  **Crisis & Foundation:** It began with "detective work" to solve deep, hidden bugs, which instilled the "discipline" and strong technical foundation the project stands on today.
2.  **The AI Architectural Revolution:** A major overhaul that transformed the system from a single agent to a "Mixture of Experts," shifted the core logic to be "Dispatcher-centric," and created a powerful "Mixture of Models" (Gemini + Groq).
3.  **Fusing the Soul & The Engine:** The final stage involved breathing "soul" into the "Feng" persona via `persona_core.py`, designing the `FengAgent` as an intelligent gateway, and engineering the `Unified RAG Engine Architecture` to arm every agent with the most powerful tools.

The result is an AI ecosystem with a "prefrontal cortex" (Dispatcher), a "team of specialists" (Agents), a "hybrid powerhouse" (Models), a vast "memory" (RAG Engines), and most importantly, a "heart" (Persona) that makes it more than just a program.

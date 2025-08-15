# 🧠 PROJECT NEXUS: The Unified Engine Architecture

> An "Intellectual Companion" powered by a "Mixture of Experts & Models" architecture, orchestrated by a central "Dispatcher." It leverages "Advanced RAG" and "KG-RAG" for reasoning, all built upon a modern, scalable "Service-Oriented" architecture.

[![Python Version](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

**PROJECT NEXUS** is a living AI ecosystem designed to be a "companion" that is ready to reflect and research alongside the user. This project doesn't rely on a single architecture but is a **"Layered Architectural Blend"** where multiple systems work in concert to create an AI that is versatile, deeply contextual, and maintains a consistent personality.

## ✨ Core Features

*   **Dispatcher-Centric MoE:** A Dispatcher acts as an "orchestra conductor," directing a "team of specialists" (Agents) with specific responsibilities, enabling complex and systematic decision-making.
*   **Hybrid Model Strategy:** Strategically combines the strengths of various models, including **Google Gemini 1.5 Flash** for tasks requiring depth and **Groq (Llama 3)** for tasks demanding speed and balance.
*   **Advanced RAG (Plan-Retrieve-Synthesize):** A sophisticated 3-step information retrieval process that goes beyond standard RAG to produce high-quality analytical responses.
*   **Unified RAG Engine Architecture:** A partitioned data retrieval system with dedicated engines for different knowledge sources (books, Knowledge Graph, news), ensuring maximum precision and efficiency.
*   **Service-Oriented & API-Driven:** Built on FastAPI with a clean separation between backend and frontend, ready for future expansion into microservices.

---

## 🏛️ Core Architecture

Project Nexus is built on three interconnected architectural layers:

### 1. AI & Decision-Making Architecture
*   **Dispatcher-Centric Mixture of Experts (MoE):** The Dispatcher is the system's heart, receiving a "work file" from the FengAgent (triage unit) and assigning the mission to the most suitable Agent.
*   **Hybrid Model Strategy:** Uses Gemini 1.5 Flash for high-quality tasks (planning, counseling) and Groq (Llama 3 70B & 8B) for speed-sensitive tasks (conversation, news summary, coding).
*   **Advanced & Unified RAG:** Employs the Plan-Retrieve-Synthesize technique for in-depth research and features dedicated RAG engines for each data type (Book, KG, News).

### 2. Application & Service Architecture
*   **Service-Oriented & API-Driven:** `main.py` (FastAPI) serves as the API Gateway, completely decoupling the backend and frontend.
*   **Client-Server Architecture:** `web/` acts as the client, sending requests to the `main.py` processing server.

### 3. Data & Software Architecture
*   **ETL Pipelines:** Separate scripts (`manage_*.py`, `knowledge_extractor_*.py`) for building and maintaining the entire knowledge base.
*   **Modular Architecture & Dependency Injection:** The project is structured into modules (core, agents, data), utilizing Dependency Injection in `main.py` for clean, testable code.

---

## 🌊 How It Works (Data Flow)

The entire process is orchestrated by `dispatcher.py`. When a user query is received:

1.  **Intelligent Triage:**
    *   The `FengAgent` acts as the first line of response.
    *   It checks against a whitelist for quick, predefined answers.
    *   For complex queries, it uses an LLM to correct typos, classify user intent, and extract keywords.
    *   It creates a "work file" and sends it to the Dispatcher.

2.  **Intent-based Delegation:**
    *   The `Dispatcher` receives the "work file" and uses an `intent_to_agent_map` to identify the appropriate specialist Agent.
    *   It delegates the task to the correct Agent (e.g., `PlannerAgent`, `NewsAgent`, `CounselorAgent`) along with necessary tools (like a RAG Engine).

3.  **Outcome Management:**
    *   The `Dispatcher` receives the result from the executing Agent.
    *   If necessary, it forwards the result to the `FormatterAgent` to translate, format with Markdown, and align with the "Feng" persona.
    *   The conversation is saved via the `MemoryManager`.
    *   A `FinalResponse` object is created and sent back to the frontend for display.

---

## 🚀 Getting Started

Follow these steps to set up and run the project in your local environment.

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
    python3 -m venv .venvs
    source .venvs/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    *   Copy the `.env.example` file (if available) or create a new file named `.env`.
    *   Add your secret credentials to the `.env` file:
    ```env
    # Google Gemini API Keys (as a comma-separated list)
    GOOGLE_API_KEYS=your_gemini_key_1,your_gemini_key_2

    # Groq API Keys (as a comma-separated list)
    GROQ_API_KEYS=your_groq_key_1,your_groq_key_2

    # Neo4j Database Credentials
    NEO4J_URI="bolt://localhost:7687"
    NEO4J_USER="neo4j"
    NEO4J_PASSWORD="your_neo4j_password"

    # Unsplash API Key (for ImageAgent)
    UNSPLASH_ACCESS_KEY="your_unsplash_key"
    ```

5.  **Prepare data and build indices:**
    *   (Optional but Recommended) Run the ETL scripts in sequence to build the knowledge base:
    ```bash
    # 1. Extract Knowledge Graph from books (can be time-consuming)
    python3 knowledge_extractor_gemini.py

    # 2. Create the vector index for books
    python3 manage_data.py

    # 3. Create the vector index for the Knowledge Graph
    python3 manage_kg_data.py

    # 4. Fetch and create the vector index for news
    python3 manage_news.py
    ```

6.  **Run the application:**
    ```bash
    uvicorn main:app --reload
    ```
    The server will be running at `http://127.0.0.1:8000`.

---

## 🛠️ Usage

*   **Main Web Interface:** Open your browser and navigate to `http://127.0.0.1:8000`.
*   **API Documentation:** FastAPI automatically generates interactive API documentation at `http://127.0.0.1:8000/docs`.

---

## 🗺️ Project Structure
PROJECT_NEXUS/
│
├── .venvs/ # 📦 Python virtual environment
│
├── agents/ # 🧠 The Agency: A collection of specialists (Agents) with single responsibilities
│ ├── persona_core.py # 🆔 "Feng" Persona: The core personality DNA prompt
│ ├── formatter_agent.py # 🎨 The Editor: Refines language, formats, and ensures persona consistency
│ ├── coder_mode/ # - Faction: The Coders Guild
│ ├── consultant_mode/ # - Faction: The Librarians
│ ├── counseling_mode/ # - Faction: The Empathic Counselors
│ ├── feng_mode/ # - Faction: The Core Identity & Triage
│ ├── news_mode/ # - Faction: The Journalists
│ ├── planning_mode/ # - Faction: The Architects
│ ├── storytelling_mode/ # - Faction: The Listeners
│ └── utility_mode/ # - Faction: The Support Crew
│
├── core/ # ⚙️ The Engine Room: Core mechanics and shared tools
│ ├── api_key_manager.py # 🔑 Manages Gemini API Keys
│ ├── groq_key_manager.py # 🔑 Manages Groq API Keys
│ ├── config.py # 📜 Main Control Panel: Loads settings from .env
│ ├── dispatcher.py # 🚦 The Conductor: The heart of the system
│ ├── graph_manager.py # 🕸️ Neo4j Graph Manager
│ ├── memory_manager.py # 🧠 Short-term memory management
│ ├── rag_engine.py # 🔍 Book RAG Engine
│ ├── kg_rag_engine.py # 💡 Intuition RAG Engine (KG-RAG)
│ └── news_rag_engine.py # 📡 Intelligence RAG Engine (News)
│
├── data/ # 📦 The Vault: Persistent data storage
│ ├── books/ # 📚 Bookshelf (raw data)
│ ├── index/ # 📇 Book Index Cabinet (FAISS)
│ ├── graph_index/ # 🌐 Intuition Index Cabinet (FAISS)
│ ├── news_index/ # 📰 News Index (FAISS)
│ └── memory.db # 💾 Memory Database (SQLite)
│
├── neo4j-data/ # 🧠 Knowledge Graph Brain (Neo4j data)
├── sandbox_workspace/ # 🔬 Safe laboratory for the CodeInterpreterAgent
│
├── web/ # 🎨 Frontend (HTML, CSS, JS)
│
├── .env # 🤫 The Safe: Secret credentials (ignored by Git)
├── .gitignore # 🙈 The Ignore List: Specifies files and folders for Git to ignore
│
├── main.py # ▶️ The Start Button: FastAPI application entry point
├── knowledge_extractor_gemini.py # 🏭 Knowledge Extraction Factory (ETL)
├── manage_data.py # 🛠️ Book Data Management Tool (ETL)
├── manage_kg_data.py # 🛠️ Graph Data Management Tool (ETL)
├── manage_news.py # 🛠️ News Management Tool (ETL)
└── requirements.txt # 📜 Installation Blueprint (Dependencies)





# 🧠 PROJECT NEXUS: The Unified Engine Architecture

> "สหายทางปัญญา" (Intellectual Companion) ที่ขับเคลื่อนด้วยสถาปัตยกรรม "Mixture of Experts & Models" ซึ่งถูกบัญชาการโดย "Dispatcher" กลาง, มีความสามารถในการใช้ "Advanced RAG" และ "KG-RAG" ในการให้เหตุผล, และถูกสร้างขึ้นบนสถาปัตยกรรม "Service-Oriented" ที่ทันสมัยและพร้อมสำหรับการขยายขนาด

[![Python Version](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

**PROJECT NEXUS** คือระบบนิเวศ AI ที่มีชีวิต ซึ่งถูกออกแบบให้เป็น "สหาย" ที่พร้อมจะร่วมไตร่ตรองและค้นคว้าไปกับผู้ใช้ โปรเจกต์นี้ไม่ได้ใช้สถาปัตยกรรมเพียงหนึ่งเดียว แต่เป็นการ **"หลอมรวมสถาปัตยกรรมหลายชั้น" (Layered Architectural Blend)** ที่ทำงานร่วมกันอย่างเป็นระบบ เพื่อสร้าง AI ที่มีความสามารถหลากหลาย, เข้าใจบริบทเชิงลึก, และมีบุคลิกภาพที่สอดคล้องกัน

## ✨ คุณสมบัติหลัก (Core Features)

*   **Dispatcher-Centric MoE:** ใช้ Dispatcher เป็น "ผู้ควบคุมวงออร์เคสตรา" ในการบัญชาการ "ทีมผู้เชี่ยวชาญ" (Agents) ที่มีความสามารถเฉพาะทาง ทำให้การตัดสินใจซับซ้อนและเป็นระบบ
*   **Hybrid Model Strategy:** ผสมผสานจุดแข็งของโมเดลจากหลายสังกัดอย่างมีกลยุทธ์ ทั้ง **Google Gemini 1.5 Flash** สำหรับงานที่ต้องการความลึกซึ้ง และ **Groq (Llama 3)** สำหรับงานที่ต้องการความเร็วและความสมดุล
*   **Advanced RAG (Plan-Retrieve-Synthesize):** กระบวนการค้นหาความรู้เชิงลึกแบบ 3 ขั้นตอนที่ซับซ้อนกว่า RAG ทั่วไป เพื่อสร้างบทวิเคราะห์ที่มีคุณภาพ
*   **Unified RAG Engine Architecture:** สถาปัตยกรรมคลังข้อมูลแบบแยกส่วน (หนังสือ, Knowledge Graph, ข่าว) เพื่อความแม่นยำและประสิทธิภาพสูงสุดในการค้นหา
*   **Service-Oriented & API-Driven:** ออกแบบบน FastAPI โดยแยกส่วน Backend และ Frontend อย่างสมบูรณ์ พร้อมสำหรับการขยายขนาดเป็น Microservices ในอนาคต

---

## 🏛️ สถาปัตยกรรมหลัก (Core Architecture)

Project Nexus ถูกสร้างขึ้นบนสถาปัตยกรรม 3 ระดับที่ทำงานร่วมกัน:

### 1. สถาปัตยกรรมระดับ AI และการตัดสินใจ (AI & Decision-Making)
*   **Dispatcher-Centric Mixture of Experts (MoE):** Dispatcher เป็นหัวใจของระบบ ทำหน้าที่รับ "แฟ้มงาน" จาก FengAgent (หน่วยคัดกรอง) และมอบหมายภารกิจให้ Agent ที่เหมาะสมที่สุด
*   **Hybrid Model Strategy:** ใช้ Gemini 1.5 Flash สำหรับงานคุณภาพสูง (การวางแผน, ให้คำปรึกษา) และใช้ Groq (Llama 3 70B & 8B) สำหรับงานที่ต้องการความเร็ว (การสนทนา, สรุปข่าว, เขียนโค้ด)
*   **Advanced & Unified RAG:** ใช้เทคนิค Plan-Retrieve-Synthesize สำหรับการค้นคว้าเชิงลึก และมี RAG Engine แยกเฉพาะสำหรับข้อมูลแต่ละประเภท (หนังสือ, KG, ข่าว)

### 2. สถาปัตยกรรมระดับแอปพลิเคชันและบริการ (Application & Service)
*   **Service-Oriented & API-Driven:** `main.py` (FastAPI) ทำหน้าที่เป็น API Gateway ทำให้ Backend และ Frontend แยกจากกันอย่างสมบูรณ์
*   **Client-Server Architecture:** `web/` ทำหน้าที่เป็น Client ที่ส่ง Request ไปยัง `main.py` ซึ่งเป็น Server ประมวลผล

### 3. สถาปัตยกรรมระดับข้อมูลและซอฟต์แวร์ (Data & Software)
*   **ETL Pipelines:** มีสคริปต์แยกต่างหาก (`manage_*.py`, `knowledge_extractor_*.py`) สำหรับการสร้างและบำรุงรักษาคลังความรู้ทั้งหมด
*   **Modular Architecture & Dependency Injection:** โครงสร้างโปรเจกต์ถูกแบ่งเป็นโมดูล (core, agents, data) และใช้หลักการ Dependency Injection ใน `main.py` เพื่อโค้ดที่สะอาดและทดสอบง่าย

---

## 🌊 การไหลของข้อมูล (How It Works)

กระบวนการทำงานทั้งหมดถูกควบคุมโดย `dispatcher.py` เมื่อผู้ใช้ส่งคำถามเข้ามา:

1.  **การคัดกรองอัจฉริยะ (Intelligent Triage):**
    *   `FengAgent` รับคำถามเข้ามาเป็นด่านแรก
    *   ตรวจสอบกับ Whitelist เพื่อตอบคำถามง่ายๆ ทันที
    *   หากซับซ้อน จะใช้ LLM เพื่อแก้ไขคำผิด, วิเคราะห์เจตนา (Intent), และสกัด Keyword
    *   สร้าง "แฟ้มงาน" แล้วส่งให้ Dispatcher

2.  **การบัญชาการตามเจตนา (Intent-based Delegation):**
    *   `Dispatcher` รับ "แฟ้มงาน" และใช้ `intent_to_agent_map` เพื่อหา Agent ที่เหมาะสม
    *   จ่ายงานให้ Agent ผู้เชี่ยวชาญ (เช่น `PlannerAgent`, `NewsAgent`, `CounselorAgent`) พร้อมเครื่องมือที่จำเป็น (เช่น RAG Engine)

3.  **การจัดการผลลัพธ์และการสรุปผล (Outcome Management):**
    *   `Dispatcher` รับผลลัพธ์จาก Agent
    *   หากจำเป็น จะส่งต่อให้ `FormatterAgent` เพื่อแปล, จัดรูปแบบ Markdown, และปรับให้ตรงตามบุคลิกของ "เฟิง"
    *   บันทึกการสนทนาลงใน `MemoryManager`
    *   สร้าง `FinalResponse` ส่งกลับไปให้ Frontend เพื่อแสดงผล

---

## 🚀 เริ่มต้นใช้งาน (Getting Started)

ทำตามขั้นตอนต่อไปนี้เพื่อตั้งค่าและรันโปรเจกต์บนสภาพแวดล้อมของคุณ

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
    python3 -m venv .venvs
    source .venvs/bin/activate
    ```

3.  **ติดตั้ง Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **ตั้งค่า Environment Variables:**
    *   คัดลอกไฟล์ `.env.example` (ถ้ามี) หรือสร้างไฟล์ใหม่ชื่อ `.env`
    *   เพิ่มข้อมูลลับของคุณลงในไฟล์ `.env`:
    ```env
    # Google Gemini API Keys (ใส่เป็น list คั่นด้วย comma)
    GOOGLE_API_KEYS=your_gemini_key_1,your_gemini_key_2

    # Groq API Keys (ใส่เป็น list คั่นด้วย comma)
    GROQ_API_KEYS=your_groq_key_1,your_groq_key_2

    # Neo4j Database Credentials
    NEO4J_URI="bolt://localhost:7687"
    NEO4J_USER="neo4j"
    NEO4J_PASSWORD="your_neo4j_password"

    # Unsplash API Key (สำหรับ ImageAgent)
    UNSPLASH_ACCESS_KEY="your_unsplash_key"
    ```

5.  **เตรียมข้อมูลและสร้าง Index:**
    *   (แนะนำ) รันสคริปต์ ETL ตามลำดับเพื่อสร้างคลังความรู้:
    ```bash
    # 1. สกัด Knowledge Graph จากหนังสือ (อาจใช้เวลานาน)
    python3 knowledge_extractor_gemini.py

    # 2. สร้าง Vector Index สำหรับหนังสือ
    python3 manage_data.py

    # 3. สร้าง Vector Index สำหรับ Knowledge Graph
    python3 manage_kg_data.py

    # 4. ดึงข้อมูลและสร้าง Vector Index สำหรับข่าว
    python3 manage_news.py
    ```

6.  **รันแอปพลิเคชัน:**
    ```bash
    uvicorn main:app --reload
    ```
    เซิร์ฟเวอร์จะทำงานที่ `http://127.0.0.1:8000`

---

## 🛠️ การใช้งาน (Usage)

*   **หน้าเว็บหลัก:** เปิดเบราว์เซอร์แล้วไปที่ `http://127.0.0.1:8000`
*   **เอกสาร API:** FastAPI จะสร้างเอกสาร API แบบโต้ตอบให้โดยอัตโนมัติที่ `http://127.0.0.1:8000/docs`

---

## 🗺️ โครงสร้างโปรเจกต์ (Project Structure)
PROJECT_NEXUS/
│
├── .venvs/ # 📦 สภาพแวดล้อมเสมือนของ Python
│
├── agents/ # 🧠 ศูนย์บัญชาการของผู้เชี่ยวชาญ (Agents) ที่มีหน้าที่รับผิดชอบเพียงหนึ่งเดียว
│ ├── persona_core.py # 🆔 บัตรประจำตัว "เฟิง": เก็บ Prompt บุคลิกภาพหลัก (DNA)
│ ├── formatter_agent.py # 🎨 บรรณาธิการใหญ่: ขัดเกลาภาษา, จัดรูปแบบ, และตรวจสอบบุคลิก
│ ├── coder_mode/ # - Faction: The Coders Guild
│ ├── consultant_mode/ # - Faction: The Librarians
│ ├── counseling_mode/ # - Faction: The Empathic Counselors
│ ├── feng_mode/ # - Faction: The Core Identity & Triage
│ ├── news_mode/ # - Faction: The Journalists
│ ├── planning_mode/ # - Faction: The Architects
│ ├── storytelling_mode/ # - Faction: The Listeners
│ └── utility_mode/ # - Faction: The Support Crew
│
├── core/ # ⚙️ ห้องเครื่องยนต์: กลไกหลักและเครื่องมือที่ใช้ร่วมกัน
│ ├── api_key_manager.py # 🔑 จัดการ API Key ของ Gemini
│ ├── groq_key_manager.py # 🔑 จัดการ API Key ของ Groq
│ ├── config.py # 📜 แผงควบคุมหลัก: โหลดค่าจาก .env
│ ├── dispatcher.py # 🚦 ผู้ควบคุมวงออร์เคสตรา: หัวใจของระบบ
│ ├── graph_manager.py # 🕸️ ผู้จัดการกราฟ Neo4j
│ ├── memory_manager.py # 🧠 จัดการความจำระยะสั้น
│ ├── rag_engine.py # 🔍 เครื่องมือค้นหาหนังสือ (Book RAG)
│ ├── kg_rag_engine.py # 💡 เครื่องมือค้นหาสัญชาตญาณ (KG-RAG)
│ └── news_rag_engine.py # 📡 เครื่องมือค้นหาข่าวกรอง (News RAG)
│
├── data/ # 📦 คลังข้อมูลถาวร
│ ├── books/ # 📚 ชั้นหนังสือ (ข้อมูลดิบ)
│ ├── index/ # 📇 ตู้ดัชนีหนังสือ (FAISS)
│ ├── graph_index/ # 🌐 ตู้ดัชนีสัญชาตญาณ (FAISS)
│ ├── news_index/ # 📰 ดัชนีข่าว (FAISS)
│ └── memory.db # 💾 ฐานข้อมูลความทรงจำ (SQLite)
│
├── neo4j-data/ # 🧠 สมองส่วน Knowledge Graph (Neo4j)
├── sandbox_workspace/ # 🔬 ห้องทดลองปลอดภัยสำหรับ CodeInterpreterAgent
│
├── web/ # 🎨 ส่วนหน้าบ้าน (Frontend - HTML, CSS, JS)
│
├── .env # 🤫 ตู้นิรภัย (ข้อมูลลับ, ignored by Git)
├── .gitignore # 🙈 รายการสิ่งที่ Git จะไม่สนใจ
│
├── main.py # ▶️ ปุ่มสตาร์ท: จุดเริ่มต้นของแอปพลิเคชัน FastAPI
├── knowledge_extractor_gemini.py # 🏭 โรงงานสกัดความรู้ (ETL)
├── manage_data.py # 🛠️ เครื่องมือจัดการข้อมูลหนังสือ (ETL)
├── manage_kg_data.py # 🛠️ เครื่องมือจัดการข้อมูลกราฟ (ETL)
├── manage_news.py # 🛠️ เครื่องมือจัดการข่าว (ETL)
└── requirements.txt # 📜 พิมพ์เขียวการติดตั้ง (Dependencies)



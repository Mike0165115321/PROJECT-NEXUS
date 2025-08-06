# PROJECT NEXUS: สหายทางปัญญา (The Intellectual Companion)

**Project Nexus** คือระบบนิเวศ AI ที่ซับซ้อนและหลากหลาย ถูกออกแบบมาเพื่อเป็น "สหายทางปัญญา" อย่างแท้จริง มันไม่ใช่แค่แชทบอททั่วไป แต่เป็น "ทีมผู้เชี่ยวชาญ AI" ที่ทำงานร่วมกันอย่างเป็นระบบ โดยมีผู้บัญชาการกลาง (Dispatcher) คอยควบคุม เพื่อสร้างสรรค์คำตอบที่ลึกซึ้ง, เข้าใจบริบท, และมีเหตุผลประกอบอย่างสมบูรณ์

---

## ✨ คุณสมบัติเด่น (Key Features)

*   **สถาปัตยกรรม Mixture of Experts (MoE):** มี `Dispatcher` กลางคอยวิเคราะห์และจ่ายงานให้ Agent ที่เชี่ยวชาญที่สุดในแต่ละด้าน เช่น การเขียนโค้ด, การให้คำปรึกษา, การสรุปข่าว, หรือการสนทนาทั่วไป
*   **กลยุทธ์ Hybrid Model:** ผสมผสานความเร็วของ **Groq (Llama 3)** สำหรับการโต้ตอบที่ฉับไว เข้ากับความลุ่มลึกของ **Google Gemini** สำหรับการวิเคราะห์ที่ซับซ้อน
*   **ระบบความจำขั้นสูง:** ใช้เทคนิค **Advanced RAG** และ **KG-RAG** (Knowledge Graph-Augmented RAG) เพื่อค้นหาข้อมูลจากคลังความรู้ (หนังสือ) และกราฟความสัมพันธ์ ทำให้การตอบสนองมีมิติและสัญชาตญาณ
*   **โครงสร้างที่พร้อมขยายขนาด:** ออกแบบด้วย **FastAPI** ในสถาปัตยกรรมแบบ Modular และ Service-Oriented ทำให้ง่ายต่อการบำรุงรักษาและต่อยอดในอนาคต

---

## 🚀 การติดตั้งและเริ่มต้นใช้งาน (Getting Started)

ทำตามขั้นตอนต่อไปนี้เพื่อติดตั้งและรันโปรเจกต์บนเครื่องของคุณ

### 1. สิ่งที่ต้องมี (Prerequisites)

*   Python 3.11+
*   Git
*   ฐานข้อมูล [Neo4j](https://neo4j.com/download/) ที่กำลังทำงานอยู่ (สำหรับฟีเจอร์ Knowledge Graph)

### 2. การติดตั้ง (Installation)

1.  **Clone Repository:**
    ```sh
    git clone https://github.com/Mike0165115321/My_AI_PROJECT-NEXUS.git
    cd My_AI_PROJECT-NEXUS
    ```

2.  **สร้างและเปิดใช้งาน Virtual Environment:**
    ```sh
    # สำหรับ Windows
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

    # สำหรับ Linux/macOS (เช่นใน WSL)
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **ติดตั้ง Dependencies:**
    *   **สำหรับสภาพแวดล้อมที่ใช้ CPU เท่านั้น (แนะนำสำหรับเริ่มต้น):**
        ```sh
        pip install -r requirements-cpu.txt
        ```

4.  **ตั้งค่า Environment Variables:**
    *   สร้างไฟล์ชื่อ `.env` ขึ้นมาในโฟลเดอร์หลักของโปรเจกต์
    *   คัดลอกและวางเนื้อหาด้านล่างลงในไฟล์ `.env` แล้วแก้ไขค่าต่างๆ ให้ถูกต้อง:
        ```env
        # --- API Keys ---
        GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
        GROQ_API_KEY="YOUR_GROQ_API_KEY"
        
        # --- Neo4j Credentials ---
        NEO4J_URI="bolt://localhost:7687"
        NEO4J_USER="neo4j"
        NEO4J_PASSWORD="YOUR_NEO4J_PASSWORD"
        ```

### 3. การเตรียมข้อมูล (Data Preparation)

**สำคัญ:** Repository นี้ไม่มีข้อมูลเริ่มต้นมาให้ คุณต้องสร้างคลังความรู้ขึ้นเองโดยใช้สคริปต์ที่เตรียมไว้ให้

1.  **เตรียมข้อมูลหนังสือ:**
    *   นำไฟล์หนังสือของคุณ (แนะนำให้เป็นไฟล์ `.txt`) ไปวางไว้ในโฟลเดอร์ `data/books/` (ถ้ายังไม่มีโฟลเดอร์ `data` หรือ `books` ให้สร้างขึ้นมาก่อน)

2.  **สร้างดัชนีสำหรับ RAG (Vector Store):**
    *   รันสคริปต์เพื่อประมวลผลหนังสือและสร้าง Vector Index:
        ```sh
        python manage_data.py
        ```

3.  **สร้างฐานข้อมูล Knowledge Graph:**
    *   รันสคริปต์เพื่อสกัดข้อมูลความสัมพันธ์จากหนังสือและนำเข้าสู่ Neo4j:
        ```sh
        python knowledge_extractor.py
        ```

### 4. รันแอปพลิเคชัน (Run the Application)

*   เมื่อเตรียมข้อมูลเสร็จแล้ว ให้สตาร์ทเซิร์ฟเวอร์:
    ```sh
    python main.py
    ```
*   ระบบจะพร้อมใช้งานที่ `http://127.0.0.1:8000`
*   ดูเอกสาร API แบบโต้ตอบได้ที่ `http://127.0.0.1:8000/docs`

---

## 🗺️ โครงสร้างโปรเจกต์ (Project Structure)

```
PROJECT_NEXUS/
│
├── agents/             # 🧠 ศูนย์บัญชาการของผู้เชี่ยวชาญ (Agents) แต่ละด้าน
├── core/               # ⚙️ ห้องเครื่องยนต์และกลไกหลักของระบบ
├── data/               # 📦 คลังข้อมูล (ไฟล์นี้จะถูกสร้างขึ้นเมื่อรันสคริปต์)
├── web/                # 🎨 ส่วนหน้าบ้าน (Frontend)
│
├── .gitignore          # 🙈 รายการไฟล์ที่ Git จะไม่ติดตาม
├── main.py             # ▶️ ปุ่มสตาร์ท (FastAPI Server)
├── knowledge_extractor.py # 🏭 โรงงานสกัดความรู้สำหรับ Knowledge Graph
├── manage_data.py      # 🛠️ เครื่องมือจัดการข้อมูลสำหรับ RAG
├── manage_memory.py    # 🛠️ เครื่องมือจัดการความทรงจำ
├── manage_news.py      # 🛠️ เครื่องมือจัดการข่าว
└── requirements-cpu.txt # 📜 รายการไลบรารีสำหรับติดตั้ง (เวอร์ชัน CPU)
```

# PROJECT NEXUS: The Intellectual Companion

**Project Nexus** is a sophisticated, multi-faceted AI ecosystem designed to be a true intellectual companion. It's more than just a chatbot; it's a "team of AI experts" working in concert, orchestrated by a central dispatcher, to provide nuanced, context-aware, and deeply reasoned responses.

---

## ✨ Key Features

*   **Mixture of Experts (MoE) Architecture:** A central `Dispatcher` intelligently analyzes and delegates tasks to specialized AI Agents (e.g., coding, counseling, news summarization, general conversation).
*   **Hybrid Model Strategy:** Leverages the best of both worlds by combining the speed of **Groq (Llama 3)** for rapid interaction with the profound depth of **Google Gemini** for complex analysis.
*   **Advanced Memory System:** Utilizes **Advanced RAG** (Retrieval-Augmented Generation) and **KG-RAG** (Knowledge Graph-Augmented RAG) techniques to retrieve information from a knowledge base (books) and a graph database, enabling more insightful and intuitive responses.
*   **Scalable Architecture:** Built with **FastAPI** using a modular and service-oriented design, ensuring ease of maintenance and future scalability.

---

## 🚀 Getting Started

Follow these instructions to set up and run Project Nexus on your local machine for development and testing purposes.

### 1. Prerequisites

*   Python 3.11+
*   Git
*   A running [Neo4j](https://neo4j.com/download/) database instance (essential for Knowledge Graph features).

### 2. Installation

1.  **Clone the Repository:**
    ```sh
    git clone https://github.com/Mike0165115321/My_AI_PROJECT-NEXUS.git
    cd My_AI_PROJECT-NEXUS
    ```

2.  **Create and Activate a Virtual Environment:**
    ```sh
    # For Windows
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

    # For Linux/macOS (e.g., inside WSL)
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies:**
    *   **For a CPU-only environment (recommended for initial setup/Windows):**
        ```sh
        pip install -r requirements-cpu.txt
        ```
    *   *(If you intend to run with GPU, you will need to generate a `requirements-gpu.txt` file from your GPU-enabled Linux/WSL environment. This repository includes `requirements-cpu.txt` by default for broader compatibility.)*

4.  **Set up Environment Variables:**
    *   Create a file named `.env` in the root directory of the project.
    *   Copy and paste the content below into your `.env` file, replacing the placeholder values with your actual API keys and credentials:
        ```env
        # --- API Keys ---
        GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
        GROQ_API_KEY="YOUR_GROQ_API_KEY"
        
        # --- Neo4j Credentials ---
        NEO4J_URI="bolt://localhost:7687"
        NEO4J_USER="neo4j"
        NEO4J_PASSWORD="YOUR_NEO4J_PASSWORD"
        ```

### 3. Data Preparation

**IMPORTANT:** This repository does not include any initial data files (books, indexes, etc.) for size and privacy reasons. You must generate your knowledge base by following these steps:

1.  **Prepare Your Book Data:**
    *   Place your text files (e.g., `.txt` format) containing the knowledge you want Project Nexus to learn into the `data/books/` directory. If `data` or `data/books` folders don't exist, create them manually.

2.  **Generate RAG Index (Vector Store):**
    *   Run the script to process your book data and create a vector index for Retrieval-Augmented Generation:
        ```sh
        python manage_data.py
        ```
    *   This will populate `data/index/`, `data/memory_index/`, `data/news_index/`, and `data/memory.db`.

3.  **Build Knowledge Graph:**
    *   Ensure your Neo4j database is running.
    *   Run the script to extract relationships and knowledge from your data and import it into Neo4j:
        ```sh
        python knowledge_extractor.py
        ```

### 4. Run the Application

*   Once all data preparation steps are complete, start the FastAPI server:
    ```sh
    python main.py
    ```
*   The application will be accessible at `http://127.0.0.1:8000`.
*   You can explore the interactive API documentation at `http://127.0.0.1:8000/docs`.

---

## 🗺️ Project Structure

```
PROJECT_NEXUS/
│
├── agents/             # 🧠 The Agency: Hub of specialized AI Agents
├── core/               # ⚙️ The Engine Room: Core system mechanics
├── data/               # 📦 The Vault: Persistent data storage (generated after running scripts)
├── web/                # 🎨 The Frontend: User-facing web interface
│
├── .gitignore          # 🙈 Files/directories ignored by Git
├── main.py             # ▶️ Entry point: FastAPI server
├── knowledge_extractor.py # 🏭 Knowledge Graph ETL: Extracts and loads knowledge into Neo4j
├── manage_data.py      # 🛠️ Data Management Tool: ETL for RAG (builds vector stores)
├── manage_memory.py    # 🛠️ Memory Management Tool
├── manage_news.py      # 🛠️ News Management Tool
└── requirements-cpu.txt # 📜 Dependency List: Libraries required for CPU-only setup
```


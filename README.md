# PROJECT NEXUS: The Intellectual Companion

**Project Nexus** is a sophisticated, multi-faceted AI ecosystem designed to be a true intellectual companion. It's not just a chatbot; it's a team of specialized AI agents working in concert, orchestrated by a central dispatcher, to provide nuanced, context-aware, and deeply reasoned responses.

---

## 🏛️ Core Architecture

Project Nexus is built on a **Layered Architectural Blend**, combining several advanced concepts to create a robust and intelligent system.

1.  **AI & Decision-Making Architecture:**
    *   **Dispatcher-Centric Mixture of Experts (MoE):** The heart of the system. A central `Dispatcher` intelligently delegates tasks to the most suitable agent based on a sophisticated triage process.
    *   **Hybrid Model Strategy:** Leverages the best of both worlds by combining the speed of **Groq (Llama 3)** for real-time interaction and the depth of **Google's Gemini** for complex analysis.
    *   **Advanced RAG & KG-RAG:** Goes beyond simple retrieval by using a `Plan-Retrieve-Synthesize` model for deep research and augmenting responses with a **Knowledge Graph** for contextual understanding.

2.  **Application & Service Architecture:**
    *   **Service-Oriented & API-Driven:** Built with a clean, modular design using **FastAPI**, making the system scalable and easy to maintain.

---

## 🚀 Getting Started

Follow these instructions to get a local copy up and running for development and testing purposes.

### Prerequisites

*   Python 3.11+
*   Git
*   An active Neo4j database (for Knowledge Graph features)

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/Mike0165115321/My_AI_PROJECT-NEXUS.git
    cd My_AI_PROJECT-NEXUS
    ```

2.  **Create and activate a virtual environment:**
    ```sh
    # For Windows
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

    # For Linux/macOS
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the required dependencies:**
    *   **For CPU-only environment (e.g., on Windows):**
        ```sh
        pip install -r requirements-cpu.txt
        ```
    *   **For GPU-enabled environment (e.g., on Linux with NVIDIA GPU):**
        *(You will need to create a `requirements-gpu.txt` file from your WSL environment for this)*
        ```sh
        pip install -r requirements-gpu.txt
        ```

4.  **Set up your environment variables:**
    *   Create a file named `.env` in the root of the project.
    *   Add your API keys to this file:
        ```env
        GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
        GROQ_API_KEY="YOUR_GROQ_API_KEY"
        # Neo4j Credentials
        NEO4J_URI="bolt://localhost:7687"
        NEO4J_USER="neo4j"
        NEO4J_PASSWORD="YOUR_NEO4J_PASSWORD"
        ```

5.  **Run the application:**
    ```sh
    python main.py
    ```
    The server will be available at `http://127.0.0.1:8000`.

---

## 🛠️ Usage

*   Access the main interface at `http://127.0.0.1:8000`.
*   Explore the API documentation at `http://127.0.0.1:8000/docs`.
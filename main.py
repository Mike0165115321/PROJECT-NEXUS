# main.py
# (V47.0 - Fully Asynchronous & CORRECTED Non-Blocking Startup)
# --- Project Nexus AI Assistant Server ---

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import traceback
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer, CrossEncoder
import torch
import time
import asyncio # <-- [V30] (ถูกต้อง)
from datetime import datetime, timedelta

# --- ส่วนของ Core (V25-V47 Fix) ---
from core.config import settings
from core.dispatcher import Dispatcher, FinalResponse
from core.rag_engine import RAGEngine # (V32)
from core.memory_manager import MemoryManager # (V17)
from core.long_term_memory_manager import LongTermMemoryManager # (V34)
from core.api_key_manager import ApiKeyManager # (V25)
from core.graph_manager import GraphManager # (V2.1 - Sync OK!)
from core.groq_key_manager import GroqApiKeyManager # (V25)
from core.tts_engine import TextToSpeechEngine # (V33)
# --- ส่วนของ Agents (V11-V46) ---
from agents.planning_mode.planner_agent import PlannerAgent # (V9)
from agents.formatter_agent import FormatterAgent # (V10)
from agents.consultant_mode.librarian_agent import LibrarianAgent # (V43)
from agents.coder_mode.code_interpreter_agent import CodeInterpreterAgent # (V45)
from agents.utility_mode.reporter_agent import ReporterAgent
from agents.utility_mode.system_agent import SystemAgent # (V22)
from agents.utility_mode.image_agent import ImageAgent # (V36)
from agents.news_mode.news_agent import NewsAgent # (V11)
from agents.feng_mode.feng_agent import FengAgent # (V37)
from agents.counseling_mode.counselor_agent import CounselorAgent # (V14)
from agents.storytelling_mode.listener_agent import ListenerAgent # (V38)
from agents.apology_agent.apology_agent import ApologyAgent # (V46)
from agents.feng_mode.general_conversation_agent import GeneralConversationAgent # (V42)
from agents.feng_mode.proactive_offer_agent import ProactiveOfferAgent # (V41)
from agents.memory_mode.memory_agent import MemoryAgent # (V40)
from agents.persona_core import FENG_PERSONA_PROMPT
from agents.presenter.presenter_agent import PresenterAgent # (V39)


web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

AGENTS = {}
GRAPH_MANAGER: GraphManager = None
DISPATCHER: Dispatcher = None
audio_tasks = {}

# [V33] (ฟังก์ชัน create_audio_file_background "แข็งแรงดี")
async def create_audio_file_background(text: str, output_path: str, task_id: str):
    """[V33] ฟังก์ชันนี้จะถูกรันใน Background เพื่อสร้างไฟล์เสียง (แบบ Async)"""
    try:
        print(f"🎙️  Starting background audio synthesis for task: {task_id}")
        tts_agent = AGENTS.get("TTS")
        if tts_agent:
            voice_file_path = await tts_agent.synthesize(text, output_path)
            if voice_file_path:
                audio_tasks[task_id] = {"status": "done", "url": f"/static/audio/{os.path.basename(output_path)}"}
                print(f" 	- ✅ Audio task {task_id} completed.")
                return
        audio_tasks[task_id] = {"status": "failed", "error": "TTS agent not found or synthesis failed"}
    except Exception as e:
        print(f" 	- ❌ Background audio synthesis failed for task {task_id}: {e}")
        audio_tasks[task_id] = {"status": "failed", "error": str(e)}

# [V3.2] (ฟังก์ชัน cleanup_old_audio_files "แข็งแรงดี")
async def cleanup_old_audio_files():
    """Service ที่ทำงานเบื้องหลังเพื่อลบไฟล์เสียงเก่า"""
    audio_dir = os.path.join(web_dir, "static", "audio")
    cleanup_interval_seconds = 300  
    max_file_age_minutes = 5 	 
    
    while True:
        await asyncio.sleep(cleanup_interval_seconds)
        
        print("🧹 Running audio cleanup service...")
        try:
            if not os.path.exists(audio_dir):
                continue

            for filename in os.listdir(audio_dir):
                if filename.endswith(".mp3"):
                    file_path = os.path.join(audio_dir, filename)
                    try:
                        file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if datetime.now() - file_mod_time > timedelta(minutes=max_file_age_minutes):
                            print(f" 	- Deleting old audio file: {filename}")
                            os.remove(file_path)
                    except FileNotFoundError:
                        continue
        except Exception as e:
            print(f" 	- Error during audio cleanup: {e}")


# [CHANGED] "ผ่าตัดใหญ่ V47.0": Non-Blocking Startup (CORRECTED)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """[V47] "Lifespan" ที่ "ผ่าตัด" แล้ว (Non-Blocking Startup ที่ "ถูกต้อง")"""
    
    global DISPATCHER, GRAPH_MANAGER, AGENTS
    print("--- 🚀 Initializing Project Nexus Server (V47 - Async & Corrected) ---") # [CHANGED] 1. อัปเดตเวอร์ชัน
    try:
        # --- [STEP 1: สร้าง Key Managers (เร็ว) (V25)] ---
        google_key_manager = ApiKeyManager(all_google_keys=settings.GOOGLE_API_KEYS, silent=True)
        groq_key_manager = GroqApiKeyManager(all_groq_keys=settings.GROQ_API_KEYS, silent=True)
        
        # --- [STEP 2: สร้าง Models (FP16) (ช้า... แต่เดี๋ยว 'await' ทีหลัง)] ---
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"--- 🧠 Initializing Central Armory on {device.upper()} (Optimized FP16 Mode) ---")
        
        def _blocking_load_hf_models():
            embedder = SentenceTransformer("intfloat/multilingual-e5-large", device=device)
            reranker = CrossEncoder("BAAI/bge-reranker-base", device=device)
            if device == "cuda":
                print(" 	- ⚡️ Converting models to FP16 for CUDA acceleration...")
                embedder.half()
                reranker.model.half()
            print(" 	- ✅ Embedding and Reranking models (FP16) loaded.")
            return embedder, reranker
        
        hf_models_task = asyncio.create_task(asyncio.to_thread(_blocking_load_hf_models))

        # --- [STEP 3: สร้าง 'Core' Agents (เร็ว)] ---
        rag_engine_instance = RAGEngine(
            embedder=None, 
            reranker=None, 
        ) # (V32)
        memory_manager_instance = MemoryManager() # (V17)
        tts_engine_instance = TextToSpeechEngine() # (V33)
        ltm_manager_instance = LongTermMemoryManager( # (V34)
            embedding_model="intfloat/multilingual-e5-large",
            index_dir="data/memory_index"
        )
        
        # --- [STEP 4: สร้าง 'All Agents' (เร็ว)] ---
        # (นี่คือการ 'Inject' Dependencies (V9-V47 Fixes) ทั้งหมด)
        AGENTS = {
            "MEMORY": memory_manager_instance,
            "SYSTEM": SystemAgent(), # (V22)
            "REPORTER": ReporterAgent(),
            "IMAGE": ImageAgent( # (V36)
                unsplash_key=settings.UNSPLASH_ACCESS_KEY,
                key_manager=groq_key_manager,
                model_name=settings.IMAGE_AGENT_MODEL 
            ),
            "TTS": tts_engine_instance, # (V33)
            "APOLOGY": ApologyAgent( # (V46)
                key_manager=groq_key_manager,
                model_name=settings.APOLOGY_AGENT_MODEL,
                persona_prompt=FENG_PERSONA_PROMPT
            ),
            "MEMORY_QUERY": MemoryAgent( # (V40)
                key_manager=groq_key_manager, 
                model_name=settings.MEMORY_AGENT_MODEL, 
                memory_manager=memory_manager_instance, 
                persona_prompt=FENG_PERSONA_PROMPT 	
            ),
            "FENG": FengAgent( # (V37)
                key_manager=google_key_manager,
                model_name=settings.PRIMARY_GEMINI_MODEL,
                persona_prompt=FENG_PERSONA_PROMPT
            ),
            "GENERAL_HANDLER": GeneralConversationAgent( # (V42)
                key_manager=groq_key_manager,
                model_name=settings.FENG_PRIMARY_MODEL,
                rag_engine=rag_engine_instance,
                ltm_manager=ltm_manager_instance,
                persona_prompt=FENG_PERSONA_PROMPT
            ),
            "PROACTIVE_OFFER_HANDLER": ProactiveOfferAgent( # (V41)
                key_manager=groq_key_manager,
                model_name=settings.FENG_PRIMARY_MODEL,
                rag_engine=rag_engine_instance,
                persona_prompt=FENG_PERSONA_PROMPT
            ),
            "COUNSELOR": CounselorAgent( # (V14)
                key_manager=google_key_manager, 
                model_name=settings.COUNSELOR_AGENT_MODEL,
                persona_prompt=FENG_PERSONA_PROMPT
            ),
            "LISTENER": ListenerAgent( # (V38)
                key_manager=groq_key_manager,
                model_name=settings.LISTENER_AGENT_MODEL,
                persona_prompt=FENG_PERSONA_PROMPT
            ),
            "PLANNER": PlannerAgent( # (V9)
                key_manager=google_key_manager, 
                model_name=settings.PLANNER_AGENT_MODEL,
                rag_engine=rag_engine_instance,
                persona_prompt=FENG_PERSONA_PROMPT
            ),
            "CODER": CodeInterpreterAgent( # (V45)
                key_manager=groq_key_manager, 
                model_name=settings.CODE_AGENT_MODEL,
                persona_prompt=FENG_PERSONA_PROMPT
            ),
            "LIBRARIAN": LibrarianAgent( # (V43)
                key_manager=groq_key_manager, 
                model_name=settings.LIBRARIAN_AGENT_MODEL,
                rag_engine=rag_engine_instance,
                persona_prompt=FENG_PERSONA_PROMPT
            ),
            "NEWS": NewsAgent( # (V11)
                key_manager=google_key_manager, 
                model_name=settings.NEWS_AGENT_MODEL,
                rag_engine=rag_engine_instance,
                persona_prompt=FENG_PERSONA_PROMPT
            ),
            "FORMATTER": FormatterAgent( # (V10)
                key_manager=google_key_manager, 
                model_name=settings.FORMATTER_AGENT_MODEL,
                persona_prompt=FENG_PERSONA_PROMPT
            ),
            "PRESENTER": PresenterAgent( # (V39)
                key_manager=groq_key_manager,
                model_name=settings.SECONDARY_GROQ_MODEL, 
                persona_prompt=FENG_PERSONA_PROMPT
            )
        }

        # --- [STEP 5: "Await" ทุกอย่างที่ "ช้า" ให้เสร็จ "พร้อมกัน"] ---
        print("--- ⏳ Awaiting all non-blocking background loads... ---")
        
        # 5.1 "รอ" ให้ HF Models (FP16) โหลดเสร็จ
        embedder_instance, reranker_instance = await hf_models_task
        
        # 5.2 "Inject" Models ที่โหลดเสร็จแล้ว... กลับเข้าไปใน RAG Engine
        rag_engine_instance.embedder = embedder_instance
        rag_engine_instance.reranker = reranker_instance
        
        # 5.3 "ปลุก" Graph Manager (V2.1 - Sync)
        global GRAPH_MANAGER
        GRAPH_MANAGER = GraphManager() # (V2.1 init เร็ว)
        
        # [CHANGED V47.0] "ผ่าตัด" การเรียก 'gather'
        # (เรา "ไม่" เรียก 'GRAPH_MANAGER.verify_connection_async()' (V29)
        #  ...แต่เรา "ห่อ" 'GRAPH_MANAGER.verify_connectivity()' (V2.1)
        #  ...ด้วย 'asyncio.to_thread' แทน!)
        
        # 5.4 สร้าง "ฟังก์ชันห่อ" (Wrapper) สำหรับ 'verify_connectivity' (V2.1)
        def _blocking_verify_neo4j():
            if GRAPH_MANAGER and GRAPH_MANAGER.driver:
                try:
                    print("🔗 Graph Manager: Verifying Neo4j connectivity (Sync in Thread)...")
                    GRAPH_MANAGER.driver.verify_connectivity()
                    print("🔗 Graph Manager: Successfully connected to Neo4j.")
                except Exception as e:
                    print(f"❌ Graph Manager: Could not connect to Neo4j. Error: {e}")
                    GRAPH_MANAGER.driver = None # ปิดการใช้งาน
        
        # 5.5 สั่ง "โหลด" (Async) คลังข้อมูล + "Verify" DB "พร้อมกัน"
        await asyncio.gather(
            rag_engine_instance.load_models_and_index(),      # (V32 - OK)
            ltm_manager_instance.load_models_and_index(),   # (V34 - OK)
            asyncio.to_thread(_blocking_verify_neo4j)         # <-- [V47 FIX!]
        )
        
        # --- [STEP 6: สร้าง Dispatcher (เร็ว)] ---
        asyncio.create_task(cleanup_old_audio_files())
        DISPATCHER = Dispatcher(agents=AGENTS, key_manager=google_key_manager) # (V9)
        
        print("✅ All systems operational. Hybrid AI team is ready.")
    
    except Exception as e:
        print(f"❌ FATAL ERROR during startup: {e}")
        traceback.print_exc()
    
    yield
    
    print("--- 🌙 Server shutting down ---")
    if GRAPH_MANAGER:
        GRAPH_MANAGER.close()

app = FastAPI(
    title="Project Nexus AI Assistant",
    version="V47.0-AsyncFixed", # [CHANGED] อัปเดตเวอร์ชัน!
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory=os.path.join(web_dir, "static")), name="static")

class QueryRequest(BaseModel):
    query: str
    user_id: str = "default_user"

@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse(os.path.join(web_dir, 'index.html'))

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    print(f"🔗 WebSocket connection established for user: {user_id}")
    try:
        while True:
            query = await websocket.receive_text()
            
            async def send_update(data: dict):
                await websocket.send_json(data)

            if not DISPATCHER:
                await send_update({"type": "error", "payload": {"detail": "Server is initializing."}})
                continue
            
            try:
                await send_update({"type": "progress", "payload": {"status": "RECEIVED", "detail": "ได้รับคำสั่งแล้ว กำลังประมวลผล..."}})
                
                response_model = await DISPATCHER.handle_query(query, user_id, update_callback=send_update)
                
                if response_model.answer and not response_model.error:
                    timestamp = int(time.time())
                    filename = f"response_{user_id}_{timestamp}.mp3"
                    task_id = filename
                    
                    audio_dir = os.path.join(web_dir, "static", "audio")
                    os.makedirs(audio_dir, exist_ok=True)
                    output_path = os.path.join(audio_dir, filename)
                    
                    audio_tasks[task_id] = {"status": "processing"}
                    
                    asyncio.create_task(create_audio_file_background(response_model.answer, output_path, task_id)) # (V33 - OK)
                    
                    response_model.voice_task_id = task_id
                
                final_data = response_model.dict()
                await send_update({"type": "final_response", "payload": final_data})

            except Exception as e:
                print(f"❌ Error during WebSocket processing for user {user_id}: {e}")
                traceback.print_exc()
                await send_update({"type": "error", "payload": {"detail": "เกิดข้อผิดพลาดร้ายแรงระหว่างการประมวลผล"}})

    except WebSocketDisconnect:
        print(f"👋 WebSocket connection closed for user: {user_id}")
    except Exception as e:
        print(f"❌ Unhandled WebSocket error for user {user_id}: {e}")
        await websocket.close(code=1011)

@app.post("/ask", response_model=FinalResponse)
async def ask_assistant(request: QueryRequest, background_tasks: BackgroundTasks):
    if not DISPATCHER:
        raise HTTPException(status_code=503, detail="Server is still initializing or has failed.")
    try:
        response = await DISPATCHER.handle_query(request.query, request.user_id)

        if response.answer and not response.error:
            timestamp = int(time.time())
            filename = f"response_{request.user_id}_{timestamp}.mp3"
            task_id = filename
            
            audio_dir = os.path.join(web_dir, "static", "audio")
            os.makedirs(audio_dir, exist_ok=True)
            output_path = os.path.join(audio_dir, filename)
            
            audio_tasks[task_id] = {"status": "processing"}
            
            # [V33 FIX] (ถูกต้อง)
            asyncio.create_task(create_audio_file_background(response.answer, output_path, task_id))
            
            response.voice_task_id = task_id

        return response
        
    except Exception as e:
        print(f"❌ Unhandled error in /ask endpoint: {e}")
        traceback.print_exc()
        return FinalResponse(agent_used="FATAL_ERROR", answer="ขออภัยครับ เกิดข้อผิดพลาดร้ายแรง", error=True)

@app.get("/audio_status/{task_id}")
async def get_audio_status(task_id: str):
    task = audio_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] in ["done", "failed"]:
        return audio_tasks.pop(task_id) 
        
    return task

# [CHANGED V30/V47] "ผ่าตัด" Endpoint นี้ให้เป็น 'async'
@app.get("/api/graph/explore", tags=["Knowledge Graph"])
async def get_graph_data_for_visualization(entity: str, limit: int = 25):
    global GRAPH_MANAGER
    if not GRAPH_MANAGER:
        raise HTTPException(status_code=503, detail="Graph Manager is not available.")
    if not entity:
        return {"nodes": [], "edges": []}
    
    # (ฟังก์ชัน 'Blocking' ที่เราจะ 'await to_thread')
    def _blocking_graph_call():
        print(f"📈 Graph Endpoint: Executing 'find_related_concepts' (Sync) in Thread...")
        try:
            # (เรียก 'GraphManager' (V2.1) ที่ "บล็อก")
            return GRAPH_MANAGER.find_related_concepts(entity, limit=limit)
        except Exception as e:
            print(f"❌ Graph Endpoint: Error during blocking call: {e}")
            return [{"error": str(e)}] 

    try:
        # "await" การรันในเธรดแยก (ไม่บล็อก)
        relations = await asyncio.to_thread(_blocking_graph_call)

        # [V34 FIX] (แก้บั๊ก 'list' object has no attribute 'count')
        if not relations or (isinstance(relations, list) and relations and relations[0].get("error")):
            error_msg = relations[0].get("error") if relations else "Unknown error"
            raise Exception(f"Graph query failed in thread: {error_msg}")

        # (โค้ดสร้าง Nodes/Edges... "แข็งแรงดี")
        nodes, edges, node_ids = [], [], set()
        for rel in relations:
            if 'source_id' not in rel or 'target_id' not in rel: continue # [NEW] กันเหนียว
            if rel['source_id'] not in node_ids:
                nodes.append({"id": rel['source_id'], "label": rel['source'], "group": rel['source_labels'][0] if rel.get('source_labels') else 'Unknown'})
                node_ids.add(rel['source_id'])
            if rel['target_id'] not in node_ids:
                nodes.append({"id": rel['target_id'], "label": rel['target'], "group": rel['target_labels'][0] if rel.get('target_labels') else 'Unknown'})
                node_ids.add(rel['target_id'])
            edges.append({"from": rel['source_id'], "to": rel['target_id'], "label": rel['relationship'].replace("_", " ").lower(), "arrows": "to"})
        
        return {"nodes": nodes, "edges": edges}
    
    except Exception as e:
        print(f"❌ API Error on /api/graph/explore: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching graph data: {e}")

print("🌐 กำลังเปิดประตูมิติ... เริ่มต้นเซิร์ฟเวอร์ FastAPI...")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
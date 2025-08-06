# core/dispatcher.py
# (V6 - The Final, Complete & Resilient Conductor)

import traceback
from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class FinalResponse(BaseModel):
    agent_used: str
    answer: str
    image: Optional[Dict] = None
    history: Optional[List[Dict[str, str]]] = None
    error: bool = False
    thought_process: Optional[Dict[str, Any]] = None

class Dispatcher:
    def __init__(self, agents: Dict, key_manager):
        self.agents = agents
        self.google_key_manager = key_manager
        self.memory_manager = agents.get("MEMORY")
        
        self.rag_engine = None
        for agent in agents.values():
            if hasattr(agent, 'rag_engine') and agent.rag_engine is not None:
                self.rag_engine = agent.rag_engine
                print(f"✅ Dispatcher: RAG Engine linked from {agent.__class__.__name__}.")
                break
        
        print("🚦 ผู้ควบคุมวงออร์เคสตรา (Dispatcher) ขึ้นประจำตำแหน่งบนโพเดียม")

    def _format_history_for_display(self, history_dicts: List[Dict]) -> List[Dict[str, str]]:
        return [{"role": h.get("role"), "parts": h.get("content")} for h in history_dicts]

    async def handle_query(self, query: str, user_id: str) -> FinalResponse:
        self.memory_manager.add_memory(role="user", content=query, session_id=user_id, agent_used="USER")
        
        try:
            pending_query = self.memory_manager.check_and_clear_pending_deep_dive(user_id, user_confirmation=query)
            if pending_query:
                print(f"✅ User confirmed deep dive. Routing to Planner for: '{pending_query}'")
                return await self._run_deep_analysis(pending_query, user_id)

            feng_agent = self.agents.get("FENG")
            if not feng_agent: raise ValueError("CRITICAL: FengAgent not found.")

            short_mem = self.memory_manager.get_last_n_memories(session_id=user_id, n=6)
            dispatch_order = feng_agent.handle(query, short_mem)
            
            intent = dispatch_order.get("intent")
            corrected_query = dispatch_order.get("corrected_query")

            intent_to_agent_map = {
                "GENERAL_CONVERSATION": "GENERAL_HANDLER",
                "DEEP_ANALYSIS_REQUEST": "PROACTIVE_OFFER_HANDLER",
                "COUNSELING_REQUEST": "COUNSELOR",
                "NEWS_REQUEST": "NEWS",
                "CODE_REQUEST": "CODER",
                "IMAGE_REQUEST": "IMAGE",
                "LIBRARIAN_REQUEST": "LIBRARIAN",
                "SYSTEM_COMMAND": "SYSTEM",
                "USER_STORYTELLING": "LISTENER"
            }
            
            agent_name = intent_to_agent_map.get(intent)
            
            if agent_name and (agent := self.agents.get(agent_name)):
                print(f"🚦 Dispatcher: Routing intent '{intent}' to '{agent_name}'.")
                
                if intent in ["GENERAL_CONVERSATION", "COUNSELING_REQUEST", "CODE_REQUEST", "LIBRARIAN_REQUEST", "SYSTEM_COMMAND", "USER_STORYTELLING"]:
                    answer = agent.handle(corrected_query, short_mem)
                    return await self._finalize_response(agent_name, answer, user_id)
                
                elif intent == "DEEP_ANALYSIS_REQUEST":
                    response = agent.handle(corrected_query)
                    self.memory_manager.set_pending_deep_dive(user_id, response.get("original_query"))
                    return await self._finalize_response("PROACTIVE_OFFER", response.get("content"), user_id)

                elif intent == "NEWS_REQUEST":
                    response = agent.handle(corrected_query)
                    return await self._finalize_response("NEWS", response.get("answer"), user_id, thought_process=response.get("thought_process"))

                elif intent == "IMAGE_REQUEST":
                    image_info = agent.handle(corrected_query)
                    answer = "นี่คือรูปภาพที่ผมหามาให้ครับ" if image_info else "ขออภัยครับ ผมไม่พบรูปภาพที่เกี่ยวข้อง"
                    return await self._finalize_response("IMAGE", answer, user_id, image_info=image_info)
            
            print(f"⚠️ Dispatcher: Unknown or unhandled intent '{intent}'. Defaulting to Planner.")
            return await self._run_deep_analysis(corrected_query, user_id)

        except Exception as e:
            print(f"❌ Unhandled error in Dispatcher handle_query: {e}")
            traceback.print_exc()
            
            apology_agent = self.agents.get("APOLOGY")
            if apology_agent:
                last_query = self.memory_manager.get_last_user_query(user_id)
                error_context = f"An exception occurred: {type(e).__name__} - {e}"
                apology_answer = apology_agent.handle(last_query, error_context)
                return await self._finalize_response("APOLOGY_HANDLER", apology_answer, user_id, is_error=True)
            
            return await self._finalize_response("DISPATCHER_ERROR", "ขออภัยครับ เกิดข้อผิดพลาดร้ายแรงในระบบจัดการ", user_id, is_error=True)

    async def _run_deep_analysis(self, query: str, user_id: str) -> FinalResponse:
        """
        ฟังก์ชันย่อยสำหรับรันกระบวนการวิเคราะห์เชิงลึกทั้งหมด
        """
        print(f"🧠 Dispatcher: Initiating deep analysis for query: '{query}'")
        planner_agent = self.agents.get("PLANNER")
        if not planner_agent:
            raise ValueError("CRITICAL: PlannerAgent not found.")

        short_mem = self.memory_manager.get_last_n_memories(session_id=user_id)
        available_cats = self.rag_engine.available_categories if self.rag_engine else []
        planner_result = planner_agent.handle(query, short_mem, available_cats)
        
        final_draft = planner_result.get("answer", "ขออภัย มีข้อผิดพลาดในการสร้างบทวิเคราะห์")
        thought_process = planner_result.get("thought_process")
        
        return await self._finalize_response("PLANNER", final_draft, user_id, thought_process=thought_process)

    async def _finalize_response(self, agent_used: str, answer: str, user_id: str, 
                                 image_info: Optional[Dict] = None, is_error: bool = False,
                                 thought_process: Optional[Dict] = None) -> FinalResponse:
        """
        ฟังก์ชันย่อยสำหรับขั้นตอนสุดท้าย: การจัดรูปแบบและบันทึกความทรงจำ
        """
        final_answer = answer or ""
        
        agents_that_need_formatting = {"PLANNER", "NEWS"}
        if agent_used in agents_that_need_formatting and not is_error and answer:
             formatter = self.agents.get("FORMATTER")
             if formatter:
                 print(f"✍️ Dispatcher: Passing draft from {agent_used} to Formatter Agent.")
                 
                 synthesis_order = {
                     "original_query": self.memory_manager.get_last_user_query(user_id),
                     "history": self.memory_manager.get_last_n_memories(user_id, n=4),
                     "draft_to_review": final_answer
                 }
                 final_answer = formatter.handle(synthesis_order)
        
        self.memory_manager.add_memory(
            role="model", 
            content=final_answer, 
            session_id=user_id,
            agent_used=agent_used
        )
        
        final_history = self.memory_manager.get_last_n_memories(session_id=user_id)
        history_for_display = self._format_history_for_display(final_history)

        return FinalResponse(
            agent_used=agent_used, 
            answer=final_answer,
            image=image_info, 
            history=history_for_display,
            error=is_error,
            thought_process=thought_process
        )
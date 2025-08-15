# knowledge_extractor_gemini.py
# (V13 - Safe & Production-Ready)
# อัปเกรดสู่มาตรฐานความปลอดภัยและการจัดการไฟล์สูงสุด

import json
import os
import time
import re
import traceback
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
from google.api_core.exceptions import ResourceExhausted, TooManyRequests, GoogleAPICallError
import google.generativeai as genai
from neo4j import GraphDatabase
from tqdm import tqdm

from core.config import settings
from core.api_key_manager import ApiKeyManager, AllKeysOnCooldownError

class KnowledgeGraphExtractorGemini:
    """
    โรงงานสกัดความรู้สำหรับ "Gemini"
    (เวอร์ชันปรับปรุง: ใช้ Batch Write และ File Safety Standard)
    """
    def __init__(self, key_manager: ApiKeyManager, model_name: str, neo4j_driver):
        self.key_manager = key_manager
        self.neo4j_driver = neo4j_driver
        self.model_name = model_name
        self.extraction_prompt_template = """
**ภารกิจของคุณ:**  
คุณคือ "สถาปนิกข้อมูล" (Data Architect) ผู้เชี่ยวชาญด้านการวางโครงสร้าง ภารกิจของคุณคือการวิเคราะห์ JSON จากหนังสือ และแปลงให้เป็น "พิมพ์เขียว Knowledge Graph" ที่มีโครงสร้างถูกต้องและแม่นยำที่สุด

**กฎการทำงาน:**
- สร้าง "โครงสร้าง" (Nodes, Edges, Labels) ให้ถูกต้องตามแนวทาง
- สำหรับ "description" และ "insight" ให้ทำการสรุปเบื้องต้นตามข้อมูลที่ได้รับ ทีมมัณฑนากร (Refinement Team) จะมาขัดเกลาในภายหลัง

---
## ⛓️ ข้อมูลนำเข้า (INPUT SCHEMA):
```json
{{
  "book_title": "ชื่อหนังสือ",
  "category": "หมวดหมู่หนังสือ",
  "chapter_title": "ชื่อบท",
  "subsection_title": "ชื่อหัวข้อย่อย",
  "title": "ชื่อหัวข้อหลักของเนื้อหาส่วนนี้",
  "description": "คำอธิบายสั้นๆ",
  "content": "เนื้อหาหลักเต็มๆ"
}}
🧠 โครงสร้างผลลัพธ์ (OUTPUT SCHEMA) (ตอบกลับเป็น JSON เท่านั้น):
json
{{
  "nodes": [
    {{ "id": "Unique ID ของโหนด", "label": "ประเภทของโหนด (Node Label)", "properties": {{...}} }}
  ],
  "edges": [
    {{ "source": "ID โหนดต้นทาง", "target": "ID โหนดปลายทาง", "label": "ประเภทความสัมพันธ์ (Relationship Type)" }}
  ]
}}
📐 แนวทางการสกัดข้อมูล:
สร้างโครงสร้างลำดับชั้น:
Book Node: สร้าง ID ด้วย Book:{{book_title}}. Label คือ Book. Property คือ {{ "name": "{{book_title}}", "category": "{{category}}" }}
Chapter Node: (ถ้ามี) สร้าง ID ด้วย Chapter:{{book_title}}-{{chapter_title}}. Label คือ Chapter. Property คือ {{ "name": "{{chapter_title}}" }}. เชื่อม (Book) -[:HAS_CHAPTER]-> (Chapter)
Subsection Node: (ถ้ามี) สร้าง ID ด้วย Subsection:{{book_title}}-{{chapter_title}}-{{subsection_title}}. Label คือ Subsection. Property คือ {{ "name": "{{subsection_title}}" }}. เชื่อม (Chapter) -[:HAS_SUBSECTION]-> (Subsection)
ระบุโหนดหลักของเนื้อหา (Main Concept Node):
ใช้ title เป็นชื่อของโหนดหลัก สร้าง ID ด้วย Concept:{{title}}. Label คือ Concept (หรือ Strategy, Technique ตามความเหมาะสม)
สร้าง property description โดยการสังเคราะห์ description และ content เข้าด้วยกัน ให้เป็นคำอธิบายเชิงแนวคิดที่กระชับ
เชื่อมโหนดโครงสร้างกับโหนดหลัก: (Subsection หรือ Chapter) -[:MENTIONS]-> (Concept)
เพิ่มมิติความเข้าใจ (Enrichment):
ถ้าเป็นกลยุทธ์ ให้เพิ่ม properties: strategy_type, influence_level, adaptability_level ให้กับ Concept Node
Insight Property: สกัด "แก่นแท้หรือผลลัพธ์ที่คาดหวัง" ของแนวคิดนี้จากเนื้อหา แล้วเพิ่มเป็น property ชื่อ insight
สร้างโหนดจากรายการ (Lists):
Psychological Technique Nodes: สำหรับแต่ละรายการใน psychological_techniques ให้สร้าง Node โดยใช้ ID Technique:{{ชื่อเทคนิค}} และ Label Technique. เพิ่ม Property {{ "name": "{{ชื่อเทคนิค}}", "type": "Psychological" }}
Risk Factor Nodes: สำหรับแต่ละรายการใน risk_factors ให้สร้าง Node โดยใช้ ID Risk:{{ชื่อปัจจัยเสี่ยง}} และ Label Risk. เพิ่ม Property {{ "name": "{{ชื่อปัจจัยเสี่ยง}}" }}
Control Technique Nodes: สำหรับแต่ละรายการใน control_techniques ให้สร้าง Node โดยใช้ ID Technique:{{ชื่อเทคนิคควบคุม}} และ Label Technique. เพิ่ม Property {{ "name": "{{ชื่อเทคนิคควบคุม}}", "type": "Control" }}
สร้างความสัมพันธ์เชิงลึก (Deep Relationships):
(Main Concept) -[:USES_TECHNIQUE]-> (Technique)
(Main Concept) -[:HAS_RISK]-> (Risk)
(Risk) -[:MITIGATED_BY]-> (Control Technique)
🎯 เจตนาเบื้องหลังการออกแบบ:
การสกัดข้อมูลของคุณคือการสร้าง "โครงกระดูก" ของความรู้ที่แข็งแรง เพื่อให้ทีมอื่นสามารถมา "เติมจิตวิญญาณ" ได้ในภายหลัง

JSON CHUNK ที่ต้องวิเคราะห์:
json
{text_chunk}
ผลลัพธ์ JSON:
"""

    def _extract_json(self, text: str) -> Optional[Dict]:
        text = text.strip()
        match = re.search(r'```(json)?\s*(\{[\s\S]*?\})\s*```', text, re.DOTALL)
        if match:
            json_str = match.group(2)
            try: return json.loads(json_str)
            except json.JSONDecodeError: pass
        brace_level, start_index = 0, -1
        for i, char in enumerate(text):
            if char == '{':
                if start_index == -1: start_index = i
                brace_level += 1
            elif char == '}':
                if start_index != -1:
                    brace_level -= 1
                    if brace_level == 0:
                        json_str = text[start_index : i + 1]
                        try: return json.loads(json_str)
                        except json.JSONDecodeError: return None
        return None

    def _process_single_chunk(self, line: str, max_retries: int) -> Optional[Dict]:
        if not line.strip(): return None
        try:
            item = json.loads(line)
            text_to_process = json.dumps(item, ensure_ascii=False, indent=2)
            prompt = self.extraction_prompt_template.format(text_chunk=text_to_process)
        except json.JSONDecodeError:
            print(f"Skipping malformed JSON line: {line[:100]}...")
            return None
        last_exception = None
        for attempt in range(max_retries):
            try:
                api_key = self.key_manager.get_key()
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(self.model_name)
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
                response = model.generate_content(prompt, safety_settings=safety_settings)
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    raise ValueError(f"Gemini API blocked the prompt. Reason: {response.prompt_feedback.block_reason}")
                graph_data = self._extract_json(response.text)
                if graph_data and isinstance(graph_data, dict) and "nodes" in graph_data:
                    for node in graph_data.get("nodes", []):
                        if node.get("label") in ["Concept", "Strategy"]:
                            if "properties" not in node: node["properties"] = {}
                            node["properties"]["raw_content"] = item.get("content", "")
                    return graph_data
                else:
                    raise ValueError(f"Failed to extract valid JSON. Raw response: {response.text[:200]}...")
            except (ResourceExhausted, TooManyRequests) as e:
                error_type = 'quota' if isinstance(e, ResourceExhausted) else 'rate_limit'
                print(f"🔻 Key ...{api_key[-4:]} failed ({error_type}). Trying next key... ({attempt + 1}/{max_retries})")
                self.key_manager.report_failure(api_key, error_type=error_type)
                last_exception = e
            except (GoogleAPICallError, ValueError) as e:
                print(f"💥 Key ...{api_key[-4:]} encountered an error: {e}. Trying next key... ({attempt + 1}/{max_retries})")
                self.key_manager.report_failure(api_key, error_type='generic')
                last_exception = e
            except AllKeysOnCooldownError as e:
                raise e
        raise last_exception if last_exception else Exception("Failed to process chunk after all retries.")

    def _write_batch_to_neo4j(self, graph_data_list: List[Dict]):
        if not graph_data_list: return
        all_nodes, all_edges = [], []
        for graph_data in graph_data_list:
            nodes, edges = graph_data.get("nodes", []), graph_data.get("edges", [])
            for node in nodes:
                if node.get('id'):
                    node['id'] = str(node['id']).strip().lower()
                    all_nodes.append(node)
            for edge in edges:
                if edge.get('source') and edge.get('target'):
                    edge['source'] = str(edge['source']).strip().lower()
                    edge['target'] = str(edge['target']).strip().lower()
                    all_edges.append(edge)
        with self.neo4j_driver.session() as session:
            session.execute_write(self._create_nodes_and_edges_in_batch, all_nodes, all_edges)

    @staticmethod
    def _create_nodes_and_edges_in_batch(tx, nodes, edges):
        nodes_by_label = {}
        for node in nodes:
            label = node.get('label')
            if not label: continue
            cleaned_label = re.sub(r'[^a-zA-Zก-๙]', '', str(label)) or "Concept"
            if cleaned_label not in nodes_by_label:
                nodes_by_label[cleaned_label] = []
            properties = node.get('properties', {})
            if 'name' not in properties and node.get('id'):
                properties['name'] = node['id'].split(':')[-1].replace('-', ' ').replace('_', ' ').title()
            nodes_by_label[cleaned_label].append({'id': node['id'], 'properties': properties})
        for label, node_list in nodes_by_label.items():
            query = (f"""
            UNWIND $node_data AS data
            MERGE (n:{label} {{id: data.id}})
            ON CREATE SET n = data.properties, n.id = data.id, n.created_at = timestamp(), n.updated_at = timestamp()
            ON MATCH SET n += data.properties, n.updated_at = timestamp()
            """)
            tx.run(query, node_data=node_list)
        edges_by_label = {}
        for edge in edges:
            label = edge.get('label')
            if not label: continue
            cleaned_label = re.sub(r'[^a-zA-Z_]', '', str(label)).upper()
            if not cleaned_label: continue
            if cleaned_label not in edges_by_label:
                edges_by_label[cleaned_label] = []
            edges_by_label[cleaned_label].append({'source': edge['source'], 'target': edge['target']})
        for label, edge_list in edges_by_label.items():
            query = (f"""
            UNWIND $edge_data AS data
            MATCH (a {{id: data.source}})
            MATCH (b {{id: data.target}})
            MERGE (a)-[r:{label}]->(b)
            """)
            tx.run(query, edge_data=edge_list)

    def _process_batch_parallel(self, lines_batch: List[str], max_workers: int) -> (List[Dict], List[str]):
        failed_lines, successful_graphs = [], []
        max_retries = len(self.key_manager.all_keys)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_line = {executor.submit(self._process_single_chunk, line, max_retries): line for line in lines_batch}
            progress_bar = tqdm(as_completed(future_to_line), total=len(lines_batch), desc="  - Processing Batch", leave=False, unit="chunk")
            for future in progress_bar:
                original_line = future_to_line[future]
                try:
                    graph_data = future.result()
                    if graph_data:
                        successful_graphs.append(graph_data)
                except AllKeysOnCooldownError as e:
                    print(f"\n❌ CRITICAL: {e}. Stopping all processing.")
                    for f in future_to_line: f.cancel()
                    raise e
                except Exception as e:
                    print(f"\nDEBUG: Line failed after all retries: {type(e).__name__} - {e}\n")
                    failed_lines.append(original_line)
                    progress_bar.set_postfix_str(f"fails={len(failed_lines)}", refresh=True)
        return successful_graphs, failed_lines

    def process_file_resiliently(self, file_path: str, batch_size: int, max_workers: int):
        file_name = os.path.basename(file_path)
        processed_folder = os.path.join(os.path.dirname(file_path), "_processed")
        os.makedirs(processed_folder, exist_ok=True)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
            if not all_lines:
                print(f"  - ✅ File '{file_name}' is empty. Moving to processed.")
                shutil.move(file_path, os.path.join(processed_folder, file_name))
                return
            print(f"\n--- 🧠 Processing: {file_name} (Model: {self.model_name}, Total: {len(all_lines)} lines) ---")
            lines_iterator = iter(all_lines)
            all_failed_lines = []
            with tqdm(total=len(all_lines), desc=f"Overall ({file_name})", unit="lines") as pbar:
                while True:
                    lines_batch = [line for _, line in zip(range(batch_size), lines_iterator)]
                    if not lines_batch:
                        break
                    successful_graphs, failed_lines_in_batch = self._process_batch_parallel(lines_batch, max_workers)
                    if successful_graphs:
                        self._write_batch_to_neo4j(successful_graphs)
                    if failed_lines_in_batch:
                        all_failed_lines.extend(failed_lines_in_batch)
                    pbar.update(len(lines_batch))
            if all_failed_lines:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(all_failed_lines)
                print(f"  - ⚠️ File state partially updated. {len(all_failed_lines)} failed lines remain in '{file_name}'.")
            else:
                shutil.move(file_path, os.path.join(processed_folder, file_name))
                print(f"  - ✨ File state fully updated. Moved '{file_name}' to processed folder.")
        except AllKeysOnCooldownError as e:
            raise e
        except Exception as e:
            print(f"❌ An unexpected error occurred while processing {file_path}: {e}")
            traceback.print_exc()

def main():
    start_time = time.time()
    print("--- 🏭 Starting Knowledge Graph Extraction Process (V13 - Gemini Production) ---")

    BATCH_SIZE = 50
    MAX_WORKERS = 2
    BOOKS_FOLDER = "data/books"
    MODEL_TO_USE = "gemini-1.5-flash-latest"
    
    from core.api_key_manager import ApiKeyManager, AllKeysOnCooldownError

    key_manager = ApiKeyManager(all_google_keys=settings.GOOGLE_API_KEYS, silent=True)
    print(f"🔑 Using Google Key Manager for model: {MODEL_TO_USE}")

    neo4j_driver = None
    try:
        neo4j_driver = GraphDatabase.driver(
            settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        neo4j_driver.verify_connectivity()
        print("✅ Successfully connected to Neo4j database.")

        extractor_instance = KnowledgeGraphExtractorGemini(
            key_manager=key_manager, model_name=MODEL_TO_USE, neo4j_driver=neo4j_driver
        )
        
        if not os.path.exists(BOOKS_FOLDER):
            print(f"⚠️ Books folder not found: {BOOKS_FOLDER}")
            return

        files_to_process = sorted([f for f in os.listdir(BOOKS_FOLDER) if f.endswith(".jsonl")])
        if not files_to_process:
            print(f"🟡 No .jsonl files found in '{BOOKS_FOLDER}'.")
        else:
            print(f"📚 Found {len(files_to_process)} files to process.")
            for filename in files_to_process:
                book_file_path = os.path.join(BOOKS_FOLDER, filename)
                extractor_instance.process_file_resiliently(
                    file_path=book_file_path, 
                    batch_size=BATCH_SIZE, 
                    max_workers=MAX_WORKERS
                )

    except AllKeysOnCooldownError as e:
        print(f"\n🔥🔥🔥 API KEYS EXHAUSTED - CRITICAL FAILURE 🔥🔥🔥")
        print(f"   -> Reason: {e}")
        print(f"   -> Halting the entire extraction process. Remaining files will be processed in the next run.")
    except Exception as e:
        print(f"❌ A critical error occurred in the main process: {e}")
        traceback.print_exc()
    finally:
        if neo4j_driver:
            neo4j_driver.close()
            print("\n🔗 Neo4j connection closed.")

        end_time = time.time()
        print(f"\n✅ Knowledge Graph extraction process finished. Total time: {end_time - start_time:.2f} seconds.")


if __name__ == "__main__":
    main()
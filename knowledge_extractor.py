# knowledge_extractor.py
# (V6 - The Final, Groq-Dedicated & Bulletproof Version)

import json
import os
import time
import re
import traceback
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
from groq import Groq
from neo4j import GraphDatabase
from tqdm import tqdm

from core.config import settings
from core.groq_key_manager import GroqApiKeyManager, AllGroqKeysOnCooldownError

class KnowledgeGraphExtractor:
    def __init__(self, key_manager: GroqApiKeyManager, model_name: str, neo4j_driver):
        self.key_manager = key_manager
        self.neo4j_driver = neo4j_driver
        self.model_name = model_name
        self.extraction_prompt_template = """
**ภารกิจของคุณ:**  
คุณคือสถาปนิกข้อมูลผู้เชี่ยวชาญที่มีเป้าหมายไม่ใช่แค่สกัดข้อมูล แต่เพื่อ **สร้างโครงสร้างความเข้าใจ**  
โดยคุณจะวิเคราะห์ JSON ที่ได้จากหนังสือ และแปลงให้เป็น Knowledge Graph (KG) ที่ **สื่อสารแนวคิดสำคัญได้อย่างมีความหมาย** ไม่ใช่เพียงอ้างอิงแบบคำต่อคำ
---
🔍 **หลักการสำคัญ:**  
คุณจะไม่เพียง "ถอดเนื้อหา" แต่จะ **ช่วยเฟิงเอเจนเข้าใจโลกในเชิงแนวคิด**  
> "จำเป็นรู้หนังสือทุกเล่ม และ *เข้าใจสิ่งที่หนังสือพยายามสอน*"
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
  "content": "เนื้อหาหลักเต็มๆ",
  "strategy_type": "ประเภทกลยุทธ์",
  "psychological_techniques": ["เทคนิคทางจิตวิทยา"],
  "risk_factors": ["ปัจจัยเสี่ยง"],
  "control_techniques": ["วิธีควบคุมหรือป้องกัน"],
  "influence_level": "ระดับผลกระทบ (สูง/กลาง/ต่ำ)",
  "adaptability_level": "ระดับการปรับใช้ (สูง/กลาง/ต่ำ)"
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
Chapter Node: (ถ้ามี) สร้าง ID ด้วย Chapter:{{book_title}}-{{chapter_title}}. Label คือ Chapter. เชื่อม (Book) -[:HAS_CHAPTER]-> (Chapter)
Subsection Node: (ถ้ามี) สร้าง ID ด้วย Subsection:{{book_title}}-{{chapter_title}}-{{subsection_title}}. Label คือ Subsection. เชื่อม (Chapter) -[:HAS_SUBSECTION]-> (Subsection)
ระบุโหนดหลักของเนื้อหา (Main Concept Node):
ใช้ title เป็นชื่อของโหนดหลัก สร้าง ID ด้วย Concept:{{title}}. Label คือ Concept (หรือ Strategy, Technique ตามความเหมาะสม)
สร้าง property description โดยการสังเคราะห์ description และ content เข้าด้วยกัน ให้เป็นคำอธิบายเชิงแนวคิดที่กระชับ
เชื่อมโหนดโครงสร้างกับโหนดหลัก: (Subsection หรือ Chapter) -[:MENTIONS]-> (Concept)
เพิ่มมิติความเข้าใจ (Enrichment):
ถ้าเป็นกลยุทธ์ ให้เพิ่ม properties: strategy_type, influence_level, adaptability_level ให้กับ Concept Node
Insight Property: สกัด "แก่นแท้หรือผลลัพธ์ที่คาดหวัง" ของแนวคิดนี้จากเนื้อหา แล้วเพิ่มเป็น property ชื่อ insight
สร้างโหนดจากรายการ (Lists):
Psychological Technique Nodes: สำหรับแต่ละรายการใน psychological_techniques ให้สร้าง Node โดยใช้ ID Technique:{{ชื่อเทคนิค}} และ Label Technique. เพิ่ม Property {{ "type": "Psychological" }}
Risk Factor Nodes: สำหรับแต่ละรายการใน risk_factors ให้สร้าง Node โดยใช้ ID Risk:{{ชื่อปัจจัยเสี่ยง}} และ Label Risk
Control Technique Nodes: สำหรับแต่ละรายการใน control_techniques ให้สร้าง Node โดยใช้ ID Technique:{{ชื่อเทคนิคควบคุม}} และ Label Technique. เพิ่ม Property {{ "type": "Control" }}
สร้างความสัมพันธ์เชิงลึก (Deep Relationships):
(Main Concept) -[:USES_TECHNIQUE]-> (Technique)
(Main Concept) -[:HAS_RISK]-> (Risk)
(Risk) -[:MITIGATED_BY]-> (Control Technique)
🎯 เป้าหมายสุดท้าย: สร้าง Knowledge Graph ที่มีความแม่นยำทางเทคนิคและสื่อถึงความเข้าใจในระดับแนวคิด เพื่อให้ "เฟิง" สามารถใช้ "กรอบคิด" ที่ยืดหยุ่นนี้ในการวิเคราะห์และตอบสนองต่อสถานการณ์ต่างๆ
🎯 เจตนาเบื้องหลังการออกแบบ:
การสกัดข้อมูลของคุณจะไม่ใช่เพื่อให้ AI จำหนังสือได้หมด
แต่เพื่อสร้าง โครงสร้างความเข้าใจแบบมนุษย์
ให้เฟิงสามารถตอบสนองต่อโลกด้วย "กรอบคิด" ที่ยืดหยุ่น ไม่ใช่แค่คำตอบที่อ้างอิง
JSON CHUNK ที่ต้องวิเคราะห์:
json
{text_chunk}
ผลลัพธ์ JSON:
"""
    def _extract_json(self, text: str) -> Optional[Dict]:
        text = text.strip()
        match = re.search(r'```(json)?\s*(\{[\s\S]*?\})\s*```', text)
        if match:
            json_str = match.group(2)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        brace_level = 0
        start_index = -1
        for i, char in enumerate(text):
            if char == '{':
                if start_index == -1: start_index = i
                brace_level += 1
            elif char == '}':
                if start_index != -1:
                    brace_level -= 1
                    if brace_level == 0:
                        json_str = text[start_index : i + 1]
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            return None
        return None

    def _get_raw_llm_response(self, text_chunk: str) -> str:
        api_key = self.key_manager.get_key()
        prompt = self.extraction_prompt_template.format(text_chunk=text_chunk)
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model_name,
        )
        return chat_completion.choices[0].message.content

    def _write_graph_to_neo4j(self, graph_data: Dict):
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        if not nodes and not edges: return
        id_map, cleaned_nodes, cleaned_edges = {}, [], []
        for node in nodes:
            original_id = node.get('id')
            if not original_id or not isinstance(original_id, str): continue
            cleaned_id = original_id.strip().lower()
            id_map[original_id] = cleaned_id
            node['id'] = cleaned_id
            cleaned_nodes.append(node)
        for edge in edges:
            edge['source'] = id_map.get(edge.get('source'), edge.get('source'))
            edge['target'] = id_map.get(edge.get('target'), edge.get('target'))
            cleaned_edges.append(edge)
        with self.neo4j_driver.session() as session:
            session.execute_write(self._create_nodes_and_edges, cleaned_nodes, cleaned_edges)

    @staticmethod
    def _create_nodes_and_edges(tx, nodes, edges):
        for node in nodes:
            node_id, node_label = node.get('id'), node.get('label')
            if not node_id or not node_label: continue
            cleaned_label = re.sub(r'[^a-zA-Zก-๙]', '', str(node_label)) or "Concept"
            query = (f"MERGE (n:{cleaned_label} {{id: $id}}) "
                     f"ON CREATE SET n.created_at = timestamp(), n.updated_at = timestamp() "
                     f"ON MATCH SET n.updated_at = timestamp() "
                     f"SET n += $properties, n.name = $id")
            tx.run(query, id=node_id, properties=node.get('properties', {}))
        for edge in edges:
            source, target, label = edge.get('source'), edge.get('target'), edge.get('label')
            if not source or not target or not label: continue
            cleaned_edge_label = re.sub(r'[^A-Z_]', '', str(label))
            if not cleaned_edge_label: continue
            query = (f"MATCH (a {{id: $source}}), (b {{id: $target}}) "
                     f"MERGE (a)-[r:{cleaned_edge_label}]->(b)")
            tx.run(query, source=source, target=target)

    def _process_single_chunk(self, line: str) -> Optional[Dict]:
        if not line.strip(): return None
        try:
            item = json.loads(line)
            text_to_process = json.dumps(item, ensure_ascii=False, indent=2)
            raw_response_text = self._get_raw_llm_response(text_to_process)
            graph_data = self._extract_json(raw_response_text)
            if graph_data and isinstance(graph_data, dict) and "nodes" in graph_data and "edges" in graph_data:
                return graph_data
            else:
                print(f"  - ⚠️ Invalid or missing JSON. Raw response was: {raw_response_text[:200]}...")
                return None
        except Exception as e:
            raise e

    def _process_batch_parallel(self, lines_batch: List[str], max_workers: int) -> List[str]:
        failed_lines = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_line = {executor.submit(self._process_single_chunk, line): line for line in lines_batch}
            progress_bar = tqdm(as_completed(future_to_line), total=len(lines_batch), desc="  - Processing Batch", leave=False, unit="chunk")
            for future in progress_bar:
                original_line = future_to_line[future]
                try:
                    graph_data = future.result()
                    if graph_data:
                        self._write_graph_to_neo4j(graph_data)
                    else:
                        raise ValueError("Processing chunk failed (e.g., JSON parsing).")
                except AllGroqKeysOnCooldownError as e:
                    print(f"\n❌ CRITICAL: {e}. Stopping all processing.")
                    for f in future_to_line: f.cancel()
                    raise e
                except Exception as e:
                    print(f"\nDEBUG: Caught exception in worker thread: {type(e).__name__} - {e}\n")
                    failed_lines.append(original_line)
                    progress_bar.set_postfix_str(f"fails={len(failed_lines)}", refresh=True)
        return failed_lines

    def process_file_resiliently(self, file_path: str, batch_size: int, max_workers: int):
        file_name = os.path.basename(file_path)
        temp_file_path = file_path + ".tmp"
        
        print(f"\n--- 🧠 Processing: {file_name} (Model: {self.model_name}) ---")
        
        try:
            if not os.path.exists(file_path):
                print(f"  - ⚠️ File '{file_name}' not found. Skipping.")
                return

            with open(file_path, "r", encoding="utf-8") as f:
                total_lines = sum(1 for _ in f)
            if total_lines == 0:
                print(f"  - ✅ File '{file_name}' is empty. Skipping.")
                return

            with open(temp_file_path, 'w', encoding='utf-8') as temp_f:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines_batch = []
                    with tqdm(total=total_lines, desc=f"Overall ({file_name})", unit="lines") as pbar:
                        for line in f:
                            lines_batch.append(line)
                            if len(lines_batch) >= batch_size:
                                failed_lines = self._process_batch_parallel(lines_batch, max_workers)
                                for failed_line in failed_lines: temp_f.write(failed_line)
                                pbar.update(len(lines_batch))
                                lines_batch = []
                        if lines_batch:
                            failed_lines = self._process_batch_parallel(lines_batch, max_workers)
                            for failed_line in failed_lines: temp_f.write(failed_line)
                            pbar.update(len(lines_batch))

            temp_file_size = os.path.getsize(temp_file_path)
            print(f"  [DEBUG] Finished. Temp file size: {temp_file_size} bytes.")
            
            print(f"  [DEBUG] Replacing original file...")
            os.remove(file_path)
            shutil.move(temp_file_path, file_path)
            
            final_file_size = os.path.getsize(file_path)
            print(f"  [DEBUG] Replacement complete. Final file size: {final_file_size} bytes.")
            
            if final_file_size > 0:
                print(f"  - ⚠️ File state partially updated. {final_file_size} bytes of failed chunks remain.")
            else:
                print(f"  - ✨ File state fully updated for '{file_name}'.")

        except (AllGoogleKeysOnCooldownError, AllGroqKeysOnCooldownError):
             print(f"🛑 Halting process for {file_name} due to API key exhaustion. Failed chunks are saved.")
             if os.path.exists(temp_file_path):
                 os.remove(file_path)
                 shutil.move(temp_file_path, file_path)
        
        except Exception as e:
            print(f"❌ An unexpected error occurred while processing {file_path}: {e}")
            if os.path.exists(temp_file_path): os.remove(temp_file_path)
            traceback.print_exc()


if __name__ == "__main__":
    start_time = time.time()
    print("--- 🏭 Starting Knowledge Graph Extraction Process (V6 - Groq Dedicated) ---")

    BATCH_SIZE = 20
    MAX_WORKERS = 2 
    BOOKS_FOLDER = "data/books"
    MODEL_TO_USE = settings.KNOWLEDGE_EXTRACTOR_MODEL
    
    key_manager = GroqApiKeyManager(all_groq_keys=settings.GROQ_API_KEYS, silent=True)
    print(f"🔑 Using Groq Key Manager for model: {MODEL_TO_USE}")
    
    neo4j_driver = None
    try:
        neo4j_driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        neo4j_driver.verify_connectivity()
        print("✅ Successfully connected to Neo4j database.")

        extractor = KnowledgeGraphExtractor(
            key_manager=key_manager, 
            model_name=MODEL_TO_USE,
            neo4j_driver=neo4j_driver
        )

        if os.path.exists(BOOKS_FOLDER):
            files_to_process = sorted([f for f in os.listdir(BOOKS_FOLDER) if f.endswith(".jsonl")])
            if not files_to_process:
                print(f"🟡 No .jsonl files found in '{BOOKS_FOLDER}'.")
            else:
                print(f"📚 Found {len(files_to_process)} files to process.")
                for filename in files_to_process:
                    book_file_path = os.path.join(BOOKS_FOLDER, filename)
                    extractor.process_file_resiliently(
                        file_path=book_file_path, 
                        batch_size=BATCH_SIZE, 
                        max_workers=MAX_WORKERS
                    )
        else:
            print(f"⚠️ Books folder not found: {BOOKS_FOLDER}")

    except Exception as e:
        print(f"❌ A critical error occurred in the main process: {e}")
        traceback.print_exc()
    finally:
        if neo4j_driver:
            neo4j_driver.close()
            print("\n🔗 Neo4j connection closed.")

    end_time = time.time()
    print(f"\n✅ Knowledge Graph extraction process complete! Total time: {end_time - start_time:.2f} seconds.")
# core/graph_manager.py
# (V2 - Cypher Ready)

from neo4j import GraphDatabase
from typing import List, Dict, Any
from core.config import settings

class GraphManager:
    """
    จัดการการเชื่อมต่อและค้นหาข้อมูลจากฐานข้อมูล Neo4j
    รองรับทั้งการค้นหาแบบพื้นฐานและการรัน Cypher Query โดยตรง
    """
    def __init__(self):
        self.driver = None
        try:
            if settings.NEO4J_URI and settings.NEO4J_USER and settings.NEO4J_PASSWORD:
                self.driver = GraphDatabase.driver(
                    settings.NEO4J_URI, 
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )
                self.driver.verify_connectivity()
                print("🔗 Graph Manager: Successfully connected to Neo4j.")
            else:
                print("🟡 Graph Manager: Neo4j credentials not found. Graph features disabled.")
        except Exception as e:
            print(f"❌ Graph Manager: Could not connect to Neo4j. Graph features disabled. Error: {e}")

    def close(self):
        if self.driver:
            self.driver.close()
            print("🔗 สมองส่วนความเข้าใจเชิงโครงสร้าง (Neo4j) เชื่อมต่อสำเร็จ")

    def find_related_concepts(self, entity_id: str, limit: int = 5) -> List[Dict]:
        """
        (เมธอดอัปเกรด) ค้นหาความสัมพันธ์โดยใช้ 'id' ที่ผ่านการ Normalization แล้ว
        """
        if not self.driver: return []
        normalized_id = entity_id.strip().lower()
        
        print(f"📈 Graph Manager: Searching for neighbors of '{normalized_id}'...")
        try:
            with self.driver.session() as session:
                result = session.execute_read(self._find_neighbors_transaction, normalized_id, limit)
            print(f"  -> Found {len(result)} related concepts.")
            return result
        except Exception as e:
            print(f"❌ Graph Manager: Error during neighbor search: {e}")
            return []

    @staticmethod
    def _find_neighbors_transaction(tx, entity_id, limit):
        query = (
            "MATCH (n {id: $entity_id})-[r]-(m) "
            "RETURN n.name AS source, labels(n) AS source_labels, "
            "       type(r) AS relationship, "
            "       m.name AS target, labels(m) AS target_labels, "
            "       n.id AS source_id, m.id AS target_id "
            "LIMIT $limit"
        )
        result = tx.run(query, entity_id=entity_id, limit=limit)
        return [dict(record) for record in result]

    # --- 👇 **** เมธอดใหม่ที่ทรงพลังที่สุด **** 👇 ---
    def execute_cypher(self, query: str, params: Dict[str, Any] = None) -> List[Dict]:
        """
        (เวอร์ชันปลอดภัย) รัน Cypher Query โดยใช้ Parameters เพื่อป้องกัน Injection
        """
        if not self.driver or not query: 
            return []
        
        # ใช้ params ที่ว่างเปล่าถ้าไม่ได้ส่งมา
        if params is None:
            params = {}
            
        print(f"⚡️ Graph Manager: Executing parameterized Cypher...")
        print(f"   Query: {query}")
        print(f"   Params: {params}")
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(self._run_query_transaction, query, params)
            print(f"  -> Query returned {len(result)} records.")
            return result
        except Exception as e:
            print(f"❌ Graph Manager: Error executing Cypher. Error: {e}")
            # ส่งข้อความ Error ที่ชัดเจนกลับไปให้ AI เรียนรู้
            return [{"error": f"Cypher Query Failed: {e}"}]

    @staticmethod
    def _run_query_transaction(tx, query, params):
        # ⭐️ tx.run จะจัดการกับการ Sanitize พารามิเตอร์ให้เราโดยอัตโนมัติ ⭐️
        result = tx.run(query, **params)
        return [dict(record) for record in result]
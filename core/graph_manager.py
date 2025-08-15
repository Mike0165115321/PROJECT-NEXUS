# core/graph_manager.py
# (V2.1 - Read/Write Separation & Refined)

from neo4j import GraphDatabase
from typing import List, Dict, Any, Literal

from core.config import settings

class GraphManager:
    """
    จัดการการเชื่อมต่อและค้นหาข้อมูลจากฐานข้อมูล Neo4j
    (เวอร์ชันปรับปรุง: แยกเมธอด Read/Write ชัดเจนเพื่อความเสถียร)
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
            print("🔗 Graph Manager: Neo4j connection closed.")

    def find_related_concepts(
        self, 
        entity_id: str, 
        limit: int = 5, 
        direction: Literal["out", "in", "both"] = "both"
    ) -> List[Dict]:
        if not self.driver: return []
        normalized_id = entity_id.strip().lower()
        
        print(f"📈 Graph Manager: Searching for neighbors of '{normalized_id}' (direction: {direction})...")
        try:
            with self.driver.session() as session:
                result = session.execute_read(self._find_neighbors_transaction, normalized_id, limit, direction)
            print(f"  -> Found {len(result)} related concepts.")
            return result
        except Exception as e:
            print(f"❌ Graph Manager: Error during neighbor search: {e}")
            return []

    @staticmethod
    def _find_neighbors_transaction(tx, entity_id, limit, direction):
        if direction == "out":
            arrow = "-[r]->"
        elif direction == "in":
            arrow = "<-[r]-"
        else:
            arrow = "-[r]-"
            
        query = (
            f"MATCH (n {{id: $entity_id}}){arrow}(m) "
            "RETURN n.name AS source, labels(n) AS source_labels, "
            "       type(r) AS relationship, "
            "       m.name AS target, labels(m) AS target_labels, "
            "       n.id AS source_id, m.id AS target_id "
            "LIMIT $limit"
        )
        result = tx.run(query, entity_id=entity_id, limit=limit)
        return [dict(record) for record in result]

    def execute_read_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict]:
        """
        รัน Cypher Query ที่เป็นการอ่านข้อมูลเท่านั้น (Read-only).
        """
        if not self.driver or not query: 
            return []
        
        params = params or {}
        print(f"⚡️ Graph Manager: Executing READ query...")
        
        try:
            with self.driver.session() as session:
                result = session.read_transaction(self._run_query_transaction, query, params)
            print(f"  -> Query returned {len(result)} records.")
            return result
        except Exception as e:
            print(f"❌ Graph Manager: Error executing READ Cypher. Error: {e}")
            return [{"error": f"Cypher Read Query Failed: {e}"}]

    def execute_write_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict]:
        """
        รัน Cypher Query ที่มีการเขียน/แก้ไขข้อมูล (CREATE, MERGE, SET, DELETE).
        """
        if not self.driver or not query:
            return []
            
        params = params or {}
        print(f"⚡️ Graph Manager: Executing WRITE query...")

        try:
            with self.driver.session() as session:
                result = session.write_transaction(self._run_query_transaction, query, params)
            print(f"  -> Write operation successful. Returned {len(result)} records.")
            return result
        except Exception as e:
            print(f"❌ Graph Manager: Error executing WRITE Cypher. Error: {e}")
            return [{"error": f"Cypher Write Query Failed: {e}"}]

    @staticmethod
    def _run_query_transaction(tx, query, params):
        result = tx.run(query, **params)
        return result.data()
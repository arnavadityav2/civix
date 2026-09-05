import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from civix_api.config import settings
from neo4j import GraphDatabase

async def main():
    try:
        driver = GraphDatabase.driver(
            settings.neo4j_uri, 
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        with driver.session() as session:
            query = """
                MATCH (a)-[r]->(b)
                RETURN type(r) AS rel_type, count(r) AS count
                ORDER BY count DESC
            """
            result = session.run(query)
            print("Relationships in Neo4j:")
            for record in result:
                print(f"{record['rel_type']}: {record['count']}")

            

                
    except Exception as e:
        print(f"Error querying Neo4j: {e}")

asyncio.run(main())

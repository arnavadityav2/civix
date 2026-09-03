import asyncio
import os
try:
    from neo4j import GraphDatabase
except ImportError:
    import sys
    sys.exit("neo4j not installed")

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

def main():
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            with driver.session() as session:
                # Count nodes
                result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
                print("Neo4j reachable: YES\nNodes:")
                records = list(result)
                if not records:
                    print("Empty graph")
                for record in records:
                    print(f"{record['labels']} | {record['count']}")
                
                # Count relationships
                result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
                print("\nRelationships:")
                records = list(result)
                if not records:
                    print("No relationships")
                for record in records:
                    print(f"{record['type']} | {record['count']}")

    except Exception as e:
        print("Neo4j reachable: NO")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

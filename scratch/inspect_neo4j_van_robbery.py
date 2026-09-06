from neo4j import GraphDatabase

def main():
    driver = GraphDatabase.driver('bolt://localhost:7688', auth=('neo4j', 'civix123456'))
    with driver.session() as session:
        print("=== NEO4J PERSON NODES FOR CIV-2012-001 ===")
        res = session.run("""
            MATCH (p:Person)
            WHERE p.name IN [
                'Suresh Valmiki', 'Rakesh Yadav', 'Mohinder Bhati', 
                'Ramesh Chauhan', 'Devender Nagar', 'Vikram Sharma', 
                'Anita Mehta', 'Ram Karan Singh'
            ]
            RETURN p.name as name, p.id as id, labels(p) as labels
        """)
        for row in res:
            print(f"Name: {row['name']:<20} | ID: {row['id']} | Labels: {row['labels']}")
            
        print("\n=== EXISTING COMMUNICATED_WITH EDGES IN GRAPH ===")
        res_comm = session.run("MATCH (p1:Person)-[r:COMMUNICATED_WITH]-(p2:Person) RETURN p1.name, p2.name, properties(r) LIMIT 5")
        for row in res_comm:
            print(row)

    driver.close()

if __name__ == "__main__":
    main()

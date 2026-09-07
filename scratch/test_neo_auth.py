from neo4j import GraphDatabase

for pwd in ['password', 'neo4j_demo_password_123', 'neo4j']:
    try:
        driver = GraphDatabase.driver('bolt://127.0.0.1:7688', auth=('neo4j', pwd))
        with driver.session() as session:
            res = session.run('MATCH (n) RETURN count(n) AS count').single()['count']
            rels = session.run('MATCH ()-[r]->() RETURN count(r) AS count').single()['count']
            print(f"SUCCESS with password '{pwd}'! Node count: {res}, Relationship count: {rels}")
            driver.close()
            break
    except Exception as e:
        print(f"Failed password '{pwd}': {e}")

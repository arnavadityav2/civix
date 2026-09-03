import psycopg2
conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
cur = conn.cursor()
from neo4j import GraphDatabase
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
session = driver.session()
print("Identity count:", session.run("MATCH (n:Identity) RETURN count(n)").single())
print("Assertion count:", session.run("MATCH (n:Assertion) RETURN count(n)").single())
print("Event count:", session.run("MATCH (n:Event) RETURN count(n)").single())
print("Edges count:", session.run("MATCH ()-[r]->() RETURN count(r)").single())

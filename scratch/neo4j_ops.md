# Neo4j Acceptance Environment Operations

## START Neo4j
```powershell
# Open a PowerShell terminal
cd "scratch\neo4j\neo4j-community-5.23.0\bin"
.\neo4j.bat console
```
*(Leave the console running, or use `Start-Process ".\neo4j.bat" -ArgumentList "console"` to run it in the background)*

## STOP Neo4j
If running via `console` in a foreground window, simply press `Ctrl+C` to terminate the batch process.
If running in background, you can kill the Java process associated with Neo4j:
```powershell
Stop-Process -Name java -Force
```

## RESET Neo4j TEST DATA
To completely wipe the database (nodes and relationships) without dropping schema constraints, execute this Cypher query through the driver or Neo4j browser:
```cypher
MATCH (n) DETACH DELETE n;
```
*Note: This command safely removes data but leaves the indexes and constraints intact.*

## REAPPLY SCHEMA
If you need to completely drop and recreate the schema, run the provided Python integration script:
```powershell
python scratch\scratch_neo4j_integration.py
```
*(This script executes `database/schema_neo4j.cypher` and verifies constraints).*

## CHECK HEALTH
Run a simple Cypher query to verify responsiveness:
```cypher
RETURN 1 AS health;
```
Or verify the ports using PowerShell:
```powershell
Test-NetConnection -ComputerName localhost -Port 7687
Test-NetConnection -ComputerName localhost -Port 7474
```

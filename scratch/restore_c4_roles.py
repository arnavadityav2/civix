import asyncio
import asyncpg
import uuid

DB_DSN = "postgresql://postgres:postgres@localhost:5433/civix_test"

async def restore():
    conn = await asyncpg.connect(DB_DSN)
    case_id = await conn.fetchval("SELECT case_id FROM civix.investigative_case WHERE title = 'Golden Case 001'")
    if not case_id:
        print("No Golden Case 001 found!")
        await conn.close()
        return

    entities = [
        "Vikram Singh",
        "Neha Gupta",
        "Global Exports Pvt Ltd",
        "Apex Shell Consultants",
        "Rahul Sharma",
        "Drug Trafficking Cartel"
    ]
    
    # Persons
    for name in entities:
        ent_id = await conn.fetchval("SELECT entity_id FROM civix.person WHERE display_name = $1 LIMIT 1", name)
        if ent_id:
            await conn.execute("""
                INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, role_basis)
                VALUES ($1, $2, $3, 'SUSPECT', 'Restored for C4')
                ON CONFLICT DO NOTHING
            """, str(uuid.uuid4()), case_id, ent_id)
            print(f"Restored role for {name}")

    # Orgs
    for name in entities:
        ent_id = await conn.fetchval("SELECT entity_id FROM civix.organization WHERE legal_name = $1 LIMIT 1", name)
        if ent_id:
            await conn.execute("""
                INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, role_basis)
                VALUES ($1, $2, $3, 'SUSPECT', 'Restored for C4')
                ON CONFLICT DO NOTHING
            """, str(uuid.uuid4()), case_id, ent_id)
            print(f"Restored role for {name}")

    # Vehicles
    vehicles = [("Maruti", "Dzire"), ("Toyota", "Fortuner")]
    for make, model in vehicles:
        ent_id = await conn.fetchval("SELECT entity_id FROM civix.vehicle WHERE make = $1 AND model = $2 LIMIT 1", make, model)
        if ent_id:
            await conn.execute("""
                INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, role_basis)
                VALUES ($1, $2, $3, 'SUSPECT', 'Restored for C4')
                ON CONFLICT DO NOTHING
            """, str(uuid.uuid4()), case_id, ent_id)
            print(f"Restored role for {make} {model}")

    await conn.close()
    print("Done")

if __name__ == "__main__":
    asyncio.run(restore())

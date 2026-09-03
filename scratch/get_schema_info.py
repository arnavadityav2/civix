import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect('postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test')
    
    print("--- TRIGGERS ---")
    triggers = await conn.fetch('''
        SELECT event_object_table, trigger_name, action_statement 
        FROM information_schema.triggers 
        WHERE trigger_schema = 'civix';
    ''')
    for t in triggers:
        print(f"Table: {t['event_object_table']}, Trigger: {t['trigger_name']}, Action: {t['action_statement']}")

    print("\n--- TABLES ---")
    tables = await conn.fetch('''
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'civix' AND table_type = 'BASE TABLE';
    ''')
    for t in tables:
        print(t['table_name'])
        
    await conn.close()

asyncio.run(main())

import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:5432/civix_demo')
    rows = await conn.fetch("""
        SELECT 
            c.case_id, 
            c.case_number, 
            c.title, 
            c.jurisdiction,
            ST_X(ST_Centroid(ST_Collect(l.geometry))) as lon, 
            ST_Y(ST_Centroid(ST_Collect(l.geometry))) as lat 
        FROM civix.investigative_case c
        LEFT JOIN civix.event_location el ON el.case_id = c.case_id
        LEFT JOIN civix.location l ON el.location_id = l.entity_id
        WHERE c.case_number NOT LIKE 'SYN-%'
        GROUP BY c.case_id, c.case_number, c.title, c.jurisdiction
        ORDER BY c.case_number;
    """)
    print(f"Total Golden Cases in DB: {len(rows)}")
    for r in rows:
        print(f"- {r['case_number']}: {r['title']} | Lon: {r['lon']}, Lat: {r['lat']}")
    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())

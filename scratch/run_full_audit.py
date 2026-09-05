import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo"

async def generate_audit_report():
    engine = create_async_engine(DB_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    report = ["# CDR & TOWER AUDIT REPORT\\n"]
    
    async with async_session() as session:
        # Database
        report.append("## Database")
        r = await session.execute(text("SELECT COUNT(*) FROM civix.entity WHERE entity_type = 'PHONE_NUMBER'"))
        report.append(f"- **PHONE_NUMBER**: {r.scalar()}")
        r = await session.execute(text("SELECT COUNT(*) FROM civix.entity WHERE entity_type = 'SIM'"))
        report.append(f"- **SIM**: {r.scalar()}")
        r = await session.execute(text("SELECT COUNT(*) FROM civix.entity WHERE entity_type = 'DEVICE'"))
        report.append(f"- **DEVICE**: {r.scalar()}")
        
        # We need to query attributes or specific tables. Oh right, there are specific tables: civix.device, civix.sim
        r = await session.execute(text("SELECT COUNT(DISTINCT imei) FROM civix.device WHERE imei IS NOT NULL"))
        report.append(f"- **IMEI**: {r.scalar()}")
        r = await session.execute(text("SELECT COUNT(DISTINCT imsi) FROM civix.sim WHERE imsi IS NOT NULL"))
        report.append(f"- **IMSI**: {r.scalar()}")
        
        # Events
        report.append("\\n## Events")
        r = await session.execute(text("SELECT event_type, COUNT(*) FROM civix.event WHERE event_type IN ('CALL', 'MESSAGE', 'DEVICE_PING') GROUP BY event_type"))
        events = {row[0]: row[1] for row in r.fetchall()}
        report.append(f"- **CALL**: {events.get('CALL', 0)}")
        report.append(f"- **MESSAGE**: {events.get('MESSAGE', 0)}")
        report.append(f"- **DEVICE_PING**: {events.get('DEVICE_PING', 0)}")
        
        r = await session.execute(text("SELECT COUNT(*) FROM civix.event WHERE event_type IN ('CALL', 'MESSAGE', 'DEVICE_PING')"))
        report.append(f"- **TOTAL**: {r.scalar()}")
        
        # Spatial
        report.append("\\n## Spatial")
        r = await session.execute(text("SELECT location_type, COUNT(*) FROM civix.location GROUP BY location_type"))
        locs = {row[0]: row[1] for row in r.fetchall()}
        report.append(f"- **CELL SECTORS**: {locs.get('CELL_SECTOR_POLYGON', 0)}")
        
        r = await session.execute(text("SELECT COUNT(*) FROM civix.location WHERE location_name ILIKE '%tower%' OR location_name ILIKE '%cell%'"))
        report.append(f"- **TOWERS**: {r.scalar()}")
        
        # Mapped vs Unmapped pings
        r = await session.execute(text("""
            SELECT 
                SUM(CASE WHEN ep.entity_id IS NOT NULL THEN 1 ELSE 0 END) as mapped,
                SUM(CASE WHEN ep.entity_id IS NULL THEN 1 ELSE 0 END) as unmapped
            FROM civix.event e
            LEFT JOIN civix.event_participant ep ON e.event_id = ep.event_id AND ep.participant_role = 'LOCATION'
            WHERE e.event_type = 'DEVICE_PING'
        """))
        mapped, unmapped = r.fetchone()
        report.append(f"- **MAPPED PINGS**: {mapped or 0}")
        report.append(f"- **UNMAPPED PINGS**: {unmapped or 0}")
        
        # Evidence
        report.append("\\n## Evidence")
        # Check source_record for CDR_ROW
        r = await session.execute(text("SELECT COUNT(*) FROM civix.source_record WHERE record_type = 'CDR_ROW'"))
        report.append(f"- **structured CDR records**: {r.scalar()}")
        
        # Cross-case
        report.append("\\n## Cross-case")
        r = await session.execute(text("""
            WITH entity_cases AS (
                SELECT entity_id, COUNT(DISTINCT case_id) as case_count 
                FROM civix.case_entity_role 
                GROUP BY entity_id
            )
            SELECT e.entity_type, COUNT(*) 
            FROM entity_cases ec
            JOIN civix.entity e ON ec.entity_id = e.entity_id
            WHERE ec.case_count > 1 AND e.entity_type IN ('PHONE_NUMBER', 'DEVICE', 'SIM')
            GROUP BY e.entity_type
        """))
        cross = {row[0]: row[1] for row in r.fetchall()}
        report.append(f"- **shared phones**: {cross.get('PHONE_NUMBER', 0)}")
        report.append(f"- **shared devices**: {cross.get('DEVICE', 0)}")
        report.append(f"- **shared SIMs**: {cross.get('SIM', 0)}")
        report.append(f"- **shared IMEIs**: (Pending queries on sim_in_device)")
        report.append(f"- **shared towers**: (Pending queries on event_location)")

        # Analytical capability
        report.append("\\n## Analytical capability")
        report.append("- **CDR Inspector**: BLOCKED (No backend API, Frontend maps to /spatial)")
        report.append("- **Tower Dump**: BLOCKED (No API, no direct tower-to-devices indexing exposed)")
        report.append("- **Co-location**: BLOCKED (No overlap-window API)")
        report.append("- **SIM/IMEI Matrix**: BLOCKED (No aggregation endpoint)")
        report.append("- **Tower Mapping**: PARTIAL (Supported in /spatial but limited to footprints)")
        report.append("- **Cross-case Telecom**: BLOCKED (No explicit cross-case telecom graph query in API)")

    with open(os.path.join(os.path.dirname(__file__), "cdr_tower_audit_report.md"), "w") as f:
        f.write("\\n".join(report))
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(generate_audit_report())

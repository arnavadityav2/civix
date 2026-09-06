import psycopg2
import uuid

# 30 realistic active cell tower sites around Delhi NCR
DELHI_TOWERS = [
    # West Delhi
    ("Cell Tower DWK-23A (Dwarka Sec 23)", 28.5921, 77.0511, 45, 120),
    ("Cell Tower DWK-21B (Dwarka Sec 21 Metro)", 28.5524, 77.0583, 120, 120),
    ("Cell Tower DWK-12C (Dwarka Sec 12 City Center)", 28.5925, 77.0410, 240, 120),
    ("Cell Tower JNK-04A (Janakpuri West Interchange)", 28.6294, 77.0781, 60, 120),
    ("Cell Tower UTM-02B (Uttam Nagar East Hub)", 28.6225, 77.0652, 180, 120),
    ("Cell Tower PLM-01C (Palam Junction BTS)", 28.5833, 77.0850, 300, 120),

    # South Delhi & Airport
    ("Cell Tower IGI-T3A (IGI Airport Terminal 3)", 28.5562, 77.1004, 30, 120),
    ("Cell Tower VSK-08B (Vasant Kunj Promenade)", 28.5391, 77.1567, 150, 120),
    ("Cell Tower HZK-03C (Hauz Khas Village Metro)", 28.5494, 77.2061, 270, 120),
    ("Cell Tower SAK-05A (Saket District Center)", 28.5282, 77.2192, 90, 120),
    ("Cell Tower LJP-02B (Lajpat Nagar Central Market)", 28.5689, 77.2410, 210, 120),

    # Central & North Delhi
    ("Cell Tower CP-01A (Connaught Place Inner Circle)", 28.6315, 77.2197, 0, 120),
    ("Cell Tower BKH-03B (Barakhamba Road Commercial)", 28.6288, 77.2285, 120, 120),
    ("Cell Tower ITO-02C (ITO Administrative Node)", 28.6271, 77.2398, 240, 120),
    ("Cell Tower KB-04A (Karol Bagh Ajmal Khan)", 28.6521, 77.1912, 60, 120),
    ("Cell Tower CC-01B (Chandni Chowk Red Fort)", 28.6562, 77.2325, 180, 120),
    ("Cell Tower KG-02C (Kashmere Gate ISBT)", 28.6675, 77.2281, 300, 120),

    # North-West Delhi
    ("Cell Tower ROH-10A (Rohini Sec 10 District)", 28.7185, 77.1189, 30, 120),
    ("Cell Tower PIT-03B (Pitampura TV Tower Node)", 28.6998, 77.1356, 150, 120),
    ("Cell Tower MT-01C (Model Town Ring Road)", 28.7025, 77.1941, 270, 120),

    # East Delhi & NCR Borders
    ("Cell Tower SHD-02A (Shahdara Junction Node)", 28.6728, 77.2885, 90, 120),
    ("Cell Tower PV-04B (Preet Vihar Vikas Marg)", 28.6412, 77.2971, 210, 120),
    ("Cell Tower IND-01C (Indirapuram Habitat Center)", 28.6385, 77.3612, 330, 120),
    ("Cell Tower NOIDA-18A (Noida Sec 18 Atta Market)", 28.5708, 77.3261, 45, 120),
    ("Cell Tower NOIDA-62B (Noida Sec 62 IT Park)", 28.6254, 77.3689, 165, 120),

    # Gurgaon & Suburbs
    ("Cell Tower GGN-CYB (Gurgaon Cyber City)", 28.4952, 77.0891, 285, 120),
    ("Cell Tower GGN-GC1 (Golf Course Road Sec 54)", 28.4412, 77.1054, 105, 120),
    ("Cell Tower FBD-15A (Faridabad Sec 15 Market)", 28.4089, 77.3195, 225, 120),
    ("Cell Tower BAH-01B (Bahadurgarh Metro Border)", 28.6925, 76.9281, 345, 120),
    ("Cell Tower GNW-02C (Greater Noida West Knowledge Park)", 28.4721, 77.4892, 75, 120),
]

try:
    conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
    cur = conn.cursor()

    inserted_count = 0
    for name, lat, lon, azimuth, beamwidth in DELHI_TOWERS:
        # Check if tower already exists
        cur.execute("SELECT entity_id FROM civix.location WHERE location_name = %s;", (name,))
        if cur.fetchone():
            continue

        loc_id = str(uuid.uuid4())
        # First insert into civix.entity
        cur.execute("""
            INSERT INTO civix.entity (entity_id, entity_type, created_at)
            VALUES (%s, 'LOCATION', NOW())
            ON CONFLICT (entity_id) DO NOTHING;
        """, (loc_id,))

        # Then insert into civix.location
        cur.execute("""
            INSERT INTO civix.location (
                entity_id, location_name, location_type, geometry,
                uncertainty_radius_meters, altitude_meters, azimuth_degrees, beamwidth_degrees
            ) VALUES (
                %s, %s, 'CELL_SECTOR_POLYGON', ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                350.0, 18.0, %s, %s
            );
        """, (loc_id, name, lon, lat, azimuth, beamwidth))
        inserted_count += 1

    conn.commit()
    print(f"Successfully seeded {inserted_count} new active cell towers across Delhi NCR!")

except Exception as e:
    print("Error seeding Delhi cell towers:", e)

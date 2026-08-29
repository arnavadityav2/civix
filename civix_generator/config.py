import datetime
import pytz

# ============================================================================
# CIVIX Synthetic World Generator Config
# ============================================================================

WORLD_VERSION = "2.1"
WORLD_SEED = 20260828
RNG_ALGORITHM = "PCG64"
TIMEZONE = pytz.timezone("Asia/Kolkata")

DATE_START = datetime.datetime(2026, 6, 1, tzinfo=TIMEZONE)
DATE_END = datetime.datetime(2026, 8, 31, 23, 59, 59, tzinfo=TIMEZONE)

EXPECTED_COUNTS = {
    "persons": 55,
    "networks": 3,
    "organizations": 16,
    "phones": 42,
    "vehicles": 13,
    "accounts": 29,
    "properties": 8,
    "devices": 11,
    
    "cdrs": 385,
    "transactions": 50,
    "surveillance_reports": 12,
    "vehicle_sightings": 8,
    "intelligence_reports": 5,
    "criminal_history_records": 6,
    "property_transfers": 3
}

OUTPUT_DIR = "output"

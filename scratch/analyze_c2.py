import asyncio
import asyncpg
import os

async def analyze_c2_rules():
    # 1. Search for C2 rules in the codebase
    print("=== Checking C2 Rules in Python files ===")
    os.system("grep -Rn 'RULE_01_NAME_PHONE' civix_api/services/entity_resolution/")
    os.system("grep -Rn 'RULE_01_NAME_PHONE' civix_api/")
    
    print("\n=== Checking API endpoints for Resolution ===")
    os.system("grep -Rn 'resolve' civix_api/routers/")
    
    print("\n=== Checking Entity Mapper rules for predicates ===")
    os.system("grep -A 10 -Rn 'KNOWN_ASSOCIATE_OF' civix_api/services/nlp/")
    
    print("\n=== Checking Validator for entity type constraints ===")
    os.system("grep -A 20 -Rn 'validate' civix_api/services/nlp/validator.py")

asyncio.run(analyze_c2_rules())

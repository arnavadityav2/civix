from typing import Any
from .models import CanonicalWorld

def validate_canonical_world(world: CanonicalWorld) -> None:
    errors = []
    
    # 1. Validate Expected Counts
    if len(world.persons) != world.expected_counts.get("persons", 55):
        errors.append(f"persons loaded = {len(world.persons)}, expected = {world.expected_counts.get('persons', 55)}")
        
    if len(world.devices) != world.expected_counts.get("devices", 11):
        errors.append(f"devices loaded = {len(world.devices)}, expected = {world.expected_counts.get('devices', 11)}")

    if len(world.properties) != world.expected_counts.get("properties", 8):
        errors.append(f"properties loaded = {len(world.properties)}, expected = {world.expected_counts.get('properties', 8)}")
        
    if len(world.networks) != world.expected_counts.get("networks", 3):
        errors.append(f"networks loaded = {len(world.networks)}, expected = {world.expected_counts.get('networks', 3)}")
        
    if len(world.phones) != world.expected_counts.get("phones", 42):
        errors.append(f"phones loaded = {len(world.phones)}, expected = {world.expected_counts.get('phones', 42)}")
        
    if len(world.vehicles) != world.expected_counts.get("vehicles", 18):
        errors.append(f"vehicles loaded = {len(world.vehicles)}, expected = {world.expected_counts.get('vehicles', 18)}")
        
    if len(world.accounts) != world.expected_counts.get("accounts", 24):
        errors.append(f"accounts loaded = {len(world.accounts)}, expected = {world.expected_counts.get('accounts', 24)}")

    # 2. Cross-reference validation
    for p in world.persons.values():
        for ph in p.phone_ids:
            if ph not in world.phones:
                errors.append(f"Unknown Phone ID '{ph}' referenced by Person '{p.entity_id}'")
        for acc in p.account_ids:
            # check if account is in accounts
            if not any(a.account_id == acc or a.account_number_masked == acc for a in world.accounts.values()):
                errors.append(f"Unknown Account ID '{acc}' referenced by Person '{p.entity_id}'")
        for org in p.organization_ids:
            if org not in world.organizations:
                errors.append(f"Unknown Organization ID '{org}' referenced by Person '{p.entity_id}'")
                
    for dev in world.devices.values():
        if dev.owner_id not in world.persons:
            errors.append(f"Unknown Person ID '{dev.owner_id}' referenced by Device '{dev.device_id}'")
            
    for prop in world.properties.values():
        if prop.true_owner_id not in world.persons:
            errors.append(f"Unknown Person ID '{prop.true_owner_id}' referenced by Property '{prop.property_id}'")
        if prop.location_id not in world.locations:
            errors.append(f"Unknown Location ID '{prop.location_id}' referenced by Property '{prop.property_id}'")
            
    # Check explicitly defined relations
    # e.g., PNB-****8877 is jointly held by P-02 and P-09
    pnb = next((a for a in world.accounts.values() if a.account_number_masked == 'PNB-****8877'), None)
    if not pnb:
        errors.append("Joint account PNB-****8877 not found")
    else:
        holders = [h['person_id'] for h in pnb.holders]
        if 'P-02' not in holders or 'P-09' not in holders:
            errors.append(f"PNB-****8877 missing P-02 or P-09. Found: {holders}")

    if errors:
        print("CanonicalWorldValidationError:")
        for e in errors:
            print(" -", e)
        raise ValueError("Canonical World Validation Failed")
        
    print("Canonical world validation: PASS")

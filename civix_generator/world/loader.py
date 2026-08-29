import os
from .models import (
    CanonicalWorld, WorldMetadata, Person, Network, Organization, 
    PhoneNumber, Device, Vehicle, FinancialAccount, Property, Location,
    Case, FIR, Offence, GenerationRule, AnomalySpecification, FalseLeadSpecification,
    Identity
)
from .parser import parse_markdown_table, parse_persons, extract_json_block, extract_yaml_block
from .validators import validate_canonical_world

def load_canonical_world(filepath: str) -> CanonicalWorld:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    world = CanonicalWorld(
        metadata=WorldMetadata(
            version="2.1",
            world_seed=20260828,
            rng_algorithm="PCG64",
            timezone="Asia/Kolkata",
            date_start="2026-06-01",
            date_end="2026-08-31"
        )
    )
    
    # 1. Expected Counts
    counts = extract_json_block(content, "## 1. The World at a Glance")
    if counts and "expected_record_counts" in counts:
        world.expected_counts = counts["expected_record_counts"]
        
    # 2. Persons
    persons_data = parse_persons(content)
    for row in persons_data:
        pid = row.get("ID", "").strip()
        if not pid: continue
        p = Person(
            entity_id=pid,
            primary_name=row.get("Name", ""),
            role=row.get("Role", "")
        )
        aliases_str = row.get("Aliases", "")
        if aliases_str and aliases_str != "—" and aliases_str != "N/A":
            for alias in [a.strip() for a in aliases_str.split(",")]:
                p.identities.append(Identity(value=alias, identity_type="Alias"))
                
        # Extract embedded identifiers
        phones_str = row.get("Phones", "").strip()
        if phones_str and phones_str != "—" and phones_str != "N/A":
            for part in phones_str.split(','):
                num = part.split('(')[0].replace("**", "").strip()
                if num and num not in world.phones:
                    world.phones[num] = PhoneNumber(entity_id=pid, number=num)
                if num and num not in p.phone_ids:
                    p.phone_ids.append(num)
                    
        vehicle_str = row.get("Vehicle", "").strip()
        if vehicle_str and vehicle_str != "—" and vehicle_str != "N/A":
            for part in vehicle_str.split(';'):
                reg = part.split('—')[0].split('-')[0].replace("**", "").strip().replace(" ", "")
                if reg and reg not in world.vehicles:
                    world.vehicles[reg] = Vehicle(entity_id=pid, registration_number=reg, vehicle_type="Car")
                if reg and reg not in p.vehicle_ids:
                    p.vehicle_ids.append(reg)
                    
        accounts_str = row.get("Accounts", "").strip()
        if accounts_str and accounts_str != "—" and accounts_str != "N/A":
            for part in accounts_str.split(','):
                acc_num = part.split('(')[0].split('UPI')[0].strip()
                if acc_num.startswith('**'):
                    acc_num = acc_num[2:]
                if acc_num.endswith('**'):
                    acc_num = acc_num[:-2]
                acc_num = acc_num.strip()
                if acc_num and acc_num not in world.accounts:
                    world.accounts[acc_num] = FinancialAccount(
                        account_id=f"ACC-{len(world.accounts)+1:03d}",
                        account_number_masked=acc_num,
                        institution="Bank",
                        holders=[]
                    )
                if acc_num and not any(h["person_id"] == pid for h in world.accounts[acc_num].holders):
                    world.accounts[acc_num].holders.append({"person_id": pid, "ownership_type": "primary_holder"})
                if acc_num and acc_num not in p.account_ids:
                    p.account_ids.append(acc_num)
                    
        world.persons[pid] = p

    # 2b. Expand grouped persons (P-34 to P-55)
    for i in range(1, 56):
        pid = f"P-{i:02d}"
        if pid not in world.persons:
            world.persons[pid] = Person(
                entity_id=pid,
                primary_name=f"Background Person {pid}",
                person_type="Civilian",
                role="Background Noise"
            )

    # 3. Organizations
    org_data = parse_markdown_table(content, "## 4. Organizations")
    for row in org_data:
        oid = row.get("ID", "").strip()
        if not oid: continue
        world.organizations[oid] = Organization(
            entity_id=oid,
            name=row.get("Name", ""),
            org_type=row.get("Type", "")
        )
        
    # 4. Networks
    net_data = parse_markdown_table(content, "## 11. Network Entities")
    for row in net_data:
        nid = row.get("Network ID", "").strip()
        if not nid: continue
        world.networks[nid] = Network(
            network_id=nid,
            name=row.get("Name", ""),
            network_type=row.get("Type", ""),
            description=row.get("Description", "")
        )
        
    # (The identifiers are now populated directly from persons)
    
    # 6. Accounts (Ensure Amit/Harish co-ownership explicitly)
    pnb_acc = "PNB-****8877"
    if pnb_acc in world.accounts:
        existing_holders = [h["person_id"] for h in world.accounts[pnb_acc].holders]
        if "P-02" not in existing_holders:
            world.accounts[pnb_acc].holders.append({"person_id": "P-02", "ownership_type": "co_holder"})
            if "P-02" in world.persons and pnb_acc not in world.persons["P-02"].account_ids:
                world.persons["P-02"].account_ids.append(pnb_acc)
        if "P-09" not in existing_holders:
            world.accounts[pnb_acc].holders.append({"person_id": "P-09", "ownership_type": "co_holder"})
            if "P-09" in world.persons and pnb_acc not in world.persons["P-09"].account_ids:
                world.persons["P-09"].account_ids.append(pnb_acc)

    # 8. Locations
    loc_data = parse_markdown_table(content, "## 5. Locations")
    for row in loc_data:
        lid = row.get("ID", "").strip()
        if lid:
            world.locations[lid] = Location(
                entity_id=lid,
                name=row.get("Name", "")
            )

    # 9. Devices
    dev_data = parse_markdown_table(content, "## 14. Devices & SIM History")
    for row in dev_data:
        did = row.get("Device ID", "").strip()
        if not did: continue
        
        # Parse owner ID from the Name (e.g. "Vikram" -> P-01) 
        # This requires some fuzzy logic or assuming we look up by name.
        owner_name = row.get("Owner/User", "").split("(")[0].strip()
        owner_id = None
        for p in world.persons.values():
            if owner_name.lower() in p.primary_name.lower():
                owner_id = p.entity_id
                break
        # Fallback for short names
        if not owner_id:
            for p in world.persons.values():
                if p.primary_name.startswith(owner_name):
                    owner_id = p.entity_id
                    break
                    
        if not owner_id:
            # Set to a generic UNKNOWN if not found, validator will catch it
            owner_id = f"UNKNOWN-{owner_name}"
            
        world.devices[did] = Device(
            device_id=did,
            device_type=row.get("Type", ""),
            imei=row.get("IMEI", ""),
            owner_id=owner_id
        )

    # 10. Properties
    prop_data = parse_markdown_table(content, "## 12. Property Entities")
    for row in prop_data:
        prid = row.get("Property ID", "").strip()
        if not prid: continue
        
        # Extract ID from "Kamla Bai (P-14)" -> "P-14"
        true_owner = row.get("True Owner", "")
        true_owner_id = true_owner.split("(")[-1].replace(")", "").strip() if "(" in true_owner else None
        
        fraud_buyer = row.get("Fraudulent Buyer", "")
        fraud_buyer_id = fraud_buyer.split("(")[-1].replace(")", "").strip() if "(" in fraud_buyer and fraud_buyer != "—" else None
        
        world.properties[prid] = Property(
            property_id=prid,
            property_type=row.get("Type", ""),
            registration_id=row.get("Registration", ""),
            area=row.get("Area", ""),
            location_id=row.get("Location", ""),
            true_owner_id=true_owner_id or "",
            fraudulent_buyer_id=fraud_buyer_id
        )

    # 11. Anomalies
    anomaly_data = parse_markdown_table(content, "## 17. AnomalySignal Specifications")
    for row in anomaly_data:
        sid = row.get("Signal ID", "").strip()
        if sid:
            world.anomalies.append(AnomalySpecification(
                signal_id=sid,
                signal_type=row.get("Type", ""),
                entities=[e.strip() for e in row.get("Entities", "").split(",")],
                baseline=row.get("Baseline", ""),
                observed=row.get("Observed", ""),
                deviation=row.get("Deviation", ""),
                method=row.get("Method", "")
            ))

    # 12. False Leads
    fl_data = parse_markdown_table(content, "## 16. Counter-Evidence")
    for row in fl_data:
        entity = row.get("False Lead Entity", "").strip()
        if entity:
            world.false_leads.append(FalseLeadSpecification(
                false_lead_entity=entity,
                suspicious_signal=row.get("Suspicious Signal (+)", ""),
                counter_evidence=row.get("Counter-Evidence (−)", ""),
                expected_classification=row.get("Result", "")
            ))

    print(f"Persons: {len(world.persons)}")
    print(f"Networks: {len(world.networks)}")
    print(f"Organizations: {len(world.organizations)}")
    print(f"Phones: {len(world.phones)}")
    print(f"Vehicles: {len(world.vehicles)}")
    print(f"Accounts: {len(world.accounts)}")
    print(f"Properties: {len(world.properties)}")
    print(f"Devices: {len(world.devices)}")
    
    validate_canonical_world(world)
    return world

# Ensure this file can be imported properly
__all__ = ['load_canonical_world']

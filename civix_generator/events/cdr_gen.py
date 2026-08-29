import csv
import os
import datetime
from typing import List, Dict, Any
from numpy.random import Generator

from world.models import CanonicalWorld
from lineage.lineage import tracker
from config import OUTPUT_DIR

def generate(world: CanonicalWorld, rng: Generator):
    cdrs = []
    
    start_date = datetime.date.fromisoformat(world.metadata.date_start)
    end_date = datetime.date.fromisoformat(world.metadata.date_end)
    total_days = (end_date - start_date).days + 1
    
    # 1. P-01 (Vikram) and P-02 (Amit) Baseline (~1.2 times/day) and Spike (12 times on Aug 13)
    # We will generate these explicitly.
    vikram = world.persons["P-01"]
    amit = world.persons["P-02"]
    
    vikram_phone = vikram.phone_ids[0] if vikram.phone_ids else "9876543210"
    amit_phone = amit.phone_ids[0] if amit.phone_ids else "9123456789"
    
    # Find their default devices
    vikram_imei = ""
    for d in world.devices.values():
        if d.owner_id == "P-01" and "Burner" not in d.device_id: # simplified check
            vikram_imei = d.imei
            break
            
    amit_imei = ""
    for d in world.devices.values():
        if d.owner_id == "P-02":
            amit_imei = d.imei
            break
            
    # Generate Baseline + Spike
    aug_13 = datetime.date(2026, 8, 13)
    
    for day_offset in range(total_days):
        current_date = start_date + datetime.timedelta(days=day_offset)
        
        if current_date == aug_13:
            num_calls = 12
            is_forced = True
            rule = "Alpha Comm Spike"
        else:
            num_calls = rng.poisson(1.2)
            is_forced = False
            rule = "Alpha Comm Baseline"
            
        for _ in range(num_calls):
            # Random time in the day
            hour = int(rng.integers(8, 23))
            minute = int(rng.integers(0, 59))
            sec = int(rng.integers(0, 59))
            dt = datetime.datetime.combine(current_date, datetime.time(hour, minute, sec))
            duration = int(rng.integers(10, 600))
            
            # Determine direction
            caller, caller_imei, caller_pid = (vikram_phone, vikram_imei, "P-01") if rng.random() > 0.5 else (amit_phone, amit_imei, "P-02")
            receiver, receiver_imei, receiver_pid = (amit_phone, amit_imei, "P-02") if caller_pid == "P-01" else (vikram_phone, vikram_imei, "P-01")
            
            record_id = tracker.add_record(
                source_file="cdr_gen.py",
                generator_module="cdr",
                generation_rule=rule,
                entities=["P-01", "P-02"],
                event_type="cdr",
                is_forced_event=is_forced,
                ground_truth_relevance=["Alpha Comm Spike"] if is_forced else []
            )
            
            cdrs.append({
                "record_id": record_id,
                "timestamp": dt.isoformat(),
                "caller_msisdn": caller,
                "caller_imei": caller_imei,
                "receiver_msisdn": receiver,
                "receiver_imei": receiver_imei,
                "duration_sec": duration,
                "call_type": "Voice",
                "location_cell": "CELL-01"
            })
            
    # 2. SIM Sharing: Bhupendra (P-15) uses Ravi's SIM (9555666777) in DEV-06 between Jun 15 - Jun 28
    # We will generate a few calls during this time to demonstrate this.
    ravi_sim = "9555666777"
    bhupendra_device = "DEV-06"
    bhupendra_imei = world.devices[bhupendra_device].imei if bhupendra_device in world.devices else ""
    
    # We will make Bhupendra call Arjun (P-16) during this time.
    arjun = world.persons.get("P-16")
    arjun_phone = arjun.phone_ids[0] if arjun and arjun.phone_ids else "9888888888"
    arjun_imei = ""
    for d in world.devices.values():
        if d.owner_id == "P-16":
            arjun_imei = d.imei
            break
            
    sim_share_start = datetime.date(2026, 6, 15)
    sim_share_end = datetime.date(2026, 6, 28)
    
    # Generate 5 calls to demonstrate the sharing
    for _ in range(5):
        day_offset = int(rng.integers(0, (sim_share_end - sim_share_start).days))
        current_date = sim_share_start + datetime.timedelta(days=day_offset)
        
        hour = int(rng.integers(9, 21))
        dt = datetime.datetime.combine(current_date, datetime.time(hour, int(rng.integers(0, 59)), 0))
        
        record_id = tracker.add_record(
            source_file="cdr_gen.py",
            generator_module="cdr",
            generation_rule="SIM Sharing",
            entities=["P-15", "P-06"], # Bhupendra using Ravi's SIM
            event_type="cdr",
            is_forced_event=True,
            ground_truth_relevance=["SIM Sharing"]
        )
        
        cdrs.append({
            "record_id": record_id,
            "timestamp": dt.isoformat(),
            "caller_msisdn": ravi_sim,
            "caller_imei": bhupendra_imei, # The anomaly!
            "receiver_msisdn": arjun_phone,
            "receiver_imei": arjun_imei,
            "duration_sec": int(rng.integers(30, 300)),
            "call_type": "Voice",
            "location_cell": "CELL-02"
        })

    # 2b. SIG-08: Periodic communication between Bhupendra (P-15) and Gopal Saini (P-24)
    gopal = world.persons.get("P-24")
    bhupendra = world.persons.get("P-15")
    
    gopal_phone = gopal.phone_ids[0] if gopal and gopal.phone_ids else "9222222222"
    bhup_phone = bhupendra.phone_ids[0] if bhupendra and bhupendra.phone_ids else "9333333333"
    
    gopal_imei = ""
    for d in world.devices.values():
        if d.owner_id == "P-24":
            gopal_imei = d.imei
            break
            
    # Add roughly monthly calls
    periodic_dates = [datetime.date(2026, 6, 12), datetime.date(2026, 7, 14), datetime.date(2026, 8, 11)]
    for d_date in periodic_dates:
        hour = int(rng.integers(10, 18))
        dt = datetime.datetime.combine(d_date, datetime.time(hour, int(rng.integers(0, 59)), 0))
        
        record_id = tracker.add_record(
            source_file="cdr_gen.py",
            generator_module="cdr",
            generation_rule="Periodicity",
            entities=["P-15", "P-24"],
            event_type="cdr",
            is_forced_event=True,
            ground_truth_relevance=["Periodicity"]
        )
        
        cdrs.append({
            "record_id": record_id,
            "timestamp": dt.isoformat(),
            "caller_msisdn": bhup_phone,
            "caller_imei": bhupendra_imei,
            "receiver_msisdn": gopal_phone,
            "receiver_imei": gopal_imei,
            "duration_sec": int(rng.integers(60, 300)),
            "call_type": "Voice",
            "location_cell": "CELL-18"
        })

    # 3. Fill the rest with background noise between random phones to reach exactly 385
    expected_cdrs = world.expected_counts.get("cdrs", 385)
    
    phones = list(world.phones.values())
    
    def get_imei_for_phone(phone_num: str, dt: datetime.date) -> str:
        # Check SIM sharing logic for background calls too
        if phone_num == ravi_sim and sim_share_start <= dt <= sim_share_end:
            return bhupendra_imei
            
        # Find who owns this phone
        owner_id = ""
        for p in world.persons.values():
            if phone_num in p.phone_ids:
                owner_id = p.entity_id
                break
                
        for d in world.devices.values():
            if d.owner_id == owner_id:
                return d.imei
        return "UNKNOWN-IMEI"
        
    while len(cdrs) < expected_cdrs:
        caller = rng.choice(phones)
        receiver = rng.choice(phones)
        if caller.number == receiver.number:
            continue
            
        day_offset = int(rng.integers(0, total_days - 1))
        current_date = start_date + datetime.timedelta(days=day_offset)
        hour = int(rng.integers(6, 23))
        dt = datetime.datetime.combine(current_date, datetime.time(hour, int(rng.integers(0, 59)), 0))
        
        record_id = tracker.add_record(
            source_file="cdr_gen.py",
            generator_module="cdr",
            generation_rule="Background Noise",
            entities=[caller.entity_id, receiver.entity_id],
            event_type="cdr",
            is_forced_event=False
        )
        
        cdrs.append({
            "record_id": record_id,
            "timestamp": dt.isoformat(),
            "caller_msisdn": caller.number,
            "caller_imei": get_imei_for_phone(caller.number, current_date),
            "receiver_msisdn": receiver.number,
            "receiver_imei": get_imei_for_phone(receiver.number, current_date),
            "duration_sec": int(rng.integers(5, 1200)),
            "call_type": "Voice",
            "location_cell": f"CELL-{int(rng.integers(1, 50)):02d}"
        })
        
    # If we exceeded 385 (unlikely due to baseline randomness, but possible if poisson gave > 380), truncate background ones
    if len(cdrs) > expected_cdrs:
        cdrs = cdrs[:expected_cdrs]
        
    # Sort cdrs by timestamp
    cdrs.sort(key=lambda x: x["timestamp"])
    
    # Save to CSV
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "cdrs.csv")
    
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "record_id", "timestamp", "caller_msisdn", "caller_imei", 
            "receiver_msisdn", "receiver_imei", "duration_sec", "call_type", "location_cell"
        ])
        writer.writeheader()
        writer.writerows(cdrs)
        
    return cdrs

import csv
import os
import datetime
from typing import List, Dict, Any
from numpy.random import Generator

from world.models import CanonicalWorld
from lineage.lineage import tracker
from config import OUTPUT_DIR

def generate(world: CanonicalWorld, rng: Generator):
    txs = []
    
    start_date = datetime.date.fromisoformat(world.metadata.date_start)
    end_date = datetime.date.fromisoformat(world.metadata.date_end)
    total_days = (end_date - start_date).days + 1
    
    # Helpers
    def find_account_for_person(pid: str) -> str:
        person = world.persons.get(pid)
        if person and person.account_ids:
            return person.account_ids[0]
        return "UNKNOWN-ACCOUNT"
        
    vikram_acc = find_account_for_person("P-01")
    amit_acc = find_account_for_person("P-02")
    dinesh_acc = find_account_for_person("P-04")
    sunita_acc = find_account_for_person("P-12")
    deepak_acc = find_account_for_person("P-13")
    joint_acc = "PNB-****8877"
    
    def add_tx(rule: str, sender: str, receiver: str, date: datetime.date, amount: float, is_forced: bool, rel: List[str] = None):
        hour = int(rng.integers(9, 17))
        minute = int(rng.integers(0, 59))
        dt = datetime.datetime.combine(date, datetime.time(hour, minute, 0))
        
        # Resolve entity IDs from account IDs for lineage
        entities = []
        for p in world.persons.values():
            if sender in p.account_ids or receiver in p.account_ids:
                entities.append(p.entity_id)
                
        record_id = tracker.add_record(
            source_file="finance_gen.py",
            generator_module="finance",
            generation_rule=rule,
            entities=sorted(list(set(entities))),
            event_type="transaction",
            is_forced_event=is_forced,
            ground_truth_relevance=rel or ([] if not is_forced else [rule])
        )
        
        txs.append({
            "record_id": record_id,
            "timestamp": dt.isoformat(),
            "sender_account": sender,
            "receiver_account": receiver,
            "amount": amount,
            "currency": "INR",
            "transaction_type": "Bank Transfer"
        })

    # 1. Alpha Financial Spike: Aug 10, Vikram transfers exactly 1,50,000 to Amit
    add_tx("Alpha Financial Spike", vikram_acc, amit_acc, datetime.date(2026, 8, 10), 150000.0, True)
    
    # 2. Alpha Financial: Normal transfers Vikram->Amit are 5K-15K
    # Let's generate 5 of these throughout the period
    for _ in range(5):
        day_offset = int(rng.integers(0, total_days - 1))
        current_date = start_date + datetime.timedelta(days=day_offset)
        amt = float(rng.integers(5000, 15000))
        add_tx("Alpha Financial Normal", vikram_acc, amit_acc, current_date, amt, False)
        
    # 3. Cross-Network Finance: Amit transfers money to joint account PNB-****8877
    add_tx("Cross-Network Finance", amit_acc, joint_acc, datetime.date(2026, 6, 22), 200000.0, True)
    add_tx("Cross-Network Finance", amit_acc, joint_acc, datetime.date(2026, 7, 22), 150000.0, True)
    add_tx("Cross-Network Finance", amit_acc, joint_acc, datetime.date(2026, 8, 16), 300000.0, True)
    
    # 4. Corrupt Payments (Alpha): Amit to Dinesh
    add_tx("Corrupt Payments (Alpha)", amit_acc, dinesh_acc, datetime.date(2026, 6, 18), 100000.0, True)
    add_tx("Corrupt Payments (Alpha)", amit_acc, dinesh_acc, datetime.date(2026, 7, 20), 100000.0, True)
    add_tx("Corrupt Payments (Alpha)", amit_acc, dinesh_acc, datetime.date(2026, 8, 13), 125000.0, True)
    
    # 5. Corrupt Payments (Beta): Sunita to Deepak within 72h of every land mutation (there are 3)
    land_mutations = [datetime.date(2026, 6, 10), datetime.date(2026, 7, 12), datetime.date(2026, 8, 5)]
    for lm in land_mutations:
        pay_date = lm + datetime.timedelta(days=int(rng.integers(1, 3)))
        add_tx("Corrupt Payments (Beta)", sunita_acc, deepak_acc, pay_date, 75000.0, True)
        
    # 6. Fill the rest with background noise between random accounts to reach exactly 50
    expected_txs = world.expected_counts.get("transactions", 50)
    
    accounts = list(world.accounts.values())
    
    while len(txs) < expected_txs:
        sender = rng.choice(accounts)
        receiver = rng.choice(accounts)
        if sender.account_id == receiver.account_id:
            continue
            
        day_offset = int(rng.integers(0, total_days - 1))
        current_date = start_date + datetime.timedelta(days=day_offset)
        amt = float(rng.integers(100, 20000))
        
        add_tx("Background Noise", sender.account_number_masked, receiver.account_number_masked, current_date, amt, False)
        
    if len(txs) > expected_txs:
        txs = txs[:expected_txs]
        
    # Sort by timestamp
    txs.sort(key=lambda x: x["timestamp"])
    
    # Save to CSV
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "transactions.csv")
    
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "record_id", "timestamp", "sender_account", "receiver_account", 
            "amount", "currency", "transaction_type"
        ])
        writer.writeheader()
        writer.writerows(txs)
        
    return txs

import json
import os
import datetime
from typing import List, Dict, Any
from numpy.random import Generator

from world.models import CanonicalWorld
from lineage.lineage import tracker
from config import OUTPUT_DIR

def generate(world: CanonicalWorld, rng: Generator):
    reports = []
    
    start_date = datetime.date.fromisoformat(world.metadata.date_start)
    end_date = datetime.date.fromisoformat(world.metadata.date_end)
    total_days = (end_date - start_date).days + 1
    
    def add_intel(rule: str, date: datetime.date, source: str, classification: str, narrative: str, entities: List[str], locations: List[str], cases: List[str], is_forced: bool):
        record_id = tracker.add_record(
            source_file="intelligence_gen.py",
            generator_module="intelligence",
            generation_rule=rule,
            entities=entities,
            event_type="intelligence_report",
            is_forced_event=is_forced,
            ground_truth_relevance=[rule] if is_forced else []
        )
        
        reports.append({
            "report_id": record_id,
            "date": date.isoformat(),
            "source": source,
            "classification": classification,
            "narrative": narrative,
            "entities_mentioned": entities,
            "locations_mentioned": locations,
            "cases_mentioned": cases
        })

    # We can use the false leads from the canonical world to populate intelligence reports
    generated_count = 0
    
    if world.false_leads:
        # Group FL-04 (SI Rakesh Verma) and FL-06 (Rekha Verma) since they both share "Verma" / relate to Amit Verma
        # Or group dynamically based on common keywords. The simplest is to just pair the last two if length > 5
        
        grouped_leads = []
        # Let's put FL-04 (P-30) and FL-06 (P-23) together, or just pair the last two
        i = 0
        while i < len(world.false_leads):
            if i == 3: # Assuming index 3 is FL-04 and index 5 is FL-06, let's just group them by checking IDs
                # Group 4th and 6th? No, let's just group by "Verma"
                vermas = [fl for fl in world.false_leads if "Verma" in fl.false_lead_entity]
                others = [fl for fl in world.false_leads if "Verma" not in fl.false_lead_entity]
                grouped_leads.append(vermas)
                for o in others:
                    grouped_leads.append([o])
                break
            i += 1
            
        if not grouped_leads:
             grouped_leads = [[fl] for fl in world.false_leads]
             
        # Make sure we don't exceed 5
        grouped_leads = grouped_leads[:5]

        for fl_group in grouped_leads:
            day_offset = int(rng.integers(0, total_days - 1))
            current_date = start_date + datetime.timedelta(days=day_offset)
            
            import re
            entities = []
            narratives = []
            for fl in fl_group:
                match = re.search(r'(P-\d+)', fl.false_lead_entity)
                p_id = match.group(1) if match else fl.false_lead_entity
                entities.append(p_id)
                narratives.append(f"Subject {fl.false_lead_entity}: {fl.suspicious_signal}.")
            
            narrative = "Source reports suspicious activity: " + " ".join(narratives)
            
            add_intel(
                "False Lead",
                current_date,
                "Confidential Informant",
                "Secret",
                narrative,
                entities,
                [],
                [],
                False
            )
            generated_count += 1
            
    # Fill the rest
    expected = world.expected_counts.get("intelligence_reports", 5)
    
    persons = list(world.persons.keys())
    
    while len(reports) < expected:
        day_offset = int(rng.integers(0, total_days - 1))
        current_date = start_date + datetime.timedelta(days=day_offset)
        p = rng.choice(persons)
        
        add_intel(
            "Background Intelligence",
            current_date,
            "Anonymous Tip",
            "Restricted",
            f"Anonymous caller claims {world.persons[p].primary_name} is involved in unspecified illicit activities in the area.",
            [p],
            [],
            [],
            False
        )
        
    if len(reports) > expected:
        reports = reports[:expected]
        
    reports.sort(key=lambda x: x["date"])
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "intelligence_reports.json")
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2)
        
    return reports

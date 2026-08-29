from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class Identity:
    value: str
    identity_type: str

@dataclass
class PhoneNumber:
    entity_id: str
    number: str
    status: str = "Active"

@dataclass
class Device:
    device_id: str
    device_type: str
    imei: str
    owner_id: str
    sim_history: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class Vehicle:
    entity_id: str
    registration_number: str
    vehicle_type: str
    make: str = ""
    model: str = ""
    color: str = ""
    year: Optional[int] = None

@dataclass
class FinancialAccount:
    account_id: str
    account_number_masked: str
    institution: str
    holders: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class Address:
    address_id: str
    full_text: str

@dataclass
class Location:
    entity_id: str
    name: str

@dataclass
class Property:
    property_id: str
    property_type: str
    registration_id: str
    area: str
    location_id: str
    true_owner_id: str
    fraudulent_buyer_id: Optional[str]

@dataclass
class Organization:
    entity_id: str
    name: str
    org_type: str

@dataclass
class Network:
    network_id: str
    name: str
    network_type: str
    description: str
    members: List[str] = field(default_factory=list)

@dataclass
class CanonicalRelationship:
    source: str
    target: str
    relationship_type: str
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Person:
    entity_id: str
    primary_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    is_criminal: Optional[bool] = None
    
    # Do not flatten objects! Store relationships or IDs
    identities: List[Identity] = field(default_factory=list)
    phone_ids: List[str] = field(default_factory=list)
    vehicle_ids: List[str] = field(default_factory=list)
    address_ids: List[str] = field(default_factory=list)
    account_ids: List[str] = field(default_factory=list)
    organization_ids: List[str] = field(default_factory=list)
    historical_cases: List[str] = field(default_factory=list)
    current_investigations: List[str] = field(default_factory=list)
    
    role: str = ""
    person_type: str = "Civilian"

@dataclass
class Case:
    entity_id: str
    case_number: str

@dataclass
class FIR:
    entity_id: str
    fir_number: str
    police_station: str
    district: str
    date_filed: str
    crime_type: str

@dataclass
class Offence:
    offence_id: str
    section: str

@dataclass
class GenerationRule:
    rule_id: str
    rule_type: str
    entities: List[str]
    properties: Dict[str, Any] = field(default_factory=dict)
    exact_count: Optional[int] = None
    forced: bool = True

@dataclass
class AnomalySpecification:
    signal_id: str
    signal_type: str
    entities: List[str]
    baseline: str
    observed: str
    deviation: str
    method: str

@dataclass
class FalseLeadSpecification:
    false_lead_entity: str
    suspicious_signal: str
    counter_evidence: str
    expected_classification: str

@dataclass
class WorldMetadata:
    version: str
    world_seed: int
    rng_algorithm: str
    timezone: str
    date_start: str
    date_end: str

@dataclass
class CanonicalWorld:
    metadata: WorldMetadata
    
    persons: Dict[str, Person] = field(default_factory=dict)
    organizations: Dict[str, Organization] = field(default_factory=dict)
    networks: Dict[str, Network] = field(default_factory=dict)
    
    phones: Dict[str, PhoneNumber] = field(default_factory=dict)
    devices: Dict[str, Device] = field(default_factory=dict)
    vehicles: Dict[str, Vehicle] = field(default_factory=dict)
    accounts: Dict[str, FinancialAccount] = field(default_factory=dict)
    
    locations: Dict[str, Location] = field(default_factory=dict)
    addresses: Dict[str, Address] = field(default_factory=dict)
    properties: Dict[str, Property] = field(default_factory=dict)
    
    cases: Dict[str, Case] = field(default_factory=dict)
    firs: Dict[str, FIR] = field(default_factory=dict)
    offences: Dict[str, Offence] = field(default_factory=dict)
    
    relationships: List[CanonicalRelationship] = field(default_factory=list)
    
    deterministic_rules: List[GenerationRule] = field(default_factory=list)
    anomalies: List[AnomalySpecification] = field(default_factory=list)
    false_leads: List[FalseLeadSpecification] = field(default_factory=list)
    
    expected_counts: Dict[str, int] = field(default_factory=dict)

    def get_person(self, person_id: str) -> Person:
        if person_id not in self.persons:
            raise ValueError(f"CanonicalWorldValidationError: Unknown Person ID '{person_id}'")
        return self.persons[person_id]
        
    def get_phone_for_person(self, person_id: str) -> List[PhoneNumber]:
        person = self.get_person(person_id)
        return [self.phones[pid] for pid in person.phone_ids if pid in self.phones]

    def get_device(self, device_id: str) -> Device:
        if device_id not in self.devices:
            raise ValueError(f"CanonicalWorldValidationError: Unknown Device ID '{device_id}'")
        return self.devices[device_id]

    def get_account(self, account_id: str) -> FinancialAccount:
        for acc in self.accounts.values():
            if acc.account_id == account_id or acc.account_number_masked == account_id:
                return acc
        raise ValueError(f"CanonicalWorldValidationError: Unknown Account ID '{account_id}'")

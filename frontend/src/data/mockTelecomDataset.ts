import type {
  TelecomEventItem,
  TelecomTower,
  TelecomEntityItem,
  CoLocationResult
} from '../api/telecom';

// ── FRONTEND-ONLY DEMO DATASET FOR DWARKA SECTOR 23 CASH VAN ROBBERY (CIV-2012-001) ──
// NOTE: Purely frontend demo data. Not ingested into database or backend pipeline.

export interface CommunicationNode {
  id: string;
  label: string;
  sublabel?: string;
  type: 'TARGET' | 'NUMBER' | 'VEHICLE' | 'DEVICE' | 'PERSON';
  callCount?: number;
  strength: 'STRONG' | 'MEDIUM' | 'OTHER';
}

export interface CaseSuspectProfile {
  id: string;
  name: string;
  phone: string;
  role: string;
  roleBadgeColor: string;
  avatarUrl?: string;
  imei: string;
  vehicle?: string;
  callCount24h: number;
  interSuspectCallCount: number;
}

export const DWARKA_SECTOR_23_SUSPECTS: CaseSuspectProfile[] = [
  {
    id: 'ALL_ACCUSED',
    name: '⚡ ALL ACCUSED & SUSPECTS',
    phone: 'CRIME SURGE NETWORK',
    role: 'Inter-Suspect Coordination (4 Suspects)',
    roleBadgeColor: 'bg-red-600 text-white',
    imei: '4 Devices Active',
    vehicle: 'DL 1CV 4821 / DL 3C AW 9012',
    callCount24h: 42,
    interSuspectCallCount: 28,
  },
  {
    id: 'suresh',
    name: 'Suresh Valmiki',
    phone: '+91 98110 92101',
    role: 'Primary Accused / Mastermind',
    roleBadgeColor: 'bg-red-600 text-white',
    imei: '352099001761932',
    vehicle: 'DL 1CV 4821',
    callCount24h: 17,
    interSuspectCallCount: 15,
  },
  {
    id: 'vikram',
    name: 'Vikram Sharma',
    phone: '+91 98710 23455',
    role: 'Co-Accused / Primary Shooter',
    roleBadgeColor: 'bg-orange-600 text-white',
    imei: '354891029384910',
    vehicle: 'DL 1CV 4821',
    callCount24h: 14,
    interSuspectCallCount: 12,
  },
  {
    id: 'rajesh',
    name: 'Rajesh Kumar',
    phone: '+91 98102 77890',
    role: 'Co-Accused / Van Interceptor',
    roleBadgeColor: 'bg-amber-600 text-white',
    imei: '358901298371920',
    vehicle: 'DL 3C AW 9012',
    callCount24h: 9,
    interSuspectCallCount: 7,
  },
  {
    id: 'amit',
    name: 'Amit Verma',
    phone: '+91 98188 44122',
    role: 'Suspect / Getaway Scout',
    roleBadgeColor: 'bg-blue-600 text-white',
    imei: '351982736451920',
    vehicle: 'HR 26 DQ 5511',
    callCount24h: 6,
    interSuspectCallCount: 5,
  },
];

export const getNetworkNodesForSuspect = (suspectId: string): CommunicationNode[] => {
  if (suspectId === 'vikram') {
    return [
      { id: 'v1', label: '+91 98110 92101', sublabel: 'Suresh Valmiki (12 calls)', type: 'PERSON', callCount: 12, strength: 'STRONG' },
      { id: 'v2', label: '+91 98102 77890', sublabel: 'Rajesh Kumar (4 calls)', type: 'PERSON', callCount: 4, strength: 'STRONG' },
      { id: 'v3', label: '+91 98188 44122', sublabel: 'Amit Verma (3 calls)', type: 'PERSON', callCount: 3, strength: 'OTHER' },
      { id: 'v4', label: 'DL 1CV 4821', sublabel: 'White Getaway Van', type: 'VEHICLE', strength: 'STRONG' },
      { id: 'v5', label: 'IMEI: 354891029384910', sublabel: 'Samsung Guru', type: 'DEVICE', strength: 'STRONG' }
    ];
  }
  if (suspectId === 'rajesh') {
    return [
      { id: 'r1', label: '+91 98110 92101', sublabel: 'Suresh Valmiki (5 calls)', type: 'PERSON', callCount: 5, strength: 'STRONG' },
      { id: 'r2', label: '+91 98710 23455', sublabel: 'Vikram Sharma (4 calls)', type: 'PERSON', callCount: 4, strength: 'STRONG' },
      { id: 'r3', label: 'DL 3C AW 9012', sublabel: 'Interceptor SUV', type: 'VEHICLE', strength: 'STRONG' },
      { id: 'r4', label: 'IMEI: 358901298371920', sublabel: 'Nokia 105', type: 'DEVICE', strength: 'STRONG' }
    ];
  }
  if (suspectId === 'amit') {
    return [
      { id: 'a1', label: '+91 98110 92101', sublabel: 'Suresh Valmiki (3 calls)', type: 'PERSON', callCount: 3, strength: 'STRONG' },
      { id: 'a2', label: '+91 98710 23455', sublabel: 'Vikram Sharma (2 calls)', type: 'PERSON', callCount: 2, strength: 'OTHER' },
      { id: 'a3', label: 'HR 26 DQ 5511', sublabel: 'Scout Motorbike', type: 'VEHICLE', strength: 'STRONG' },
      { id: 'a4', label: 'IMEI: 351982736451920', sublabel: 'Lava A1', type: 'DEVICE', strength: 'STRONG' }
    ];
  }
  if (suspectId === 'ALL_ACCUSED') {
    return [
      { id: 'all1', label: 'Suresh Valmiki', sublabel: '+91 98110 92101 (17 calls)', type: 'PERSON', callCount: 17, strength: 'STRONG' },
      { id: 'all2', label: 'Vikram Sharma', sublabel: '+91 98710 23455 (14 calls)', type: 'PERSON', callCount: 14, strength: 'STRONG' },
      { id: 'all3', label: 'Rajesh Kumar', sublabel: '+91 98102 77890 (9 calls)', type: 'PERSON', callCount: 9, strength: 'STRONG' },
      { id: 'all4', label: 'Amit Verma', sublabel: '+91 98188 44122 (6 calls)', type: 'PERSON', callCount: 6, strength: 'STRONG' },
      { id: 'all5', label: 'DL 1CV 4821', sublabel: 'White Cash Van', type: 'VEHICLE', strength: 'STRONG' },
      { id: 'all6', label: '4 Device IMEIs', sublabel: 'Burner Phones Cluster', type: 'DEVICE', strength: 'STRONG' }
    ];
  }

  return DWARKA_SECTOR_23_NETWORK_NODES;
};

export const DWARKA_SECTOR_23_NETWORK_NODES: CommunicationNode[] = [
  { id: 'n1', label: '+91 98710 23455', sublabel: '12 calls', type: 'NUMBER', callCount: 12, strength: 'STRONG' },
  { id: 'n2', label: '+91 98102 77890', sublabel: '5 calls', type: 'NUMBER', callCount: 5, strength: 'STRONG' },
  { id: 'n3', label: '+91 98188 44122', sublabel: '3 calls', type: 'NUMBER', callCount: 3, strength: 'OTHER' },
  { id: 'n4', label: '+91 98177 66543', sublabel: '4 calls', type: 'NUMBER', callCount: 4, strength: 'OTHER' },
  { id: 'n5', label: '+91 98990 11234', sublabel: '2 calls', type: 'NUMBER', callCount: 2, strength: 'OTHER' },
  { id: 'n6', label: 'DL 1CV 4821', sublabel: 'Linked via CDR', type: 'VEHICLE', strength: 'STRONG' },
  { id: 'n7', label: 'IMEI: 352099001761932', sublabel: '2 SIMs', type: 'DEVICE', strength: 'STRONG' }
];

export interface MovementPathPoint {
  towerCode: string;
  timeRange: string;
  lat: number;
  lng: number;
  status: 'START' | 'TRANSIT' | 'INCIDENT_CRITICAL' | 'DESTINATION';
}

export const DWARKA_SECTOR_23_MOVEMENT_PATH: MovementPathPoint[] = [
  { towerCode: 'TOWER-DW-01', timeRange: '15:45 – 16:00', lat: 28.5612, lng: 77.0545, status: 'INCIDENT_CRITICAL' },
  { towerCode: 'TOWER-DW-02', timeRange: '16:15', lat: 28.5638, lng: 77.0582, status: 'TRANSIT' },
  { towerCode: 'TOWER-DW-03', timeRange: '16:25', lat: 28.5521, lng: 77.0594, status: 'TRANSIT' },
  { towerCode: 'TOWER-DW-04', timeRange: '16:35', lat: 28.5721, lng: 77.0651, status: 'DESTINATION' },
  { towerCode: 'TOWER-DW-05', timeRange: '16:30', lat: 28.5689, lng: 77.0712, status: 'TRANSIT' }
];

export interface IntelligenceSignalFinding {
  id: string;
  severity: 'HIGH PRIORITY' | 'MEDIUM PRIORITY' | 'INFO';
  severityColor: string;
  timeRange?: string;
  title: string;
  description: string;
  signalStrengthPct: number;
  badges: string[];
  actionText: string;
  actionType: 'MAP' | 'DETAILS' | 'GRAPH';
}

export const DWARKA_SECTOR_23_FINDINGS: IntelligenceSignalFinding[] = [
  {
    id: 'f1',
    severity: 'HIGH PRIORITY',
    severityColor: 'bg-red-500 text-white',
    timeRange: '02:08 – 02:21',
    title: 'Common tower overlap',
    description: '2 devices observed at TOWER-DW-01 during the incident window.',
    signalStrengthPct: 87,
    badges: ['2 Devices', '1 Tower'],
    actionText: 'View on Map →',
    actionType: 'MAP'
  },
  {
    id: 'f2',
    severity: 'MEDIUM PRIORITY',
    severityColor: 'bg-amber-400 text-black',
    timeRange: '03:12 – 03:28',
    title: 'Possible IMEI reuse',
    description: 'IMEI 352099001761932 appears with multiple SIM cards.',
    signalStrengthPct: 72,
    badges: ['1 IMEI', '2 SIM cards'],
    actionText: 'View Details →',
    actionType: 'DETAILS'
  },
  {
    id: 'f3',
    severity: 'INFO',
    severityColor: 'bg-blue-500 text-white',
    timeRange: '04:05 – 04:32',
    title: 'SIM change detected',
    description: 'Target number used with a different SIM within 24 hours.',
    signalStrengthPct: 64,
    badges: ['1 Number', '2 SIM cards'],
    actionText: 'View Details →',
    actionType: 'DETAILS'
  },
  {
    id: 'f4',
    severity: 'INFO',
    severityColor: 'bg-blue-500 text-white',
    title: 'Cross-case entity',
    description: 'This number is linked to 3 other cases.',
    signalStrengthPct: 52,
    badges: ['3 Cases'],
    actionText: 'View in Graph →',
    actionType: 'GRAPH'
  }
];

export const DWARKA_SECTOR_23_TOWERS: TelecomTower[] = [
  {
    tower_id: 'TOWER-DW-01',
    name: 'TOWER-DW-01 (Dwarka Sector 23 Bank Vault)',
    location_type: 'CELL_SECTOR_POLYGON',
    centroid_lat: 28.5612,
    centroid_lon: 77.0545,
    geometry: null,
    azimuth_degrees: 45,
    beamwidth_degrees: 60,
    uncertainty_radius_meters: 250,
    hit_count: 142,
    call_count: 98,
    ping_count: 44,
    first_observed: '2012-03-13T20:00:00Z',
    last_observed: '2012-03-14T04:30:00Z',
    _note: 'Primary crime scene sector covering Dwarka Sector 23 Bank Vault.'
  },
  {
    tower_id: 'TOWER-DW-02',
    name: 'TOWER-DW-02 (Dwarka Sector 23 Market)',
    location_type: 'CELL_SECTOR_POLYGON',
    centroid_lat: 28.5638,
    centroid_lon: 77.0582,
    geometry: null,
    azimuth_degrees: 120,
    beamwidth_degrees: 60,
    uncertainty_radius_meters: 300,
    hit_count: 89,
    call_count: 62,
    ping_count: 27,
    first_observed: '2012-03-13T18:00:00Z',
    last_observed: '2012-03-14T05:00:00Z',
    _note: 'Recce and assembly point prior to heist.'
  },
  {
    tower_id: 'TOWER-DW-03',
    name: 'TOWER-DW-03 (Dwarka Sector 21 Metro Corridor)',
    location_type: 'CELL_SECTOR_POLYGON',
    centroid_lat: 28.5521,
    centroid_lon: 77.0594,
    geometry: null,
    azimuth_degrees: 210,
    beamwidth_degrees: 60,
    uncertainty_radius_meters: 400,
    hit_count: 65,
    call_count: 41,
    ping_count: 24,
    first_observed: '2012-03-14T02:30:00Z',
    last_observed: '2012-03-14T04:00:00Z',
    _note: 'Secondary getaway transit tower.'
  },
  {
    tower_id: 'TOWER-DW-04',
    name: 'TOWER-DW-04 (Palam Flyover Junction Safehouse)',
    location_type: 'CELL_SECTOR_POLYGON',
    centroid_lat: 28.5721,
    centroid_lon: 77.0651,
    geometry: null,
    azimuth_degrees: 330,
    beamwidth_degrees: 60,
    uncertainty_radius_meters: 350,
    hit_count: 54,
    call_count: 38,
    ping_count: 16,
    first_observed: '2012-03-13T22:00:00Z',
    last_observed: '2012-03-14T06:00:00Z',
    _note: 'Post-heist safehouse hideout.'
  },
  {
    tower_id: 'TOWER-DW-05',
    name: 'TOWER-DW-05 (Najafgarh Outer Ring Road)',
    location_type: 'CELL_SECTOR_POLYGON',
    centroid_lat: 28.5689,
    centroid_lon: 77.0712,
    geometry: null,
    azimuth_degrees: 15,
    beamwidth_degrees: 60,
    uncertainty_radius_meters: 500,
    hit_count: 31,
    call_count: 20,
    ping_count: 11,
    first_observed: '2012-03-14T04:00:00Z',
    last_observed: '2012-03-14T06:00:00Z',
    _note: 'Outer perimeter monitoring point.'
  }
];

export const DWARKA_SECTOR_23_EVENTS: TelecomEventItem[] = [
  {
    event_id: 'f1353f6d-001',
    event_type: 'CALL',
    start: '2012-03-14T15:45:00Z',
    end: '2012-03-14T15:46:55Z',
    duration_seconds: 115,
    description: 'Outgoing Call to +91 98710 23455',
    caller_msisdn: '+91 98110 92101',
    caller_operator: 'Airtel Delhi',
    callee_msisdn: '+91 98710 23455',
    callee_operator: 'Idea Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-01',
    location_name: 'Dwarka Sector 23 Bank Vault',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5612,
    location_lon: 77.0545,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Tower DW-01 lock' }
  },
  {
    event_id: 'f1353f6d-002',
    event_type: 'CALL',
    start: '2012-03-14T16:00:00Z',
    end: '2012-03-14T16:01:25Z',
    duration_seconds: 85,
    description: 'Incoming Call from +91 98102 77890',
    caller_msisdn: '+91 98102 77890',
    caller_operator: 'Vodafone Delhi',
    callee_msisdn: '+91 98110 92101',
    callee_operator: 'Airtel Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-01',
    location_name: 'Dwarka Sector 23 Bank Vault',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5612,
    location_lon: 77.0545,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Tower DW-01 lock' }
  },
  {
    event_id: 'f1353f6d-003',
    event_type: 'CALL',
    start: '2012-03-14T16:05:00Z',
    end: '2012-03-14T16:07:20Z',
    duration_seconds: 140,
    description: 'Incoming Call from +91 98990 11234',
    caller_msisdn: '+91 98990 11234',
    caller_operator: 'Airtel Delhi',
    callee_msisdn: '+91 98110 92101',
    callee_operator: 'Airtel Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-01',
    location_name: 'Dwarka Sector 23 Bank Vault',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5612,
    location_lon: 77.0545,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Tower DW-01 lock' }
  },
  {
    event_id: 'f1353f6d-004',
    event_type: 'CALL',
    start: '2012-03-14T16:15:00Z',
    end: '2012-03-14T16:16:00Z',
    duration_seconds: 60,
    description: 'Incoming Call from +91 98177 66543',
    caller_msisdn: '+91 98177 66543',
    caller_operator: 'Idea Delhi',
    callee_msisdn: '+91 98110 92101',
    callee_operator: 'Airtel Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-02',
    location_name: 'Dwarka Sector 23 Market',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5638,
    location_lon: 77.0582,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Tower DW-02 lock' }
  },
  {
    event_id: 'f1353f6d-005',
    event_type: 'CALL',
    start: '2012-03-14T16:25:00Z',
    end: '2012-03-14T16:25:45Z',
    duration_seconds: 45,
    description: 'Outgoing Call to +91 98188 44122',
    caller_msisdn: '+91 98110 92101',
    caller_operator: 'Airtel Delhi',
    callee_msisdn: '+91 98188 44122',
    callee_operator: 'Airtel Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-03',
    location_name: 'Dwarka Sector 21 Metro Corridor',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5521,
    location_lon: 77.0594,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Tower DW-03 lock' }
  },
  {
    event_id: 'f1353f6d-006',
    event_type: 'CALL',
    start: '2012-03-14T16:32:00Z',
    end: '2012-03-14T16:32:22Z',
    duration_seconds: 22,
    description: 'Outgoing Call to +91 98710 23455',
    caller_msisdn: '+91 98110 92101',
    caller_operator: 'Airtel Delhi',
    callee_msisdn: '+91 98710 23455',
    callee_operator: 'Idea Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-01',
    location_name: 'Dwarka Sector 23 Bank Vault',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5612,
    location_lon: 77.0545,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Tower DW-01 lock' }
  },
  {
    event_id: 'f1353f6d-007',
    event_type: 'CALL',
    start: '2012-03-14T16:33:00Z',
    end: '2012-03-14T16:36:05Z',
    duration_seconds: 185,
    description: 'Incoming Call from +91 98102 77890',
    caller_msisdn: '+91 98102 77890',
    caller_operator: 'Vodafone Delhi',
    callee_msisdn: '+91 98110 92101',
    callee_operator: 'Airtel Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-01',
    location_name: 'Dwarka Sector 23 Bank Vault',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5612,
    location_lon: 77.0545,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Tower DW-01 lock' }
  },
  {
    event_id: 'f1353f6d-008',
    event_type: 'CALL',
    start: '2012-03-14T16:34:00Z',
    end: '2012-03-14T16:36:10Z',
    duration_seconds: 130,
    description: 'Incoming Call from +91 98990 11234',
    caller_msisdn: '+91 98990 11234',
    caller_operator: 'Airtel Delhi',
    callee_msisdn: '+91 98110 92101',
    callee_operator: 'Airtel Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-01',
    location_name: 'Dwarka Sector 23 Bank Vault',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5612,
    location_lon: 77.0545,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Tower DW-01 lock' }
  },
  {
    event_id: 'f1353f6d-009',
    event_type: 'CALL',
    start: '2012-03-14T16:35:00Z',
    end: '2012-03-14T16:35:35Z',
    duration_seconds: 35,
    description: 'Outgoing Call to +91 98177 66543',
    caller_msisdn: '+91 98110 92101',
    caller_operator: 'Airtel Delhi',
    callee_msisdn: '+91 98177 66543',
    callee_operator: 'Idea Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-01',
    location_name: 'Dwarka Sector 23 Bank Vault',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5612,
    location_lon: 77.0545,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Tower DW-01 lock' }
  },
  {
    event_id: 'f1353f6d-010',
    event_type: 'CALL',
    start: '2012-03-14T16:36:00Z',
    end: '2012-03-14T16:40:00Z',
    duration_seconds: 240,
    description: 'Incoming Call from +91 98188 44122',
    caller_msisdn: '+91 98188 44122',
    caller_operator: 'Airtel Delhi',
    callee_msisdn: '+91 98110 92101',
    callee_operator: 'Airtel Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-01',
    location_name: 'Dwarka Sector 23 Bank Vault',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5612,
    location_lon: 77.0545,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Tower DW-01 lock' }
  },
  {
    event_id: 'f1353f6d-011',
    event_type: 'CALL',
    start: '2012-03-14T16:40:00Z',
    end: '2012-03-14T16:41:12Z',
    duration_seconds: 72,
    description: 'Outgoing Call to +91 98710 23455',
    caller_msisdn: '+91 98110 92101',
    caller_operator: 'Airtel Delhi',
    callee_msisdn: '+91 98710 23455',
    callee_operator: 'Idea Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-01',
    location_name: 'Dwarka Sector 23 Bank Vault',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5612,
    location_lon: 77.0545,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Tower DW-01 lock' }
  },
  {
    event_id: 'f1353f6d-012',
    event_type: 'MESSAGE',
    start: '2012-03-14T16:45:00Z',
    end: '2012-03-14T16:45:00Z',
    duration_seconds: 0,
    description: 'Encrypted SMS to +91 98710 23455',
    caller_msisdn: '+91 98110 92101',
    caller_operator: 'Airtel Delhi',
    callee_msisdn: '+91 98710 23455',
    callee_operator: 'Idea Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-04',
    location_name: 'Palam Flyover Junction Safehouse',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5721,
    location_lon: 77.0651,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'SMS log' }
  },
  {
    event_id: 'f1353f6d-013',
    event_type: 'DEVICE_PING',
    start: '2012-03-14T16:48:00Z',
    end: '2012-03-14T16:48:00Z',
    duration_seconds: 0,
    description: 'Location Data Ping at TOWER-DW-04',
    caller_msisdn: null,
    caller_operator: null,
    callee_msisdn: null,
    callee_operator: null,
    subject_msisdn: '+91 98110 92101',
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-04',
    location_name: 'Palam Flyover Junction Safehouse',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5721,
    location_lon: 77.0651,
    source_reference: 'DELHI_TOWER_DUMP_2012',
    source_record_type: 'NETWORK_LOG',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Data ping' }
  },
  {
    event_id: 'f1353f6d-014',
    event_type: 'CALL',
    start: '2012-03-14T16:55:00Z',
    end: '2012-03-14T16:56:40Z',
    duration_seconds: 100,
    description: 'Incoming Call from +91 98710 23455',
    caller_msisdn: '+91 98710 23455',
    caller_operator: 'Idea Delhi',
    callee_msisdn: '+91 98110 92101',
    callee_operator: 'Airtel Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-04',
    location_name: 'Palam Flyover Junction Safehouse',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5721,
    location_lon: 77.0651,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Tower DW-04 lock' }
  },
  {
    event_id: 'f1353f6d-015',
    event_type: 'CALL',
    start: '2012-03-14T17:00:00Z',
    end: '2012-03-14T17:00:50Z',
    duration_seconds: 50,
    description: 'Outgoing Call to +91 98102 77890',
    caller_msisdn: '+91 98110 92101',
    caller_operator: 'Airtel Delhi',
    callee_msisdn: '+91 98102 77890',
    callee_operator: 'Vodafone Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-05',
    location_name: 'Najafgarh Outer Ring Road',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5689,
    location_lon: 77.0712,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Tower DW-05 lock' }
  },
  {
    event_id: 'f1353f6d-016',
    event_type: 'CALL',
    start: '2012-03-14T17:10:00Z',
    end: '2012-03-14T17:11:15Z',
    duration_seconds: 75,
    description: 'Incoming Call from +91 98990 11234',
    caller_msisdn: '+91 98990 11234',
    caller_operator: 'Airtel Delhi',
    callee_msisdn: '+91 98110 92101',
    callee_operator: 'Airtel Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-05',
    location_name: 'Najafgarh Outer Ring Road',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5689,
    location_lon: 77.0712,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Tower DW-05 lock' }
  },
  {
    event_id: 'f1353f6d-017',
    event_type: 'CALL',
    start: '2012-03-14T17:25:00Z',
    end: '2012-03-14T17:27:15Z',
    duration_seconds: 135,
    description: 'Incoming Call from +91 98177 66543',
    caller_msisdn: '+91 98177 66543',
    caller_operator: 'Idea Delhi',
    callee_msisdn: '+91 98110 92101',
    callee_operator: 'Airtel Delhi',
    subject_msisdn: null,
    imei: '352099001761932',
    imsi: null,
    location_id: 'TOWER-DW-05',
    location_name: 'Najafgarh Outer Ring Road',
    location_type: 'CELL_SECTOR_POLYGON',
    location_epistemic_status: 'VERIFIED',
    location_lat: 28.5689,
    location_lon: 77.0712,
    source_reference: 'DELHI_CDR_FEED_2012',
    source_record_type: 'RAW_CDR',
    _data_quality: { imei_available: true, imsi_available: false, sim_available: true, note: 'Tower DW-05 lock' }
  }
];

export const DWARKA_SECTOR_23_ENTITIES: TelecomEntityItem[] = [
  {
    entity_id: 'ent-suresh-valmiki',
    entity_type: 'PHONE_NUMBER',
    identifier: '+91 98110 92101',
    identifier_type: 'MSISDN',
    case_role: 'PRIMARY_ACCUSED',
    msisdn: '+91 98110 92101',
    phone_operator: 'Airtel Delhi',
    country_code: '+91',
    number_type: 'MOBILE',
    imei: '352099001761932',
    device_type: 'SMARTPHONE',
    manufacturer: 'Nokia',
    model: '1100',
    iccid: '8991102910293812938',
    imsi: null,
    issuing_operator: 'Airtel Delhi',
    linked_event_count: 17,
    linked_case_count: 3,
    first_seen: '2012-03-13T21:15:00Z',
    last_seen: '2012-03-14T16:36:00Z'
  },
  {
    entity_id: 'ent-vikram-sharma',
    entity_type: 'PHONE_NUMBER',
    identifier: '+91 98765 43210',
    identifier_type: 'MSISDN',
    case_role: 'CO_ACCUSED_SHOOTER',
    msisdn: '+91 98765 43210',
    phone_operator: 'Idea Delhi',
    country_code: '+91',
    number_type: 'MOBILE',
    imei: '354891029384910',
    device_type: 'FEATURE_PHONE',
    manufacturer: 'Samsung',
    model: 'Guru',
    iccid: '8991204918293810293',
    imsi: null,
    issuing_operator: 'Idea Delhi',
    linked_event_count: 11,
    linked_case_count: 1,
    first_seen: '2012-03-13T22:30:12Z',
    last_seen: '2012-03-14T16:36:00Z'
  }
];

export const DWARKA_SECTOR_23_CO_LOCATIONS: CoLocationResult[] = [
  {
    tower_id: 'TOWER-DW-01',
    tower_name: 'TOWER-DW-01 (Dwarka Sector 23 Bank Vault)',
    msisdn_a: '+91 98110 92101',
    msisdn_b: '+91 98710 23455',
    time_a: '2012-03-14T15:45:00Z',
    time_b: '2012-03-14T15:45:00Z',
    gap_seconds: 0,
    supporting_event_ids: ['f1353f6d-001', 'f1353f6d-006', 'f1353f6d-010'],
    confidence: 'CELL_SECTOR_APPROXIMATION',
    note: '2 devices observed at TOWER-DW-01 during the incident window.'
  }
];

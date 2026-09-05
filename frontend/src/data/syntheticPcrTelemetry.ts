/**
 * CIVIX 2.0 — Synthetic Operational Telemetry Data Layer
 * =======================================================
 * Isolated synthetic data source providing 22 canonical Delhi NCR Police Stations
 * and 108 deterministic PCR Response Units moving along plausible sector routes.
 * 
 * PROVENANCE: SYNTHETIC_OPERATIONAL_TELEMETRY (0% Database / 0% Real Telemetry)
 */

export interface PoliceStationData {
  id: string;
  name: string;
  district: string;
  zone: string;
  lat: number;
  lon: number;
}

export type PcrStatus = 'PATROL' | 'EN ROUTE' | 'AVAILABLE' | 'ON SCENE' | 'RETURNING';

export interface PcrUnit {
  unit_id: string;
  call_id: string;
  assigned_station_id: string;
  assigned_station_name: string;
  district: string;
  status: PcrStatus;
  current_area: string;
  speed_kmh: number;
  route: [number, number][]; // Array of [lat, lon] waypoints
  route_duration_sec: number;
  progress_offset: number; // 0.0 to 1.0 initial progress
  source_type: 'SYNTHETIC_OPERATIONAL_TELEMETRY';
}

// 22 Authoritative Delhi NCR Police Stations (matching CIVIX synthetic world specification)
export const PoliceStations: PoliceStationData[] = [
  { id: 'PS-ROHINI-18', name: 'PS Rohini Sector 18', district: 'North-West Delhi', zone: 'Rohini', lat: 28.7350, lon: 77.1230 },
  { id: 'PS-SHAHDARA', name: 'PS Shahdara', district: 'East Delhi', zone: 'Shahdara', lat: 28.6720, lon: 77.2950 },
  { id: 'PS-DWARKA-23', name: 'PS Dwarka Sector 23', district: 'South-West Delhi', zone: 'Dwarka', lat: 28.5680, lon: 77.0520 },
  { id: 'PS-KAROL-BAGH', name: 'PS Karol Bagh', district: 'Central Delhi', zone: 'Karol Bagh', lat: 28.6510, lon: 77.1910 },
  { id: 'PS-OKHLA-IND', name: 'PS Okhla Industrial Area', district: 'South-East Delhi', zone: 'Okhla', lat: 28.5360, lon: 77.2730 },
  { id: 'PS-IGI-AIRPORT', name: 'PS IGI Airport', district: 'South-West Delhi', zone: 'IGI Airport', lat: 28.5560, lon: 77.0990 },
  { id: 'PS-NIZAMUDDIN', name: 'PS Nizamuddin', district: 'South Delhi', zone: 'South Delhi', lat: 28.5890, lon: 77.2480 },
  { id: 'PS-CHANDNI-CHOWK', name: 'PS Chandni Chowk', district: 'North Delhi', zone: 'Old Delhi', lat: 28.6560, lon: 77.2300 },
  { id: 'PS-ITO', name: 'PS ITO', district: 'Central Delhi', zone: 'ITO Precinct', lat: 28.6290, lon: 77.2410 },
  { id: 'PS-NAJAFGARH', name: 'PS Najafgarh', district: 'Outer West Delhi', zone: 'Najafgarh', lat: 28.6090, lon: 76.9850 },
  { id: 'PS-GURUGRAM-14', name: 'PS Gurugram Sector 14', district: 'Gurugram', zone: 'Gurugram Central', lat: 28.4720, lon: 77.0420 },
  { id: 'PS-DLF-PHASE3', name: 'PS DLF Phase 3', district: 'Gurugram', zone: 'Cyber City', lat: 28.4910, lon: 77.0910 },
  { id: 'PS-CYBER-GURUGRAM', name: 'PS Cyber Crime Gurugram', district: 'Gurugram', zone: 'Gurugram Tech Hub', lat: 28.4590, lon: 77.0260 },
  { id: 'PS-NOIDA-SEC20', name: 'PS Noida Sector 20', district: 'Gautam Buddha Nagar', zone: 'Noida West', lat: 28.5790, lon: 77.3290 },
  { id: 'PS-NOIDA-SEC62', name: 'PS Noida Sector 62', district: 'Gautam Buddha Nagar', zone: 'Noida Electronic City', lat: 28.6250, lon: 77.3620 },
  { id: 'PS-GREATER-NOIDA-KP', name: 'PS Greater Noida Knowledge Park', district: 'Gautam Buddha Nagar', zone: 'Greater Noida', lat: 28.4680, lon: 77.5020 },
  { id: 'PS-SAHIBABAD', name: 'PS Sahibabad', district: 'Ghaziabad', zone: 'Sahibabad Ind.', lat: 28.6710, lon: 77.3640 },
  { id: 'PS-INDIRAPURAM', name: 'PS Indirapuram', district: 'Ghaziabad', zone: 'Indirapuram', lat: 28.6420, lon: 77.3730 },
  { id: 'PS-KAVI-NAGAR', name: 'PS Kavi Nagar', district: 'Ghaziabad', zone: 'Ghaziabad Central', lat: 28.6730, lon: 77.4490 },
  { id: 'PS-FARIDABAD-CENTRAL', name: 'PS Faridabad Central', district: 'Faridabad', zone: 'Faridabad Hub', lat: 28.4080, lon: 77.3170 },
  { id: 'PS-BAHADURGARH-CITY', name: 'PS Bahadurgarh City', district: 'Jhajjar', zone: 'Bahadurgarh Border', lat: 28.6920, lon: 76.9240 },
  { id: 'PS-MANESAR', name: 'PS Manesar', district: 'Gurugram', zone: 'IMT Manesar', lat: 28.3510, lon: 76.9380 }
];

// Helper: Seeded pseudo-random number generator for deterministic stability
function createSeededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
}

// Sub-area names pool by zone for realistic display
const ZONE_SUB_AREAS: Record<string, string[]> = {
  'Rohini': ['Sector 18 Main Road', 'Rohini Sector 15 Flyover', 'Rithala Metro Junction', 'Prashant Vihar Road'],
  'Shahdara': ['Shahdara Grand Trunk Road', 'Mansarovar Park Crossing', 'Dilshad Garden Arterial', 'Seelampur Chowk'],
  'Dwarka': ['Dwarka Sector 21 Complex', 'Sector 23 Market Road', 'Dwarka Expressway Link', 'Barthal Flyover'],
  'Karol Bagh': ['Ajmal Khan Road', 'Pusa Road Junction', 'Karol Bagh Market Circle', 'DB Gupta Road'],
  'Okhla': ['Okhla Phase 3 Main Transit', 'Modi Mill Flyover', 'Maandakini Enclave', 'Govindpuri Extension'],
  'IGI Airport': ['Aerocity Spine Road', 'Terminal 3 Departure Corridor', 'Mahipalpur Bypass', 'Cargo Complex Road'],
  'South Delhi': ['Nizamuddin West Link', 'Lajpat Nagar Ring Road', 'Mathura Road Junction', 'Hazrat Nizamuddin Station'],
  'Old Delhi': ['Chandni Chowk Promenade', 'Red Fort Crossing', 'Kashmere Gate ISBT Link', 'Daryaganj Main'],
  'ITO Precinct': ['ITO Crossing', 'Vikas Marg Arterial', 'Tilak Bridge Link', 'Deen Dayal Upadhyaya Marg'],
  'Najafgarh': ['Najafgarh Main Market', 'Jharoda Kalan Road', 'Dhansa Bus Stand Link', 'Chhawla Stand'],
  'Gurugram Central': ['Sector 14 Old Delhi Road', 'Gurugram Bus Stand Circle', 'MG Road Junction', 'Sheetla Mata Mandir Road'],
  'Cyber City': ['DLF Phase 3 Rapid Metro', 'Cyber Hub Boulevard', 'Moulsari Avenue', 'Golf Course Road Link'],
  'Gurugram Tech Hub': ['Subhash Chowk', 'Sohna Road Expressway', 'Hero Honda Chowk Flyover', 'Sector 33 Commercial'],
  'Noida West': ['Noida Sector 18 Atta Market', 'Sector 20 Police Line', 'Botanical Garden Metro', 'Film City Flyover'],
  'Noida Electronic City': ['Sector 62 Model Town', 'Noida-Greater Noida Expressway Link', 'Fortis Hospital Junction', 'Mamura Chowk'],
  'Greater Noida': ['Knowledge Park II Metro', 'Pari Chowk Flyover', 'Yamuna Expressway Slip Road', 'Omega 1 Commercial'],
  'Sahibabad Ind.': ['Sahibabad Site 4 Industrial Area', 'Mohan Nagar Crossing', 'Link Road Sahibabad', 'Vasundhara Flyover'],
  'Indirapuram': ['Ahinsa Khand 2 Boulevard', 'Shipra Mall Junction', 'Kala Pathar Road', 'CISF Camp Corridor'],
  'Kavi Nagar': ['Kavi Nagar Commercial Circle', 'RDC Raj Nagar Flyover', 'Old Bus Stand Ghaziabad', 'Hapur Road Crossing'],
  'Faridabad Hub': ['Faridabad Sector 12 City Center', 'Mathura Road NH-19 Corridor', 'Bata Chowk Metro', 'Neelam Flyover'],
  'Bahadurgarh Border': ['Bahadurgarh Bypass NH-9', 'City Park Chowk', 'Industrial Area Sector 17', 'Rohtak Road Link'],
  'IMT Manesar': ['Manesar NH-48 Toll Corridor', 'IMT Sector 5 Industrial Link', 'NSG Camp Gate', 'Panchgaon Chowk']
};

const STATUS_WEIGHTS: { status: PcrStatus; weight: number }[] = [
  { status: 'PATROL', weight: 0.35 },
  { status: 'EN ROUTE', weight: 0.25 },
  { status: 'AVAILABLE', weight: 0.20 },
  { status: 'ON SCENE', weight: 0.10 },
  { status: 'RETURNING', weight: 0.10 }
];

// Generate synthetic sector route around station coordinate
function generateRouteWaypoints(centerLat: number, centerLon: number, rand: () => number): [number, number][] {
  const waypoints: [number, number][] = [];
  const radiusLat = 0.012 + rand() * 0.018; // ~1.5km to 3km radius
  const radiusLon = 0.015 + rand() * 0.022;
  const numPoints = 4 + Math.floor(rand() * 3); // 4 to 6 waypoints

  const angleOffset = rand() * Math.PI * 2;
  for (let i = 0; i < numPoints; i++) {
    const angle = angleOffset + (i / numPoints) * Math.PI * 2 + (rand() - 0.5) * 0.3;
    const rLat = radiusLat * (0.8 + rand() * 0.4);
    const rLon = radiusLon * (0.8 + rand() * 0.4);
    const lat = centerLat + Math.sin(angle) * rLat;
    const lon = centerLon + Math.cos(angle) * rLon;
    waypoints.push([Number(lat.toFixed(6)), Number(lon.toFixed(6))]);
  }
  // Close loop
  waypoints.push(waypoints[0]);
  return waypoints;
}

// Generate exactly 108 PCR units deterministically
function generate108PcrUnits(): PcrUnit[] {
  const rand = createSeededRandom(2026);
  const units: PcrUnit[] = [];

  // Distribute 108 units across 22 stations (5 stations get 6 units, 17 get 4-5 units; total = 108)
  const stationCounts = [6, 6, 6, 6, 6, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4]; // sum = 108

  let unitCounter = 1;

  PoliceStations.forEach((station, stIdx) => {
    const count = stationCounts[stIdx];
    const areaList = ZONE_SUB_AREAS[station.zone] || [station.name];

    for (let c = 0; c < count; c++) {
      const unitIdNum = String(unitCounter).padStart(3, '0');
      const unit_id = `PCR-${unitIdNum}`;
      
      // Determine status using weighted seed
      const roll = rand();
      let cum = 0;
      let status: PcrStatus = 'PATROL';
      for (const sw of STATUS_WEIGHTS) {
        cum += sw.weight;
        if (roll <= cum) {
          status = sw.status;
          break;
        }
      }

      // Call ID
      const call_id = (status === 'EN ROUTE' || status === 'ON SCENE') 
        ? `PCR/2026/09/${18000 + unitCounter}`
        : (status === 'PATROL' ? 'PATROL-ACTIVE' : 'STANDBY');

      const current_area = areaList[c % areaList.length];
      const speed_kmh = Math.round(25 + rand() * 30); // 25-55 km/h
      const route = generateRouteWaypoints(station.lat, station.lon, rand);
      const route_duration_sec = 60 + Math.round(rand() * 90); // 60 - 150 seconds per loop
      const progress_offset = Number(rand().toFixed(4));

      units.push({
        unit_id,
        call_id,
        assigned_station_id: station.id,
        assigned_station_name: station.name,
        district: station.district,
        status,
        current_area,
        speed_kmh,
        route,
        route_duration_sec,
        progress_offset,
        source_type: 'SYNTHETIC_OPERATIONAL_TELEMETRY'
      });

      unitCounter++;
    }
  });

  return units;
}

export const SYNTHETIC_PCR_UNITS: PcrUnit[] = generate108PcrUnits();

/**
 * Calculates smooth interpolated position [lat, lon] and direction heading (degrees)
 * for a PCR unit at a specific timestamp.
 */
export function getPcrUnitPosition(unit: PcrUnit, timestampMs: number): { lat: number; lng: number; heading: number } {
  const route = unit.route;
  if (!route || route.length < 2) {
    return { lat: route[0][0], lng: route[0][1], heading: 0 };
  }

  const durationMs = unit.route_duration_sec * 1000;
  const elapsedMs = (timestampMs + unit.progress_offset * durationMs) % durationMs;
  const totalProgress = elapsedMs / durationMs; // 0.0 to 1.0

  const segmentCount = route.length - 1;
  const scaledProgress = totalProgress * segmentCount;
  const segmentIndex = Math.floor(scaledProgress) % segmentCount;
  const segmentProgress = scaledProgress - Math.floor(scaledProgress);

  const p1 = route[segmentIndex];
  const p2 = route[(segmentIndex + 1) % route.length];

  const lat = p1[0] + (p2[0] - p1[0]) * segmentProgress;
  const lng = p1[1] + (p2[1] - p1[1]) * segmentProgress;

  // Calculate heading direction angle
  const dLat = p2[0] - p1[0];
  const dLng = p2[1] - p1[1];
  const heading = Math.atan2(dLng, dLat) * (180 / Math.PI);

  return { lat, lng, heading };
}

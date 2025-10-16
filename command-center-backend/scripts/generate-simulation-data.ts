#!/usr/bin/env node
import { EventItem, Domain, Severity } from '../lib/types/database';
import * as crypto from 'crypto';

/**
 * Generate simulation data for 7-day earthquake response timeline
 * This script creates diverse events across all domains with realistic timestamps and GeoJSON geometries
 */

// Turkey earthquake epicenter (Kahramanmaraş region)
const EPICENTER = { lat: 37.226, lon: 37.014 };

// Cities affected by the earthquake
const AFFECTED_CITIES = [
  { name: 'Kahramanmaraş', lat: 37.5847, lon: 36.9228 },
  { name: 'Gaziantep', lat: 37.0662, lon: 37.3833 },
  { name: 'Hatay', lat: 36.4018, lon: 36.3498 },
  { name: 'Adıyaman', lat: 37.7648, lon: 38.2786 },
  { name: 'Malatya', lat: 38.3552, lon: 38.3095 },
  { name: 'Şanlıurfa', lat: 37.1591, lon: 38.7969 },
  { name: 'Diyarbakır', lat: 37.9144, lon: 40.2306 },
  { name: 'Osmaniye', lat: 37.0742, lon: 36.2478 },
  { name: 'Adana', lat: 37.0000, lon: 35.3213 },
  { name: 'Kilis', lat: 36.7184, lon: 37.1212 }
];

// Event templates for each domain
const EVENT_TEMPLATES = {
  MEDICAL: [
    { summary: 'Field hospital established', severity: 'HIGH', resources: ['MEDICAL_STAFF', 'MEDICAL_SUPPLIES'] },
    { summary: 'Mass casualty triage point', severity: 'CRITICAL', resources: ['MEDICAL_STAFF', 'AMBULANCES'] },
    { summary: 'Mobile clinic deployed', severity: 'MEDIUM', resources: ['MEDICAL_STAFF', 'MEDICAL_SUPPLIES'] },
    { summary: 'Blood donation center', severity: 'HIGH', resources: ['MEDICAL_STAFF', 'BLOOD_SUPPLIES'] },
    { summary: 'Injured civilians requiring evacuation', severity: 'CRITICAL', resources: ['AMBULANCES', 'HELICOPTERS'] },
    { summary: 'Pharmacy distribution point', severity: 'MEDIUM', resources: ['MEDICAL_SUPPLIES'] },
    { summary: 'Mental health support station', severity: 'LOW', resources: ['COUNSELORS'] }
  ],
  FIRE: [
    { summary: 'Building fire from gas leak', severity: 'CRITICAL', resources: ['FIRE_TRUCKS', 'FIREFIGHTERS'] },
    { summary: 'Search and rescue operation', severity: 'CRITICAL', resources: ['RESCUE_TEAMS', 'EQUIPMENT'] },
    { summary: 'Gas line rupture contained', severity: 'HIGH', resources: ['FIRE_TRUCKS', 'ENGINEERS'] },
    { summary: 'Hazmat situation - chemical spill', severity: 'HIGH', resources: ['HAZMAT_TEAMS', 'EQUIPMENT'] },
    { summary: 'Fire suppression completed', severity: 'MEDIUM', resources: [] }
  ],
  STRUCTURAL: [
    { summary: 'Building collapse - active rescue', severity: 'CRITICAL', resources: ['RESCUE_TEAMS', 'HEAVY_EQUIPMENT'] },
    { summary: 'Structural assessment in progress', severity: 'HIGH', resources: ['ENGINEERS', 'EQUIPMENT'] },
    { summary: 'Bridge damage reported', severity: 'HIGH', resources: ['ENGINEERS', 'HEAVY_EQUIPMENT'] },
    { summary: 'Building marked unsafe - evacuation', severity: 'MEDIUM', resources: ['ENGINEERS'] },
    { summary: 'Road cleared of debris', severity: 'LOW', resources: ['HEAVY_EQUIPMENT'] },
    { summary: 'Temporary shelter erected', severity: 'MEDIUM', resources: ['CONSTRUCTION_MATERIALS', 'WORKERS'] }
  ],
  LOGISTICS: [
    { summary: 'Food distribution center', severity: 'HIGH', resources: ['FOOD_SUPPLIES', 'VOLUNTEERS'] },
    { summary: 'Water purification station', severity: 'CRITICAL', resources: ['WATER_SUPPLIES', 'EQUIPMENT'] },
    { summary: 'Supply depot established', severity: 'MEDIUM', resources: ['STORAGE', 'VOLUNTEERS'] },
    { summary: 'Fuel distribution point', severity: 'HIGH', resources: ['FUEL', 'SECURITY'] },
    { summary: 'Clothing and blanket distribution', severity: 'MEDIUM', resources: ['SUPPLIES', 'VOLUNTEERS'] },
    { summary: 'Generator deployed', severity: 'HIGH', resources: ['GENERATORS', 'FUEL'] },
    { summary: 'Donation collection point', severity: 'LOW', resources: ['VOLUNTEERS', 'STORAGE'] }
  ],
  COMMUNICATION: [
    { summary: 'Mobile cell tower deployed', severity: 'HIGH', resources: ['EQUIPMENT', 'TECHNICIANS'] },
    { summary: 'Satellite communication hub', severity: 'CRITICAL', resources: ['SATELLITE_EQUIPMENT', 'TECHNICIANS'] },
    { summary: 'Radio relay station established', severity: 'MEDIUM', resources: ['RADIO_EQUIPMENT', 'OPERATORS'] },
    { summary: 'Internet connectivity restored', severity: 'LOW', resources: ['TECHNICIANS', 'EQUIPMENT'] },
    { summary: 'Emergency broadcast system active', severity: 'HIGH', resources: ['BROADCAST_EQUIPMENT', 'OPERATORS'] }
  ]
};

/**
 * Generate a random point within a radius of a location
 */
function randomPointNear(center: { lat: number; lon: number }, radiusKm: number): { lat: number; lon: number } {
  const radiusInDegrees = radiusKm / 111; // Rough conversion
  const angle = Math.random() * 2 * Math.PI;
  const distance = Math.random() * radiusInDegrees;
  
  return {
    lat: center.lat + distance * Math.cos(angle),
    lon: center.lon + distance * Math.sin(angle)
  };
}

/**
 * Generate GeoJSON for a point
 */
function generatePointGeoJSON(location: { lat: number; lon: number }): string {
  return JSON.stringify({
    type: 'Point',
    coordinates: [location.lon, location.lat]
  });
}

/**
 * Generate GeoJSON for a polygon (circular area)
 */
function generatePolygonGeoJSON(center: { lat: number; lon: number }, radiusKm: number): string {
  const points = 16;
  const coordinates: number[][] = [];
  const radiusInDegrees = radiusKm / 111;
  
  for (let i = 0; i <= points; i++) {
    const angle = (i / points) * 2 * Math.PI;
    const lat = center.lat + radiusInDegrees * Math.cos(angle);
    const lon = center.lon + radiusInDegrees * Math.sin(angle);
    coordinates.push([lon, lat]);
  }
  
  return JSON.stringify({
    type: 'Polygon',
    coordinates: [coordinates]
  });
}

/**
 * Generate a UUID
 */
function generateUUID(): string {
  return crypto.randomUUID();
}

/**
 * Generate timestamp for a specific day and hour with unique precision
 */
function generateTimestamp(day: number, hour: number, minute: number = 0, second: number = 0, millisecond: number = 0): string {
  // Start date: February 6, 2023 (earthquake date)
  const baseDate = new Date('2023-02-06T00:00:00Z');
  baseDate.setDate(baseDate.getDate() + day);
  baseDate.setHours(hour, minute, second, millisecond);
  return baseDate.toISOString();
}

/**
 * Generate events for a specific domain and day
 */
function generateEventsForDomain(
  domain: Domain,
  day: number,
  eventsPerDay: number
): EventItem[] {
  const events: EventItem[] = [];
  const templates = EVENT_TEMPLATES[domain];
  
  for (let i = 0; i < eventsPerDay; i++) {
    const template = templates[Math.floor(Math.random() * templates.length)];
    const city = AFFECTED_CITIES[Math.floor(Math.random() * AFFECTED_CITIES.length)];
    const location = randomPointNear(city, 5); // Within 5km of city center
    
    // Distribute events throughout the day with unique timestamps
    const hour = Math.floor((i / eventsPerDay) * 24);
    const minute = Math.floor(Math.random() * 60);
    const second = Math.floor(Math.random() * 60);
    const millisecond = Math.floor(Math.random() * 1000);
    
    // Use polygon for area-based events, point for specific locations
    const usePolygon = Math.random() > 0.7 && ['STRUCTURAL', 'LOGISTICS'].includes(domain);
    const geojson = usePolygon 
      ? generatePolygonGeoJSON(location, 0.5) // 500m radius
      : generatePointGeoJSON(location);
    
    const event: EventItem = {
      Day: `DAY_${day}`,
      Timestamp: generateTimestamp(day, hour, minute, second, millisecond),
      eventId: generateUUID(),
      domain,
      severity: template.severity as Severity,
      geojson,
      summary: `${template.summary} - ${city.name}`,
      details: `${template.summary} at ${city.name}. Coordinates: ${location.lat.toFixed(4)}, ${location.lon.toFixed(4)}`,
      resourcesNeeded: template.resources.length > 0 ? template.resources : undefined,
      contactInfo: Math.random() > 0.5 ? `Contact: +90-${Math.floor(Math.random() * 900 + 100)}-${Math.floor(Math.random() * 9000 + 1000)}` : undefined
    };
    
    events.push(event);
  }
  
  return events;
}

/**
 * Generate all simulation data for 7 days
 */
export function generateSimulationData(): EventItem[] {
  const allEvents: EventItem[] = [];
  const domains: Domain[] = ['MEDICAL', 'FIRE', 'STRUCTURAL', 'LOGISTICS', 'COMMUNICATION'];
  
  // Event distribution: More events in early days, tapering off
  const eventsPerDayByDomain = [
    { day: 0, perDomain: 15 }, // Day 0: Earthquake day - most events
    { day: 1, perDomain: 12 }, // Day 1: High activity
    { day: 2, perDomain: 10 }, // Day 2: Still high
    { day: 3, perDomain: 8 },  // Day 3: Moderate
    { day: 4, perDomain: 6 },  // Day 4: Decreasing
    { day: 5, perDomain: 5 },  // Day 5: Lower
    { day: 6, perDomain: 4 }   // Day 6: Stabilizing
  ];
  
  for (const { day, perDomain } of eventsPerDayByDomain) {
    for (const domain of domains) {
      const events = generateEventsForDomain(domain, day, perDomain);
      allEvents.push(...events);
    }
  }
  
  // Sort by timestamp
  allEvents.sort((a, b) => a.Timestamp.localeCompare(b.Timestamp));
  
  console.log(`Generated ${allEvents.length} events across 7 days`);
  console.log(`Events per domain:`);
  domains.forEach(domain => {
    const count = allEvents.filter(e => e.domain === domain).length;
    console.log(`  ${domain}: ${count}`);
  });
  
  return allEvents;
}

// If run directly, generate and output data
if (require.main === module) {
  const events = generateSimulationData();
  console.log('\nSample events:');
  console.log(JSON.stringify(events.slice(0, 3), null, 2));
}

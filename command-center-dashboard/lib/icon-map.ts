// Icon Contract - Single source of truth for all map icons
import {
    Building2, HeartPulse, Flame, Car, Biohazard, UserSearch, // Incidents
    Users, Ambulance, Construction, Wrench, Soup, Droplets, Stethoscope, HeartHandshake, // Resources
    Hospital, Tent, Info, Signal, HelpCircle, // Locations & Default
    AlertTriangle, MapPin, Ban // Additional
} from 'lucide-react';

/**
 * The Icon Contract.
 * This is the single source of truth for all map icons. The AI Agent must
 * use one of the keys from this object. The client uses the key to look up
 * the corresponding React component.
 */
export const IconLibrary = {
    // --- Incidents & Hazards ---
    BUILDING_COLLAPSE: Building2,
    MEDICAL_EMERGENCY: HeartPulse,
    FIRE_HAZARD: Flame,
    ROAD_BLOCKED: Ban,
    PUBLIC_HEALTH_RISK: Biohazard,
    MISSING_PERSON: UserSearch,

    // --- Resources & Assets ---
    RESCUE_TEAM: Users,
    AMBULANCE: Ambulance,
    HEAVY_MACHINERY: Construction,
    EQUIPMENT_LIGHT: Wrench,
    FOOD_SUPPLY: Soup,
    WATER_SUPPLY: Droplets,
    MEDICAL_SUPPLY: Stethoscope,
    DONATION_POINT: HeartHandshake,

    // --- Infrastructure & Locations ---
    HOSPITAL: Hospital,
    SHELTER_CAMP: Tent,
    INFO_POINT: Info,
    COMMUNICATION_TOWER: Signal,

    // --- Additional Common Icons ---
    ALERT: AlertTriangle,
    LOCATION: MapPin,

    // --- Default Fallback ---
    UNKNOWN: HelpCircle,

    // Legacy support for simple names
    error: AlertTriangle,
    food_pantry: Soup,
    hospital: Hospital,
};

export type IconKey = keyof typeof IconLibrary;

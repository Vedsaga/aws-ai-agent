/**
 * Category Configuration
 * Defines colors, icons, and styling for different incident categories
 */

export interface CategoryColors {
  bg: string;
  border: string;
  icon: string;
}

export const CATEGORY_COLORS: Record<string, CategoryColors> = {
  pothole: {
    bg: '#EF4444',      // Red
    border: '#DC2626',
    icon: '🕳️'
  },
  street_light: {
    bg: '#F59E0B',      // Amber
    border: '#D97706',
    icon: '💡'
  },
  sidewalk: {
    bg: '#8B5CF6',      // Purple
    border: '#7C3AED',
    icon: '🚶'
  },
  trash: {
    bg: '#10B981',      // Green
    border: '#059669',
    icon: '🗑️'
  },
  flooding: {
    bg: '#3B82F6',      // Blue
    border: '#2563EB',
    icon: '🌊'
  },
  fire: {
    bg: '#DC2626',      // Dark Red
    border: '#991B1B',
    icon: '🔥'
  },
  default: {
    bg: '#6B7280',      // Gray
    border: '#4B5563',
    icon: '📍'
  }
};

export const SEVERITY_COLORS: Record<string, string> = {
  critical: '#DC2626',  // Red
  high: '#F59E0B',      // Amber
  medium: '#F59E0B',    // Yellow
  low: '#10B981',       // Green
};

/**
 * Get category colors with fallback to default
 */
export function getCategoryColors(category?: string): CategoryColors {
  if (!category) return CATEGORY_COLORS.default;
  
  const normalizedCategory = category.toLowerCase().replace(/\s+/g, '_');
  return CATEGORY_COLORS[normalizedCategory] || CATEGORY_COLORS.default;
}

/**
 * Get severity color with fallback
 */
export function getSeverityColor(severity?: string): string {
  if (!severity) return SEVERITY_COLORS.medium;
  
  const normalizedSeverity = severity.toLowerCase();
  return SEVERITY_COLORS[normalizedSeverity] || SEVERITY_COLORS.medium;
}

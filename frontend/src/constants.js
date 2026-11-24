// Shared colours, labels and small helpers (colours match the mockups)

// same values as --color-risk-* in index.css
export const RISK_COLORS = {
  low: '#3f9d63',
  medium: '#d4a72c',
  high: '#e07b28',
  very_high: '#cf3b3b',
}
export const RISK_LABELS = { low: 'Low', medium: 'Medium', high: 'High', very_high: 'Very high' }
export const RISK_CLASSES = ['low', 'medium', 'high', 'very_high']

// safety slider presets (lambda in the route cost)
export const SAFETY_STEPS = [
  { value: 0, label: 'Fastest' },
  { value: 2, label: 'Balanced' },
  { value: 5, label: 'Safe' },
  { value: 10, label: 'Safest' },
]

export const CHAMOLI_CENTER = [30.45, 79.45]

export const POI_COLORS = { hospital: '#b4413a', clinic: '#c9706a', police: '#2c4a6b', fuel: '#71717a' }
export const POI_LABELS = { hospital: 'Hospital', clinic: 'Clinic', police: 'Police', fuel: 'Fuel' }

export const REPORT_TYPES = [
  { value: 'landslide', label: 'Landslide' },
  { value: 'debris', label: 'Debris / rockfall on road' },
  { value: 'road_blocked', label: 'Road blocked' },
  { value: 'flooding', label: 'Flooding / washout' },
  { value: 'other', label: 'Other' },
]

export const FACTOR_LABELS = {
  susceptibility: 'Landslide susceptibility',
  landslide_density: 'Past landslides nearby',
  terrain_slope: 'Terrain slope',
  curvature: 'Road bends',
  accident_density: 'Accidents',
}

export const EMERGENCY_NUMBERS = [
  { number: '112', label: 'Emergency' },
  { number: '108', label: 'Ambulance' },
  { number: '1070', label: 'Disaster helpline' },
]

export function fmtTime(minutes) {
  const h = Math.floor(minutes / 60)
  const m = Math.round(minutes % 60)
  return h ? `${h} h ${m} min` : `${m} min`
}

export function fmtKm(km) {
  return km >= 10 ? `${km.toFixed(0)} km` : `${km.toFixed(1)} km`
}

export function riskClass(r) {
  return r < 0.25 ? 'low' : r < 0.5 ? 'medium' : r < 0.75 ? 'high' : 'very_high'
}

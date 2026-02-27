export interface Enrichment {
  avg_rent_area: number | null
  population_density: number | null
  commercial_density: number | null
  transport_score: number | null
  liquidity_score: number | null
  accessibility_score: number | null
  vertical_storage_potential: number | null
  price_per_sqm: number | null
  estimated_rent_low: number | null
  estimated_rent_high: number | null
  gross_yield: number | null
  storage_yield_estimate: number | null
  ml_estimated_price: number | null
  ml_price_deviation: number | null
  edge_score: number | null
  computed_at: string | null
}

export interface Listing {
  id: string
  source: string
  external_id: string | null
  url: string | null
  title: string
  description: string | null
  price: number
  surface: number | null
  city: string | null
  postal_code: string | null
  address: string | null
  photos_count: number
  floor_level: number | null
  accessibility_tags: string[]
  lat: number | null
  lon: number | null
  scraped_at: string
  updated_at: string
  enrichment: Enrichment | null
}

export interface ListingsPage {
  total: number
  items: Listing[]
}

export interface GeoFeatureProperties {
  id: string
  title: string
  price: number
  surface: number | null
  city: string | null
  url: string | null
  edge_score: number | null
  gross_yield: number | null
  price_per_sqm: number | null
}

export interface GeoFeature {
  type: 'Feature'
  geometry: { type: 'Point'; coordinates: [number, number] }
  properties: GeoFeatureProperties
}

export interface GeoJSON {
  type: 'FeatureCollection'
  features: GeoFeature[]
}

export interface DashboardSummary {
  total_listings: number
  enriched_listings: number
  avg_edge_score: number | null
  avg_gross_yield: number | null
  avg_price: number | null
  top_cities: { city: string; count: number }[]
}

export interface TopOpportunity {
  id: string
  title: string
  city: string | null
  price: number
  surface: number | null
  gross_yield: number | null
  edge_score: number
  url: string | null
}

export interface Filters {
  city: string
  minPrice: number | null
  maxPrice: number | null
  minSurface: number | null
  maxSurface: number | null
  minYield: number | null
  minEdge: number | null
}

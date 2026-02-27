import axios from 'axios'
import type {
  DashboardSummary,
  Filters,
  GeoJSON,
  Listing,
  ListingsPage,
  TopOpportunity,
} from '@/types/listing'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

export function buildListingParams(filters: Filters, page = 0, limit = 50) {
  const params: Record<string, string | number> = { limit, offset: page * limit }
  if (filters.city) params.city = filters.city
  if (filters.minPrice != null) params.min_price = filters.minPrice
  if (filters.maxPrice != null) params.max_price = filters.maxPrice
  if (filters.minSurface != null) params.min_surface = filters.minSurface
  if (filters.maxSurface != null) params.max_surface = filters.maxSurface
  if (filters.minYield != null) params.min_yield = filters.minYield
  if (filters.minEdge != null) params.min_edge = filters.minEdge
  return params
}

export const apiClient = {
  getListings: (filters: Filters, page?: number, limit?: number) =>
    api.get<ListingsPage>('/listings', { params: buildListingParams(filters, page, limit) }).then(r => r.data),

  getGeoJSON: (filters: Filters) =>
    api.get<GeoJSON>('/listings/geojson', {
      params: {
        ...(filters.city && { city: filters.city }),
        ...(filters.minEdge != null && { min_edge: filters.minEdge }),
      },
    }).then(r => r.data),

  getListing: (id: string) =>
    api.get<Listing>(`/listings/${id}`).then(r => r.data),

  getSummary: () =>
    api.get<DashboardSummary>('/analytics/summary').then(r => r.data),

  getTopOpportunities: (limit = 20) =>
    api.get<TopOpportunity[]>('/analytics/top', { params: { limit } }).then(r => r.data),

  triggerMockIngest: () =>
    api.post('/jobs/ingest-mock').then(r => r.data),

  triggerEnrich: () =>
    api.post('/jobs/enrich').then(r => r.data),

  triggerTrainML: () =>
    api.post('/jobs/train-ml').then(r => r.data),
}

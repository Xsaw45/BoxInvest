import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { useFiltersStore } from '@/stores/useFiltersStore'

export function useListings(page = 0) {
  const { filters } = useFiltersStore()
  return useQuery({
    queryKey: ['listings', filters, page],
    queryFn: () => apiClient.getListings(filters, page),
    staleTime: 60_000,
  })
}

export function useGeoJSON() {
  const { filters } = useFiltersStore()
  return useQuery({
    queryKey: ['geojson', filters],
    queryFn: () => apiClient.getGeoJSON(filters),
    staleTime: 60_000,
  })
}

export function useSummary() {
  return useQuery({
    queryKey: ['summary'],
    queryFn: apiClient.getSummary,
    staleTime: 120_000,
  })
}

export function useTopOpportunities() {
  return useQuery({
    queryKey: ['top-opportunities'],
    queryFn: () => apiClient.getTopOpportunities(10),
    staleTime: 120_000,
  })
}

export function useListing(id: string | null) {
  return useQuery({
    queryKey: ['listing', id],
    queryFn: () => apiClient.getListing(id!),
    enabled: !!id,
    staleTime: 300_000,
  })
}

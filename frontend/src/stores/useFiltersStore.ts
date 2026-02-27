import { create } from 'zustand'
import type { Filters } from '@/types/listing'

interface FiltersStore {
  filters: Filters
  setFilter: <K extends keyof Filters>(key: K, value: Filters[K]) => void
  resetFilters: () => void
}

const DEFAULT_FILTERS: Filters = {
  city: '',
  minPrice: null,
  maxPrice: null,
  minSurface: null,
  maxSurface: null,
  minYield: null,
  minEdge: null,
}

export const useFiltersStore = create<FiltersStore>(set => ({
  filters: { ...DEFAULT_FILTERS },
  setFilter: (key, value) =>
    set(state => ({ filters: { ...state.filters, [key]: value } })),
  resetFilters: () => set({ filters: { ...DEFAULT_FILTERS } }),
}))

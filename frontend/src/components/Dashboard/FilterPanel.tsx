import { useFiltersStore } from '@/stores/useFiltersStore'

const CITIES = [
  '', 'Paris', 'Lyon', 'Marseille', 'Bordeaux', 'Toulouse',
  'Nantes', 'Strasbourg', 'Montpellier', 'Lille', 'Rennes', 'Nice', 'Grenoble',
]

function NumInput({
  label, value, onChange, min, max, step, placeholder,
}: {
  label: string
  value: number | null
  onChange: (v: number | null) => void
  min?: number
  max?: number
  step?: number
  placeholder?: string
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-slate-400 font-medium uppercase tracking-wide">{label}</label>
      <input
        type="number"
        min={min}
        max={max}
        step={step ?? 1}
        placeholder={placeholder ?? '—'}
        value={value ?? ''}
        onChange={e => onChange(e.target.value === '' ? null : Number(e.target.value))}
        className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-white w-full focus:outline-none focus:border-blue-500"
      />
    </div>
  )
}

export function FilterPanel() {
  const { filters, setFilter, resetFilters } = useFiltersStore()

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-4 flex flex-col gap-4">
      <div className="flex justify-between items-center">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">Filters</h2>
        <button
          onClick={resetFilters}
          className="text-xs text-slate-400 hover:text-white transition-colors"
        >
          Reset
        </button>
      </div>

      {/* City */}
      <div className="flex flex-col gap-1">
        <label className="text-xs text-slate-400 font-medium uppercase tracking-wide">City</label>
        <select
          value={filters.city}
          onChange={e => setFilter('city', e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
        >
          {CITIES.map(c => (
            <option key={c} value={c}>{c || 'All cities'}</option>
          ))}
        </select>
      </div>

      {/* Edge Score */}
      <NumInput
        label="Min Edge Score"
        value={filters.minEdge}
        onChange={v => setFilter('minEdge', v)}
        min={0} max={100} step={5}
        placeholder="0"
      />

      {/* Yield */}
      <NumInput
        label="Min Yield (%)"
        value={filters.minYield}
        onChange={v => setFilter('minYield', v)}
        min={0} max={30} step={0.5}
        placeholder="0"
      />

      {/* Price */}
      <div className="flex gap-2">
        <NumInput
          label="Min Price (€)"
          value={filters.minPrice}
          onChange={v => setFilter('minPrice', v)}
          min={0} step={500}
          placeholder="0"
        />
        <NumInput
          label="Max Price (€)"
          value={filters.maxPrice}
          onChange={v => setFilter('maxPrice', v)}
          min={0} step={500}
          placeholder="∞"
        />
      </div>

      {/* Surface */}
      <div className="flex gap-2">
        <NumInput
          label="Min m²"
          value={filters.minSurface}
          onChange={v => setFilter('minSurface', v)}
          min={0} step={1}
          placeholder="0"
        />
        <NumInput
          label="Max m²"
          value={filters.maxSurface}
          onChange={v => setFilter('maxSurface', v)}
          min={0} step={1}
          placeholder="∞"
        />
      </div>
    </div>
  )
}

import { useSummary } from '@/hooks/useListings'
import { apiClient } from '@/api/client'
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

function Chip({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div className="flex flex-col items-center bg-slate-800/60 border border-slate-700 rounded-lg px-4 py-2 min-w-[100px]">
      <span className="text-lg font-bold text-white">{value ?? '—'}</span>
      <span className="text-xs text-slate-400 whitespace-nowrap">{label}</span>
    </div>
  )
}

export function StatsBar() {
  const { data } = useSummary()
  const qc = useQueryClient()
  const [seeding, setSeeding] = useState(false)
  const [enriching, setEnriching] = useState(false)

  const handleSeed = async () => {
    setSeeding(true)
    await apiClient.triggerMockIngest()
    await new Promise(r => setTimeout(r, 1500))
    await apiClient.triggerEnrich()
    await new Promise(r => setTimeout(r, 2000))
    qc.invalidateQueries()
    setSeeding(false)
  }

  const handleEnrich = async () => {
    setEnriching(true)
    await apiClient.triggerEnrich()
    await new Promise(r => setTimeout(r, 2000))
    qc.invalidateQueries()
    setEnriching(false)
  }

  return (
    <div className="flex flex-wrap items-center gap-3 px-2">
      <Chip label="Listings" value={data?.total_listings ?? null} />
      <Chip label="Enriched" value={data?.enriched_listings ?? null} />
      <Chip
        label="Avg Edge"
        value={data?.avg_edge_score != null ? data.avg_edge_score.toFixed(1) : null}
      />
      <Chip
        label="Avg Yield"
        value={data?.avg_gross_yield != null ? `${data.avg_gross_yield.toFixed(1)}%` : null}
      />
      <Chip
        label="Avg Price"
        value={data?.avg_price != null ? `${data.avg_price.toLocaleString('fr-FR')} €` : null}
      />

      <div className="flex gap-2 ml-auto">
        <button
          onClick={handleSeed}
          disabled={seeding}
          className="text-xs bg-slate-700 hover:bg-slate-600 text-white px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
        >
          {seeding ? '⏳ Seeding…' : '⬇ Seed Mock Data'}
        </button>
        <button
          onClick={handleEnrich}
          disabled={enriching}
          className="text-xs bg-blue-700 hover:bg-blue-600 text-white px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
        >
          {enriching ? '⏳ Enriching…' : '⚡ Enrich All'}
        </button>
      </div>
    </div>
  )
}

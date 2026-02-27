import { useTopOpportunities } from '@/hooks/useListings'
import { EdgeBadge } from '@/components/UI/EdgeBadge'

interface Props {
  onSelect: (id: string) => void
}

export function TopOpportunities({ onSelect }: Props) {
  const { data, isLoading } = useTopOpportunities()

  if (isLoading) return <div className="text-slate-400 text-sm p-2">Loading top picks…</div>
  if (!data?.length) return null

  return (
    <div className="bg-gradient-to-r from-amber-950/60 to-slate-900 border border-amber-700/40 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-amber-400 text-base">★</span>
        <h2 className="text-sm font-bold text-amber-300 uppercase tracking-wider">Top Opportunities</h2>
        <span className="text-xs text-amber-500/70 ml-1">Top 5%</span>
      </div>
      <div className="flex gap-3 overflow-x-auto pb-1">
        {data.map(op => (
          <button
            key={op.id}
            onClick={() => onSelect(op.id)}
            className="flex-shrink-0 bg-slate-800/80 border border-amber-700/30 rounded-lg p-3 text-left hover:border-amber-500 transition-colors min-w-[160px]"
          >
            <div className="flex justify-between items-start mb-2">
              <span className="text-xs text-slate-400">{op.city ?? '—'}</span>
              <EdgeBadge score={op.edge_score} size="sm" />
            </div>
            <div className="text-white font-bold text-sm truncate max-w-[140px]">{op.title}</div>
            <div className="text-slate-300 text-xs mt-1">
              {op.price.toLocaleString('fr-FR')} €
              {op.surface && <span className="text-slate-500 ml-1">· {op.surface}m²</span>}
            </div>
            {op.gross_yield != null && (
              <div className="text-green-400 text-xs mt-1 font-medium">{op.gross_yield.toFixed(1)}% yield</div>
            )}
          </button>
        ))}
      </div>
    </div>
  )
}

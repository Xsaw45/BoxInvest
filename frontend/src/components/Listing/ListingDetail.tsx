import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  ResponsiveContainer, Tooltip,
} from 'recharts'
import { useListing } from '@/hooks/useListings'
import { EdgeBadge } from '@/components/UI/EdgeBadge'

interface Props {
  listingId: string
  onClose: () => void
}

function Stat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs text-slate-400 uppercase tracking-wide">{label}</span>
      <span className={`text-sm font-semibold ${highlight ? 'text-green-400' : 'text-white'}`}>
        {value}
      </span>
    </div>
  )
}

function ScoreBar({ label, value }: { label: string; value: number | null }) {
  const pct = value ?? 0
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="text-white font-medium">{pct.toFixed(0)}</span>
      </div>
      <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{
            width: `${pct}%`,
            backgroundColor: pct >= 70 ? '#22c55e' : pct >= 45 ? '#eab308' : '#f97316',
          }}
        />
      </div>
    </div>
  )
}

export function ListingDetail({ listingId, onClose }: Props) {
  const { data: listing, isLoading } = useListing(listingId)

  const radarData = listing?.enrichment
    ? [
        { subject: 'Price Dev.', value: 50 },  // placeholder — filled below
        { subject: 'Yield',      value: 0 },
        { subject: 'Transport',  value: listing.enrichment.transport_score ?? 0 },
        { subject: 'Storage',    value: listing.enrichment.vertical_storage_potential ?? 0 },
        { subject: 'Liquidity',  value: listing.enrichment.liquidity_score ?? 0 },
        { subject: 'Access',     value: listing.enrichment.accessibility_score ?? 0 },
      ]
    : []

  // Fill yield for radar
  if (radarData.length && listing?.enrichment?.gross_yield != null) {
    const yieldScore = Math.min(100, ((listing.enrichment.gross_yield - 2) / 10) * 100)
    radarData[1].value = Math.max(0, yieldScore)
  }
  if (radarData.length && listing?.enrichment?.ml_price_deviation != null) {
    radarData[0].value = Math.min(100, Math.max(0, 50 + listing.enrichment.ml_price_deviation * 3))
  }

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto mx-4 shadow-2xl">
        {/* Header */}
        <div className="flex justify-between items-start p-5 border-b border-slate-700">
          <div className="flex-1 pr-4">
            {isLoading ? (
              <div className="h-5 bg-slate-700 rounded animate-pulse w-48" />
            ) : (
              <>
                <div className="flex items-center gap-3 mb-1">
                  <h2 className="text-white font-bold text-lg">{listing?.title}</h2>
                  <EdgeBadge score={listing?.enrichment?.edge_score ?? null} size="lg" />
                </div>
                <span className="text-slate-400 text-sm">
                  {listing?.city}{listing?.postal_code && ` (${listing.postal_code})`}
                  {' · '}
                  <span className="text-xs uppercase text-slate-500">{listing?.source}</span>
                </span>
              </>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-xl leading-none p-1"
          >
            ✕
          </button>
        </div>

        {isLoading ? (
          <div className="p-5 space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-4 bg-slate-800 rounded animate-pulse" />
            ))}
          </div>
        ) : listing ? (
          <div className="p-5 flex flex-col gap-6">
            {/* Core stats grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <Stat label="Price" value={`${listing.price.toLocaleString('fr-FR')} €`} />
              <Stat label="Surface" value={listing.surface ? `${listing.surface} m²` : '—'} />
              <Stat
                label="€/m²"
                value={listing.enrichment?.price_per_sqm ? `${listing.enrichment.price_per_sqm.toFixed(0)} €` : '—'}
              />
              <Stat
                label="Gross Yield"
                value={listing.enrichment?.gross_yield ? `${listing.enrichment.gross_yield.toFixed(1)}%` : '—'}
                highlight={(listing.enrichment?.gross_yield ?? 0) >= 7}
              />
            </div>

            {/* Financial block */}
            {listing.enrichment && (
              <div className="bg-slate-800/50 rounded-xl p-4 grid grid-cols-2 sm:grid-cols-3 gap-4">
                <Stat
                  label="Est. Monthly Rent"
                  value={
                    listing.enrichment.estimated_rent_low && listing.enrichment.estimated_rent_high
                      ? `${listing.enrichment.estimated_rent_low.toFixed(0)}–${listing.enrichment.estimated_rent_high.toFixed(0)} €`
                      : '—'
                  }
                />
                <Stat
                  label="Storage Yield"
                  value={listing.enrichment.storage_yield_estimate ? `${listing.enrichment.storage_yield_estimate.toFixed(1)}%` : '—'}
                  highlight={(listing.enrichment.storage_yield_estimate ?? 0) >= 9}
                />
                <Stat
                  label="ML Fair Price"
                  value={listing.enrichment.ml_estimated_price ? `${listing.enrichment.ml_estimated_price.toLocaleString('fr-FR')} €` : 'N/A'}
                />
                <Stat
                  label="ML Deviation"
                  value={listing.enrichment.ml_price_deviation != null ? `${listing.enrichment.ml_price_deviation.toFixed(1)}%` : '—'}
                  highlight={(listing.enrichment.ml_price_deviation ?? 0) > 15}
                />
                <Stat
                  label="Avg Area Rent/m²"
                  value={listing.enrichment.avg_rent_area ? `${listing.enrichment.avg_rent_area} €/m²` : '—'}
                />
                <Stat
                  label="Pop. Density"
                  value={listing.enrichment.population_density ? `${listing.enrichment.population_density.toLocaleString('fr-FR')} /km²` : '—'}
                />
              </div>
            )}

            {/* Score breakdown bars */}
            {listing.enrichment && (
              <div className="flex flex-col gap-2">
                <h3 className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Score Breakdown</h3>
                <ScoreBar label="Transport Score" value={listing.enrichment.transport_score} />
                <ScoreBar label="Liquidity Score" value={listing.enrichment.liquidity_score} />
                <ScoreBar label="Accessibility Score" value={listing.enrichment.accessibility_score} />
                <ScoreBar label="Storage Potential" value={listing.enrichment.vertical_storage_potential} />
              </div>
            )}

            {/* Radar chart */}
            {radarData.length > 0 && (
              <div style={{ height: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
                    <PolarGrid stroke="#334155" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <Radar
                      name="Score"
                      dataKey="value"
                      stroke="#3b82f6"
                      fill="#3b82f6"
                      fillOpacity={0.25}
                    />
                    <Tooltip
                      contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                      labelStyle={{ color: '#94a3b8' }}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Tags & metadata */}
            <div className="flex flex-col gap-2">
              {listing.accessibility_tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {listing.accessibility_tags.map(tag => (
                    <span key={tag} className="text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded-full">
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              <div className="flex gap-4 text-xs text-slate-500">
                <span>{listing.photos_count} photo{listing.photos_count !== 1 ? 's' : ''}</span>
                {listing.floor_level != null && <span>Floor {listing.floor_level}</span>}
                <span>Scraped {new Date(listing.scraped_at).toLocaleDateString('fr-FR')}</span>
              </div>
            </div>

            {/* External link */}
            {listing.url && (
              <a
                href={listing.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-center bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2.5 rounded-lg transition-colors"
              >
                View Original Listing ↗
              </a>
            )}
          </div>
        ) : (
          <div className="p-5 text-slate-400">Listing not found.</div>
        )}
      </div>
    </div>
  )
}

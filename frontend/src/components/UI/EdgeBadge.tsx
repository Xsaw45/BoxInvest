interface EdgeBadgeProps {
  score: number | null
  size?: 'sm' | 'md' | 'lg'
}

export function edgeColor(score: number | null): string {
  if (score == null) return '#94a3b8'
  if (score >= 75) return '#22c55e'
  if (score >= 55) return '#eab308'
  if (score >= 35) return '#f97316'
  return '#ef4444'
}

export function EdgeBadge({ score, size = 'md' }: EdgeBadgeProps) {
  const color = edgeColor(score)
  const sizeClass = size === 'sm' ? 'text-xs px-1.5 py-0.5' : size === 'lg' ? 'text-lg px-3 py-1' : 'text-sm px-2 py-0.5'

  return (
    <span
      className={`inline-block font-bold rounded-full ${sizeClass}`}
      style={{ backgroundColor: color + '22', color, border: `1px solid ${color}` }}
    >
      {score != null ? score.toFixed(0) : '—'}
    </span>
  )
}

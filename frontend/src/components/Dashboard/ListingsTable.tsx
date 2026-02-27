import { useState } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type SortingState,
  type ColumnDef,
} from '@tanstack/react-table'
import { useListings } from '@/hooks/useListings'
import { EdgeBadge } from '@/components/UI/EdgeBadge'
import type { Listing } from '@/types/listing'

interface Props {
  onSelect: (id: string) => void
}

const fmt = (n: number | null | undefined, decimals = 0, suffix = '') =>
  n != null ? `${n.toLocaleString('fr-FR', { maximumFractionDigits: decimals })}${suffix}` : '—'

export function ListingsTable({ onSelect }: Props) {
  const [page, setPage] = useState(0)
  const [sorting, setSorting] = useState<SortingState>([])
  const { data, isLoading, isFetching } = useListings(page)

  const columns: ColumnDef<Listing>[] = [
    {
      accessorKey: 'city',
      header: 'City',
      cell: info => <span className="text-slate-300">{info.getValue<string>() ?? '—'}</span>,
    },
    {
      accessorKey: 'title',
      header: 'Title',
      cell: info => (
        <span className="text-white truncate block max-w-[200px]">{info.getValue<string>()}</span>
      ),
    },
    {
      accessorKey: 'price',
      header: 'Price',
      cell: info => <span className="text-white font-medium">{fmt(info.getValue<number>())} €</span>,
    },
    {
      accessorKey: 'surface',
      header: 'm²',
      cell: info => <span className="text-slate-300">{fmt(info.getValue<number | null>(), 1)}</span>,
    },
    {
      id: 'price_per_sqm',
      header: '€/m²',
      accessorFn: row => row.enrichment?.price_per_sqm,
      cell: info => <span className="text-slate-300">{fmt(info.getValue<number | null>(), 0)}</span>,
    },
    {
      id: 'gross_yield',
      header: 'Yield',
      accessorFn: row => row.enrichment?.gross_yield,
      cell: info => {
        const v = info.getValue<number | null>()
        return (
          <span className={v != null && v >= 7 ? 'text-green-400 font-medium' : 'text-slate-300'}>
            {v != null ? `${v.toFixed(1)}%` : '—'}
          </span>
        )
      },
    },
    {
      id: 'edge_score',
      header: 'Edge Score',
      accessorFn: row => row.enrichment?.edge_score,
      cell: info => <EdgeBadge score={info.getValue<number | null>()} size="sm" />,
    },
    {
      id: 'source',
      header: 'Source',
      accessorFn: row => row.source,
      cell: info => (
        <span className="text-xs text-slate-500 uppercase">{info.getValue<string>()}</span>
      ),
    },
  ]

  const table = useReactTable({
    data: data?.items ?? [],
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    manualPagination: true,
    pageCount: data ? Math.ceil(data.total / 50) : 0,
  })

  const totalPages = data ? Math.ceil(data.total / 50) : 0

  return (
    <div className="flex flex-col gap-2">
      <div className="flex justify-between items-center px-1">
        <span className="text-xs text-slate-400">
          {data ? `${data.total.toLocaleString('fr-FR')} listings` : '…'}
          {isFetching && <span className="ml-2 text-blue-400">↻</span>}
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="text-xs text-slate-400 hover:text-white disabled:opacity-30 px-2 py-1 rounded bg-slate-800"
          >
            ← Prev
          </button>
          <span className="text-xs text-slate-400">{page + 1} / {Math.max(1, totalPages)}</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={page >= totalPages - 1}
            className="text-xs text-slate-400 hover:text-white disabled:opacity-30 px-2 py-1 rounded bg-slate-800"
          >
            Next →
          </button>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-700">
        <table className="w-full text-sm border-collapse">
          <thead>
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id} className="border-b border-slate-700 bg-slate-800/60">
                {hg.headers.map(header => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className="px-3 py-2.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide cursor-pointer select-none hover:text-white whitespace-nowrap"
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {header.column.getIsSorted() === 'asc' && ' ↑'}
                    {header.column.getIsSorted() === 'desc' && ' ↓'}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {isLoading
              ? Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i} className="border-b border-slate-800">
                    {columns.map((_, j) => (
                      <td key={j} className="px-3 py-2.5">
                        <div className="h-3 bg-slate-800 rounded animate-pulse w-16" />
                      </td>
                    ))}
                  </tr>
                ))
              : table.getRowModel().rows.map(row => {
                  const isTop = (row.original.enrichment?.edge_score ?? 0) >= 75
                  return (
                    <tr
                      key={row.id}
                      onClick={() => onSelect(row.original.id)}
                      className={`border-b border-slate-800 cursor-pointer transition-colors
                        ${isTop ? 'bg-amber-950/20 hover:bg-amber-950/40' : 'hover:bg-slate-800/50'}`}
                    >
                      {row.getVisibleCells().map(cell => (
                        <td key={cell.id} className="px-3 py-2.5">
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </td>
                      ))}
                    </tr>
                  )
                })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

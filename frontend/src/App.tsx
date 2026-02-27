import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { InvestmentMap } from '@/components/Map/InvestmentMap'
import { FilterPanel } from '@/components/Dashboard/FilterPanel'
import { ListingsTable } from '@/components/Dashboard/ListingsTable'
import { TopOpportunities } from '@/components/Dashboard/TopOpportunities'
import { StatsBar } from '@/components/Dashboard/StatsBar'
import { ListingDetail } from '@/components/Listing/ListingDetail'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

function BoxInvestApp() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'map' | 'table'>('map')

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      {/* Top bar */}
      <header className="border-b border-slate-800 px-4 py-3 flex items-center gap-4 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <span className="text-xl font-black tracking-tight text-blue-400">Box</span>
          <span className="text-xl font-black tracking-tight text-white">Invest</span>
          <span className="text-xs bg-blue-600/20 text-blue-400 border border-blue-600/30 px-2 py-0.5 rounded-full ml-1">
            BETA
          </span>
        </div>
        <div className="h-4 w-px bg-slate-700" />
        <p className="text-xs text-slate-400 hidden sm:block">
          Garage & parking investment opportunity detector
        </p>
      </header>

      {/* Stats row */}
      <div className="border-b border-slate-800 px-4 py-3 bg-slate-900/40">
        <StatsBar />
      </div>

      {/* Top opportunities strip */}
      <div className="px-4 py-3 border-b border-slate-800">
        <TopOpportunities onSelect={setSelectedId} />
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel */}
        <div className="w-80 flex-shrink-0 border-r border-slate-800 overflow-y-auto p-4 bg-slate-900/20">
          <FilterPanel />
        </div>

        {/* Right panel: tab-switched map / table */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tab switcher */}
          <div className="flex border-b border-slate-800 bg-slate-900/30">
            {(['map', 'table'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-2.5 text-sm font-medium transition-colors capitalize
                  ${activeTab === tab
                    ? 'text-white border-b-2 border-blue-500'
                    : 'text-slate-400 hover:text-white'
                  }`}
              >
                {tab === 'map' ? '🗺 Map' : '📋 Table'}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-hidden">
            {activeTab === 'map' ? (
              <div className="h-full">
                <InvestmentMap onSelectListing={setSelectedId} />
              </div>
            ) : (
              <div className="p-4 overflow-y-auto h-full">
                <ListingsTable onSelect={setSelectedId} />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Detail modal */}
      {selectedId && (
        <ListingDetail listingId={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BoxInvestApp />
    </QueryClientProvider>
  )
}

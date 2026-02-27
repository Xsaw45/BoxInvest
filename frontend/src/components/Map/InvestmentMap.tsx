import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useGeoJSON } from '@/hooks/useListings'
import { edgeColor } from '@/components/UI/EdgeBadge'
import type { GeoFeatureProperties } from '@/types/listing'

interface InvestmentMapProps {
  onSelectListing: (id: string) => void
}

function makeIcon(score: number | null) {
  const color = edgeColor(score)
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="36" viewBox="0 0 28 36">
    <path d="M14 0C6.268 0 0 6.268 0 14c0 9.333 14 22 14 22S28 23.333 28 14C28 6.268 21.732 0 14 0z"
      fill="${color}" stroke="white" stroke-width="1.5"/>
    <text x="14" y="18" font-size="9" font-family="sans-serif" font-weight="bold"
      text-anchor="middle" fill="white">${score != null ? Math.round(score) : '?'}</text>
  </svg>`
  return L.divIcon({
    html: svg,
    iconSize: [28, 36],
    iconAnchor: [14, 36],
    popupAnchor: [0, -36],
    className: '',
  })
}

export function InvestmentMap({ onSelectListing }: InvestmentMapProps) {
  const mapRef = useRef<L.Map | null>(null)
  const layerRef = useRef<L.LayerGroup | null>(null)
  const { data: geojson } = useGeoJSON()

  useEffect(() => {
    if (mapRef.current) return
    const map = L.map('investment-map', {
      center: [46.603354, 1.888334],
      zoom: 6,
      zoomControl: true,
    })
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(map)
    layerRef.current = L.layerGroup().addTo(map)
    mapRef.current = map
  }, [])

  useEffect(() => {
    if (!geojson || !layerRef.current) return
    layerRef.current.clearLayers()

    geojson.features.forEach(feature => {
      const [lon, lat] = feature.geometry.coordinates
      const p = feature.properties as GeoFeatureProperties
      const marker = L.marker([lat, lon], { icon: makeIcon(p.edge_score) })

      const yieldStr = p.gross_yield != null ? `${p.gross_yield.toFixed(1)}%` : '—'
      const ppsqm = p.price_per_sqm != null ? `${p.price_per_sqm.toFixed(0)} €/m²` : '—'
      const priceStr = p.price.toLocaleString('fr-FR') + ' €'

      marker.bindPopup(`
        <div style="min-width:200px;font-family:sans-serif">
          <strong style="font-size:13px">${p.title}</strong><br/>
          <span style="color:#64748b;font-size:11px">${p.city ?? ''}</span>
          <hr style="margin:6px 0"/>
          <table style="font-size:12px;width:100%">
            <tr><td>Price</td><td><b>${priceStr}</b></td></tr>
            <tr><td>€/m²</td><td>${ppsqm}</td></tr>
            <tr><td>Yield</td><td>${yieldStr}</td></tr>
            <tr><td>Edge</td><td><b style="color:${edgeColor(p.edge_score)}">${p.edge_score != null ? p.edge_score.toFixed(0) : '—'}</b></td></tr>
          </table>
          <button
            onclick="document.dispatchEvent(new CustomEvent('select-listing', {detail:'${p.id}'}))"
            style="margin-top:8px;width:100%;padding:5px;background:#3b82f6;color:white;border:none;border-radius:4px;cursor:pointer;font-size:12px"
          >View Details</button>
        </div>
      `)
      layerRef.current!.addLayer(marker)
    })
  }, [geojson])

  // Listen for popup button clicks
  useEffect(() => {
    const handler = (e: Event) => {
      onSelectListing((e as CustomEvent<string>).detail)
    }
    document.addEventListener('select-listing', handler)
    return () => document.removeEventListener('select-listing', handler)
  }, [onSelectListing])

  return <div id="investment-map" style={{ width: '100%', height: '100%', minHeight: 400 }} />
}

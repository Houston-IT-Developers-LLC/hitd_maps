'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { MapPin, Layers, Mountain, Satellite } from 'lucide-react'

export default function MapDemoPage() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const [mapStyle, setMapStyle] = useState<'map' | 'satellite' | 'terrain'>('map')
  const [layers, setLayers] = useState({
    parcels: true,
    pois: true,
    buildings: true,
  })

  useEffect(() => {
    if (!mapContainer.current || map.current) return

    const initMap = async () => {
      const maplibregl = (await import('maplibre-gl')).default
      const pmtiles = await import('pmtiles')

      // Register PMTiles protocol
      const protocol = new pmtiles.Protocol()
      maplibregl.addProtocol('pmtiles', protocol.tile)

      const CDN = 'https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev'

      map.current = new maplibregl.Map({
        container: mapContainer.current!,
        style: {
          version: 8,
          sources: {
            protomaps: {
              type: 'vector',
              url: `pmtiles://${CDN}/basemap/protomaps_planet.pmtiles`,
            },
          },
          layers: [
            {
              id: 'background',
              type: 'background',
              paint: { 'background-color': '#f8f4f0' },
            },
            {
              id: 'water',
              type: 'fill',
              source: 'protomaps',
              'source-layer': 'water',
              paint: { 'fill-color': '#a0c4e8' },
            },
            {
              id: 'landuse-park',
              type: 'fill',
              source: 'protomaps',
              'source-layer': 'landuse',
              filter: ['==', ['get', 'kind'], 'park'],
              paint: { 'fill-color': '#c8e6c9' },
            },
            {
              id: 'roads-minor',
              type: 'line',
              source: 'protomaps',
              'source-layer': 'roads',
              filter: ['in', ['get', 'kind'], ['literal', ['minor_road', 'service']]],
              paint: { 'line-color': '#ffffff', 'line-width': 1 },
              minzoom: 12,
            },
            {
              id: 'roads-major',
              type: 'line',
              source: 'protomaps',
              'source-layer': 'roads',
              filter: ['in', ['get', 'kind'], ['literal', ['major_road', 'highway']]],
              paint: { 'line-color': '#ffc107', 'line-width': 2 },
            },
            {
              id: 'buildings',
              type: 'fill',
              source: 'protomaps',
              'source-layer': 'buildings',
              paint: { 'fill-color': '#d4d4d4', 'fill-opacity': 0.8 },
              minzoom: 14,
            },
            {
              id: 'places-label',
              type: 'symbol',
              source: 'protomaps',
              'source-layer': 'places',
              layout: {
                'text-field': ['get', 'name'],
                'text-size': 12,
              },
              paint: {
                'text-color': '#333',
                'text-halo-color': '#fff',
                'text-halo-width': 1,
              },
            },
          ],
        },
        center: [-95.37, 29.76], // Houston
        zoom: 10,
      })

      // Add navigation controls
      map.current.addControl(new maplibregl.NavigationControl(), 'top-right')

      // Add parcels layer on load
      map.current.on('load', () => {
        // Add parcel source
        map.current!.addSource('parcels', {
          type: 'vector',
          url: `pmtiles://${CDN}/parcels_tx_harris_v2.pmtiles`,
        })

        map.current!.addLayer({
          id: 'parcels-fill',
          type: 'fill',
          source: 'parcels',
          'source-layer': 'parcels_tx_harris_v2',
          paint: {
            'fill-color': '#e53935',
            'fill-opacity': [
              'interpolate',
              ['linear'],
              ['zoom'],
              10, 0.1,
              14, 0.3,
            ],
          },
          minzoom: 10,
        })

        map.current!.addLayer({
          id: 'parcels-outline',
          type: 'line',
          source: 'parcels',
          'source-layer': 'parcels_tx_harris_v2',
          paint: {
            'line-color': '#b71c1c',
            'line-width': 0.5,
          },
          minzoom: 12,
        })

        // Add click handler for parcels
        map.current!.on('click', 'parcels-fill', (e) => {
          if (!e.features || e.features.length === 0) return

          const props = e.features[0].properties
          const content = Object.entries(props || {})
            .filter(([key]) => !key.startsWith('_'))
            .slice(0, 10)
            .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
            .join('<br>')

          new maplibregl.Popup()
            .setLngLat(e.lngLat)
            .setHTML(`<div style="max-height: 200px; overflow-y: auto;">${content}</div>`)
            .addTo(map.current!)
        })

        map.current!.on('mouseenter', 'parcels-fill', () => {
          map.current!.getCanvas().style.cursor = 'pointer'
        })

        map.current!.on('mouseleave', 'parcels-fill', () => {
          map.current!.getCanvas().style.cursor = ''
        })
      })
    }

    initMap()

    return () => {
      map.current?.remove()
    }
  }, [])

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b px-4 py-3 flex items-center justify-between z-10">
        <Link href="/" className="flex items-center gap-2">
          <MapPin className="h-6 w-6 text-primary" />
          <span className="font-bold">Maps for Developers</span>
        </Link>
        <div className="flex items-center gap-4">
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setMapStyle('map')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                mapStyle === 'map' ? 'bg-white shadow' : 'hover:bg-white/50'
              }`}
            >
              <Layers className="h-4 w-4 inline mr-1" />
              Map
            </button>
            <button
              onClick={() => setMapStyle('satellite')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                mapStyle === 'satellite' ? 'bg-white shadow' : 'hover:bg-white/50'
              }`}
            >
              <Satellite className="h-4 w-4 inline mr-1" />
              Satellite
            </button>
            <button
              onClick={() => setMapStyle('terrain')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                mapStyle === 'terrain' ? 'bg-white shadow' : 'hover:bg-white/50'
              }`}
            >
              <Mountain className="h-4 w-4 inline mr-1" />
              3D
            </button>
          </div>
          <Button asChild size="sm">
            <Link href="/signup">Get API Key</Link>
          </Button>
        </div>
      </header>

      {/* Map */}
      <div className="flex-1 relative">
        <div ref={mapContainer} className="absolute inset-0" />

        {/* Layer Panel */}
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 w-64 z-10">
          <h3 className="font-semibold mb-3">Data Layers</h3>
          <div className="space-y-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={layers.parcels}
                onChange={(e) =>
                  setLayers((l) => ({ ...l, parcels: e.target.checked }))
                }
                className="rounded"
              />
              <span className="text-sm">Property Parcels</span>
              <span className="text-xs text-muted-foreground ml-auto">Harris County</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={layers.buildings}
                onChange={(e) =>
                  setLayers((l) => ({ ...l, buildings: e.target.checked }))
                }
                className="rounded"
              />
              <span className="text-sm">Buildings</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={layers.pois}
                onChange={(e) =>
                  setLayers((l) => ({ ...l, pois: e.target.checked }))
                }
                className="rounded"
              />
              <span className="text-sm">Points of Interest</span>
            </label>
          </div>

          <div className="mt-4 pt-4 border-t">
            <p className="text-xs text-muted-foreground">
              Click on a parcel to see property details
            </p>
          </div>
        </div>

        {/* Info Banner */}
        <div className="absolute bottom-4 left-4 right-4 bg-white/90 backdrop-blur rounded-lg shadow-lg p-4 z-10">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">This is a demo of Maps for Developers</p>
              <p className="text-sm text-muted-foreground">
                680GB of data including 150M+ parcels, 17M+ POIs, terrain, and satellite imagery
              </p>
            </div>
            <Button asChild>
              <Link href="/signup">
                Start Building Free
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

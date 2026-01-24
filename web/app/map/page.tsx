'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { MapPin, Layers, Mountain, Satellite } from 'lucide-react'
import 'maplibre-gl/dist/maplibre-gl.css'

const CDN = 'https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev'
const PROTOMAPS_URL = `${CDN}/basemap/protomaps_planet.pmtiles`
const OSM_TILES = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
const ESRI_SATELLITE = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
const AWS_TERRAIN = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'

export default function MapDemoPage() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const [mapStyle, setMapStyle] = useState<'map' | 'satellite' | 'terrain'>('map')
  const [status, setStatus] = useState('Loading map...')
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
      const protomapsThemes = await import('protomaps-themes-base')

      // Register PMTiles protocol
      const protocol = new pmtiles.Protocol()
      maplibregl.addProtocol('pmtiles', protocol.tile)

      // Build map style - try Protomaps first, fall back to OSM
      let mapStyleObj: maplibregl.StyleSpecification

      try {
        // Try to use Protomaps vector basemap
        const protomapsLayers = protomapsThemes.layers(
          'protomaps',
          protomapsThemes.namedTheme('light'),
          { lang: 'en' }
        )

        mapStyleObj = {
          version: 8,
          glyphs: 'https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf',
          sprite: 'https://protomaps.github.io/basemaps-assets/sprites/v4/light',
          sources: {
            protomaps: {
              type: 'vector',
              url: `pmtiles://${PROTOMAPS_URL}`,
            },
            sat: {
              type: 'raster',
              tiles: [ESRI_SATELLITE],
              tileSize: 256,
              maxzoom: 18,
            },
            terrain: {
              type: 'raster-dem',
              tiles: [AWS_TERRAIN],
              tileSize: 256,
              maxzoom: 15,
              encoding: 'terrarium',
            },
          },
          layers: [
            ...protomapsLayers,
            {
              id: 'sat',
              type: 'raster',
              source: 'sat',
              layout: { visibility: 'none' },
            },
            {
              id: 'hillshade',
              type: 'hillshade',
              source: 'terrain',
              layout: { visibility: 'none' },
              paint: { 'hillshade-exaggeration': 0.5 },
            },
          ],
          terrain: { source: 'terrain', exaggeration: 0 },
        }
        setStatus('Map loaded with Protomaps')
      } catch (e) {
        console.error('Failed to load Protomaps theme, falling back to OSM:', e)
        // Fallback to OSM raster tiles
        mapStyleObj = {
          version: 8,
          sources: {
            osm: {
              type: 'raster',
              tiles: [OSM_TILES],
              tileSize: 256,
              maxzoom: 19,
            },
            sat: {
              type: 'raster',
              tiles: [ESRI_SATELLITE],
              tileSize: 256,
              maxzoom: 18,
            },
            terrain: {
              type: 'raster-dem',
              tiles: [AWS_TERRAIN],
              tileSize: 256,
              maxzoom: 15,
              encoding: 'terrarium',
            },
          },
          layers: [
            { id: 'osm', type: 'raster', source: 'osm' },
            {
              id: 'sat',
              type: 'raster',
              source: 'sat',
              layout: { visibility: 'none' },
            },
            {
              id: 'hillshade',
              type: 'hillshade',
              source: 'terrain',
              layout: { visibility: 'none' },
              paint: { 'hillshade-exaggeration': 0.5 },
            },
          ],
          terrain: { source: 'terrain', exaggeration: 0 },
        }
        setStatus('Map loaded with OSM fallback')
      }

      map.current = new maplibregl.Map({
        container: mapContainer.current!,
        style: mapStyleObj,
        center: [-98.5, 39.8], // Center of USA
        zoom: 4,
      })

      // Add navigation controls
      map.current.addControl(new maplibregl.NavigationControl(), 'top-right')
      map.current.addControl(new maplibregl.ScaleControl(), 'bottom-right')

      // Add parcels layer on load
      map.current.on('load', () => {
        setStatus('Loading parcels...')

        // Add Harris County parcels as demo
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

        setStatus('Map ready - zoom to Houston to see parcels')
      })

      map.current.on('error', (e) => {
        console.error('Map error:', e)
        setStatus(`Map error: ${e.error?.message || 'Unknown error'}`)
      })
    }

    initMap()

    return () => {
      map.current?.remove()
    }
  }, [])

  // Handle map style switching
  useEffect(() => {
    if (!map.current) return

    const m = map.current

    // Helper to set layer visibility
    const setLayerVisibility = (layerId: string, visible: boolean) => {
      if (m.getLayer(layerId)) {
        m.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none')
      }
    }

    // Helper to set basemap visibility (protomaps or osm layers)
    const setBasemapVisibility = (visible: boolean) => {
      m.getStyle()?.layers?.forEach((layer) => {
        const layerSource = 'source' in layer ? layer.source : null
        if (layerSource === 'protomaps' || layerSource === 'osm') {
          setLayerVisibility(layer.id, visible)
        }
      })
    }

    if (mapStyle === 'map') {
      setBasemapVisibility(true)
      setLayerVisibility('sat', false)
      setLayerVisibility('hillshade', false)
      m.setTerrain({ source: 'terrain', exaggeration: 0 })
    } else if (mapStyle === 'satellite') {
      setBasemapVisibility(false)
      setLayerVisibility('sat', true)
      setLayerVisibility('hillshade', false)
      m.setTerrain({ source: 'terrain', exaggeration: 0 })
    } else if (mapStyle === 'terrain') {
      setBasemapVisibility(true)
      setLayerVisibility('sat', false)
      setLayerVisibility('hillshade', true)
      m.setTerrain({ source: 'terrain', exaggeration: 1.5 })
    }
  }, [mapStyle])

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
              <span className="text-xs text-muted-foreground ml-auto">150M+</span>
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
              <span className="text-xs text-muted-foreground ml-auto">17M+</span>
            </label>
          </div>

          <div className="mt-4 pt-4 border-t">
            <p className="text-xs text-muted-foreground">
              {status}
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

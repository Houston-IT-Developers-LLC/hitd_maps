'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { MapPin, Layers, Mountain, Satellite } from 'lucide-react'
import 'maplibre-gl/dist/maplibre-gl.css'

const CDN = 'https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev'
const PROTOMAPS_URL = `${CDN}/basemap/protomaps_planet.pmtiles`
const ESRI_SATELLITE = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
const AWS_TERRAIN = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'

// Minimum zoom level before loading parcels (neighborhood level)
const PARCEL_LOAD_ZOOM = 8

// All verified USA parcel files (92 files covering 50 states + DC)
const PARCELS = [
  'parcels_az', 'parcels_az_maricopa',
  'parcels_ca_los_angeles_v2', 'parcels_ca_san_francisco',
  'parcels_co', 'parcels_co_el_paso_v2', 'parcels_co_statewide',
  'parcels_ct', 'parcels_dc', 'parcels_de',
  'parcels_fl_statewide',
  'parcels_ga_chatham', 'parcels_ga_cobb', 'parcels_ga_gwinnett', 'parcels_ga_gwinnett_v2', 'parcels_ga_richmond',
  'parcels_hi',
  'parcels_ia', 'parcels_ia_statewide',
  'parcels_il', 'parcels_in_marion',
  'parcels_ks', 'parcels_ks_sedgwick',
  'parcels_ky', 'parcels_ky_boone',
  'parcels_la', 'parcels_la_orleans_v2',
  'parcels_ma', 'parcels_md_statewide',
  'parcels_me_bangor', 'parcels_me_portland',
  'parcels_mi_kent', 'parcels_mi_kent_v2', 'parcels_mi_macomb', 'parcels_mi_oakland_v2', 'parcels_mi_ottawa', 'parcels_mi_wayne',
  'parcels_mn_dakota', 'parcels_mn_hennepin', 'parcels_mn_ramsey',
  'parcels_nc_durham', 'parcels_nc_forsyth', 'parcels_nc_forsyth_wgs84', 'parcels_nc_guilford', 'parcels_nc_statewide', 'parcels_nc_wake',
  'parcels_nd', 'parcels_nd_cass',
  'parcels_ne', 'parcels_nh',
  'parcels_nj_statewide_v2', 'parcels_nm',
  'parcels_ny_centroids', 'parcels_ny_statewide', 'parcels_ny_statewide_v2',
  'parcels_oh_cuyahoga', 'parcels_oh_hamilton', 'parcels_oh_statewide', 'parcels_oh_summit_v2',
  'parcels_or_multnomah_v2',
  'parcels_pa_allegheny', 'parcels_pa_delaware', 'parcels_pa_lackawanna', 'parcels_pa_lancaster_v2', 'parcels_pa_pasda_statewide', 'parcels_pa_statewide',
  'parcels_sc_charleston', 'parcels_sc_greenville',
  'parcels_tn', 'parcels_tn_davidson', 'parcels_tn_hamilton', 'parcels_tn_nashville', 'parcels_tn_shelby', 'parcels_tn_statewide', 'parcels_tn_williamson',
  'parcels_tx_bexar', 'parcels_tx_dallas', 'parcels_tx_denton', 'parcels_tx_harris', 'parcels_tx_harris_new',
  'parcels_tx_statewide', 'parcels_tx_statewide_recent', 'parcels_tx_tarrant', 'parcels_tx_travis', 'parcels_tx_williamson_v2',
  'parcels_ut',
  'parcels_va',
  'parcels_wa_king', 'parcels_wa_spokane',
  'parcels_wi', 'parcels_wi_kenosha', 'parcels_wi_milwaukee', 'parcels_wi_racine', 'parcels_wi_waukesha',
  'parcels_wv',
  'parcels_wy_campbell'
]

export default function MapDemoPage() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const maplibreRef = useRef<any>(null)
  const parcelsLoadedRef = useRef(false)
  const parcelsLoadingRef = useRef(false)
  const [mapStyle, setMapStyle] = useState<'map' | 'satellite' | 'terrain'>('map')
  const [status, setStatus] = useState('Loading map...')
  const [parcelsLoaded, setParcelsLoaded] = useState(false)
  const [layers, setLayers] = useState({
    parcels: true,
    pois: true,
    buildings: true,
  })

  // Toggle parcel visibility
  useEffect(() => {
    if (!map.current || !parcelsLoaded) return

    const visibility = layers.parcels ? 'visible' : 'none'
    PARCELS.forEach((p) => {
      if (map.current?.getLayer(`${p}-fill`)) {
        map.current.setLayoutProperty(`${p}-fill`, 'visibility', visibility)
      }
      if (map.current?.getLayer(`${p}-line`)) {
        map.current.setLayoutProperty(`${p}-line`, 'visibility', visibility)
      }
    })
  }, [layers.parcels, parcelsLoaded])

  useEffect(() => {
    if (!mapContainer.current || map.current) return

    const initMap = async () => {
      try {
        const maplibregl = (await import('maplibre-gl')).default
        maplibreRef.current = maplibregl
        const pmtiles = await import('pmtiles')
        const protomapsThemes = await import('protomaps-themes-base')

        // Register PMTiles protocol
        const protocol = new pmtiles.Protocol()
        maplibregl.addProtocol('pmtiles', protocol.tile)

        // Build map style with Protomaps
        const protomapsLayers = protomapsThemes.layers(
          'protomaps',
          protomapsThemes.namedTheme('light'),
          { lang: 'en' }
        )

        const mapStyleObj: maplibregl.StyleSpecification = {
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

        map.current = new maplibregl.Map({
          container: mapContainer.current!,
          style: mapStyleObj,
          center: [-98.5, 39.8], // Center of USA
          zoom: 4,
        })

        setStatus('Initializing map...')

        // Add navigation controls
        map.current.addControl(new maplibregl.NavigationControl(), 'top-right')
        map.current.addControl(new maplibregl.ScaleControl(), 'bottom-right')

        // Load parcels function - called when zoom >= PARCEL_LOAD_ZOOM
        const loadParcels = async () => {
          if (parcelsLoadedRef.current || parcelsLoadingRef.current || !map.current) return
          parcelsLoadingRef.current = true

          setStatus('Loading parcels...')

          for (const p of PARCELS) {
            try {
              if (map.current?.getSource(p)) continue

              map.current?.addSource(p, {
                type: 'vector',
                url: `pmtiles://${CDN}/parcels/${p}.pmtiles`,
              })

              map.current?.addLayer({
                id: `${p}-fill`,
                type: 'fill',
                source: p,
                'source-layer': 'parcels',
                minzoom: 5,
                paint: {
                  'fill-color': '#e53935',
                  'fill-opacity': [
                    'interpolate', ['linear'], ['zoom'],
                    5, 0.02,
                    10, 0.15,
                    14, 0.3,
                  ],
                },
              })

              map.current?.addLayer({
                id: `${p}-line`,
                type: 'line',
                source: p,
                'source-layer': 'parcels',
                minzoom: 11,
                paint: {
                  'line-color': '#b71c1c',
                  'line-width': ['interpolate', ['linear'], ['zoom'], 11, 0.3, 16, 1.5],
                },
              })
            } catch (e) {
              console.warn(`Failed to load parcel: ${p}`, e)
            }
          }

          parcelsLoadedRef.current = true
          setParcelsLoaded(true)
          setStatus('Ready! Click any parcel for details.')
        }

        // Map ready - set up lazy loading
        map.current.on('load', () => {
          setStatus('Map ready! Zoom in to see parcels.')

          // Single delegated click handler for all parcels (much more efficient)
          map.current?.on('click', (e) => {
            if (!parcelsLoadedRef.current || !map.current) return

            // Get all parcel fill layers that exist
            const parcelLayers = PARCELS
              .map(p => `${p}-fill`)
              .filter(l => map.current?.getLayer(l))

            if (parcelLayers.length === 0) return

            const features = map.current.queryRenderedFeatures(e.point, {
              layers: parcelLayers
            })

            if (features.length > 0 && maplibreRef.current) {
              const props = features[0].properties
              const content = Object.entries(props || {})
                .filter(([key]) => !key.startsWith('_'))
                .slice(0, 15)
                .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
                .join('<br>')

              new maplibreRef.current.Popup()
                .setLngLat(e.lngLat)
                .setHTML(`<div style="max-height: 250px; overflow-y: auto; font-size: 12px;">${content}</div>`)
                .addTo(map.current!)
            }
          })

          // Single mousemove handler for cursor changes
          map.current?.on('mousemove', (e) => {
            if (!parcelsLoadedRef.current || !map.current) return

            const parcelLayers = PARCELS
              .map(p => `${p}-fill`)
              .filter(l => map.current?.getLayer(l))

            if (parcelLayers.length === 0) return

            const features = map.current.queryRenderedFeatures(e.point, {
              layers: parcelLayers
            })

            map.current.getCanvas().style.cursor = features.length > 0 ? 'pointer' : ''
          })

          // Zoom listener for lazy loading parcels
          map.current?.on('zoom', () => {
            if (!map.current) return
            const zoom = map.current.getZoom()

            if (zoom >= PARCEL_LOAD_ZOOM && !parcelsLoadedRef.current && !parcelsLoadingRef.current) {
              loadParcels()
            }
          })
        })

        map.current.on('error', (e) => {
          console.error('Map error:', e)
          // Don't update status for source errors (parcels loading)
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          if (!(e as any).sourceId) {
            setStatus(`Map error: ${e.error?.message || 'Unknown error'}`)
          }
        })
      } catch (err) {
        console.error('Failed to initialize map:', err)
        setStatus('Failed to load map. Please refresh the page.')
      }
    }

    initMap()

    return () => {
      map.current?.remove()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
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

    // Helper to set basemap visibility (protomaps layers)
    const setBasemapVisibility = (visible: boolean) => {
      m.getStyle()?.layers?.forEach((layer) => {
        const layerSource = 'source' in layer ? layer.source : null
        if (layerSource === 'protomaps') {
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
        <div ref={mapContainer} className="absolute inset-0 z-0" />

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

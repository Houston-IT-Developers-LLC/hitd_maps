'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { MapPin, Layers, Mountain, Satellite } from 'lucide-react'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { LngLatBounds } from 'maplibre-gl'

const CDN = 'https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev'
const PROTOMAPS_URL = `${CDN}/basemap/protomaps_planet.pmtiles`
const ESRI_SATELLITE = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
const AWS_TERRAIN = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'

// Progressive loading strategy
const PARCEL_LOAD_ZOOM = 8 // Start loading parcels
const COUNTY_LOAD_ZOOM = 11 // Load county-level detail
const VIEWPORT_BUFFER = 0.5 // degrees buffer around viewport

// Spatial index for efficient viewport-based loading
const PARCEL_INDEX = {
  FL: {
    bounds: [-87.635, 24.523, -80.031, 31.001],
    statewide: ['parcels_fl_statewide'],
    counties: ['parcels_fl_orange']
  },
  TX: {
    bounds: [-106.645, 25.837, -93.508, 36.500],
    statewide: ['parcels_tx_statewide_recent'],
    counties: [
      'parcels_tx_bexar', 'parcels_tx_dallas', 'parcels_tx_denton',
      'parcels_tx_harris_v2', 'parcels_tx_montgomery',
      'parcels_tx_tarrant_v2', 'parcels_tx_travis_v2', 'parcels_tx_williamson_v2'
    ]
  },
  CA: {
    bounds: [-124.482, 32.529, -114.131, 42.009],
    statewide: ['parcels_ca_statewide'],
    counties: [
      'parcels_ca_fresno', 'parcels_ca_los_angeles_v2',
      'parcels_ca_orange_v2', 'parcels_ca_riverside',
      'parcels_ca_sacramento_v2', 'parcels_ca_san_diego',
      'parcels_ca_san_francisco', 'parcels_ca_sonoma'
    ]
  },
  NY: {
    bounds: [-79.762, 40.496, -71.856, 45.015],
    statewide: ['parcels_ny_statewide_v2'],
    counties: []
  },
  PA: {
    bounds: [-80.519, 39.720, -74.690, 42.269],
    statewide: ['parcels_pa_statewide'],
    counties: ['parcels_pa_allegheny', 'parcels_pa_delaware', 'parcels_pa_lancaster_v2']
  },
  OH: {
    bounds: [-84.820, 38.403, -80.519, 41.977],
    statewide: ['parcels_oh_statewide'],
    counties: ['parcels_oh_cuyahoga', 'parcels_oh_franklin', 'parcels_oh_hamilton']
  },
  NC: {
    bounds: [-84.322, 33.753, -75.401, 36.588],
    statewide: ['parcels_nc_statewide'],
    counties: ['parcels_nc_mecklenburg_wgs84', 'parcels_nc_wake', 'parcels_nc_durham_wgs84']
  },
  WA: {
    bounds: [-124.736, 45.544, -116.916, 49.002],
    statewide: ['parcels_wa_statewide'],
    counties: ['parcels_wa_king_wgs84', 'parcels_wa_spokane_wgs84']
  },
  VA: {
    bounds: [-83.675, 36.541, -75.243, 39.466],
    statewide: ['parcels_va_statewide_v2'],
    counties: ['parcels_va_loudoun_v2', 'parcels_va_prince_william_v2']
  },
  WI: {
    bounds: [-92.889, 42.492, -86.249, 47.309],
    statewide: ['parcels_wi_statewide'],
    counties: ['parcels_wi_milwaukee_v2']
  },
  TN: {
    bounds: [-90.310, 34.983, -81.647, 36.678],
    statewide: ['parcels_tn_statewide'],
    counties: ['parcels_tn_davidson', 'parcels_tn_shelby']
  },
  IN: {
    bounds: [-88.098, 37.771, -84.784, 41.761],
    statewide: ['parcels_in_statewide'],
    counties: []
  },
  MN: {
    bounds: [-97.239, 43.499, -89.483, 49.384],
    statewide: ['parcels_mn_statewide'],
    counties: []
  },
  AZ: {
    bounds: [-114.816, 31.332, -109.045, 37.004],
    statewide: [],
    counties: ['parcels_az_maricopa', 'parcels_az_pima', 'parcels_az_pinal']
  },
  CO: {
    bounds: [-109.060, 36.992, -102.042, 41.003],
    statewide: ['parcels_co_statewide'],
    counties: []
  },
  MA: { bounds: [-73.508, 41.238, -69.928, 42.887], statewide: ['parcels_ma_statewide'], counties: [] },
  MD: { bounds: [-79.487, 37.887, -74.986, 39.723], statewide: ['parcels_md_statewide'], counties: [] },
  NJ: { bounds: [-75.563, 38.788, -73.894, 41.357], statewide: ['parcels_nj_statewide_v2'], counties: [] },
  CT: { bounds: [-73.728, 40.950, -71.787, 42.051], statewide: ['parcels_ct_statewide_v2'], counties: [] },
  IA: { bounds: [-96.639, 40.375, -90.140, 43.501], statewide: ['parcels_ia_statewide'], counties: [] },
  AR: { bounds: [-94.618, 33.004, -89.644, 36.500], statewide: ['parcels_ar_statewide'], counties: [] },
  NM: { bounds: [-109.050, 31.332, -103.002, 37.000], statewide: ['parcels_nm_statewide_v2'], counties: [] },
  NV: { bounds: [-120.006, 35.002, -114.040, 42.002], statewide: ['parcels_nv_statewide'], counties: [] },
  UT: { bounds: [-114.053, 36.997, -109.041, 42.001], statewide: ['parcels_ut_statewide'], counties: [] },
  WV: { bounds: [-82.644, 37.202, -77.719, 40.638], statewide: ['parcels_wv_statewide'], counties: [] },
  HI: { bounds: [-178.338, 18.911, -154.807, 28.402], statewide: ['parcels_hi_statewide'], counties: [] },
  ID: { bounds: [-117.243, 41.988, -111.043, 49.001], statewide: ['parcels_id_statewide'], counties: [] },
  ME: { bounds: [-71.084, 42.977, -66.949, 47.459], statewide: ['parcels_me_statewide'], counties: [] },
  NH: { bounds: [-72.557, 42.697, -70.610, 45.305], statewide: ['parcels_nh_statewide'], counties: [] },
  RI: { bounds: [-71.907, 41.146, -71.120, 42.019], statewide: ['parcels_ri_statewide'], counties: [] },
  AK: { bounds: [-179.150, 51.214, -129.980, 71.439], statewide: ['parcels_ak_statewide'], counties: [] },
  DE: { bounds: [-75.789, 38.451, -74.984, 39.839], statewide: ['parcels_de_statewide'], counties: [] },
  VT: { bounds: [-73.438, 42.727, -71.465, 45.017], statewide: ['parcels_vt_statewide'], counties: [] },
  WY: { bounds: [-111.056, 40.995, -104.052, 45.006], statewide: ['parcels_wy_statewide'], counties: [] },
  MT: { bounds: [-116.050, 44.358, -104.039, 49.001], statewide: ['parcels_mt_statewide_v2'], counties: [] },
  ND: { bounds: [-104.049, 45.935, -96.554, 49.000], statewide: ['parcels_nd_statewide'], counties: [] },
}

// Check if two bounding boxes intersect
function boundsIntersect(
  bbox1: [number, number, number, number],
  bbox2: [number, number, number, number]
): boolean {
  const [west1, south1, east1, north1] = bbox1
  const [west2, south2, east2, north2] = bbox2

  return !(east1 < west2 || west1 > east2 || north1 < south2 || south1 > north2)
}

export default function MapDemoPage() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const maplibreRef = useRef<any>(null)
  const loadedSourcesRef = useRef<Set<string>>(new Set())
  const [mapStyle, setMapStyle] = useState<'map' | 'satellite' | 'terrain'>('map')
  const [status, setStatus] = useState('Loading map...')
  const [loadedCount, setLoadedCount] = useState(0)
  const [layers, setLayers] = useState({
    parcels: true,
    pois: true,
    buildings: true,
  })

  // Get parcels that should be loaded for current viewport and zoom
  const getParcelsForViewport = (bounds: LngLatBounds, zoom: number): string[] => {
    const viewportBbox: [number, number, number, number] = [
      bounds.getWest() - VIEWPORT_BUFFER,
      bounds.getSouth() - VIEWPORT_BUFFER,
      bounds.getEast() + VIEWPORT_BUFFER,
      bounds.getNorth() + VIEWPORT_BUFFER,
    ]

    const parcelsToLoad: string[] = []

    // Check each state
    Object.entries(PARCEL_INDEX).forEach(([_state, data]) => {
      const stateBounds = data.bounds as [number, number, number, number]

      if (boundsIntersect(stateBounds, viewportBbox)) {
        // Load statewide files at zoom 8+
        if (zoom >= PARCEL_LOAD_ZOOM) {
          parcelsToLoad.push(...data.statewide)
        }

        // Load county files at zoom 11+
        if (zoom >= COUNTY_LOAD_ZOOM) {
          parcelsToLoad.push(...data.counties)
        }
      }
    })

    return parcelsToLoad
  }

  // Load parcel sources in batches
  const loadParcelSources = async (parcelNames: string[]) => {
    if (!map.current) return

    const toLoad = parcelNames.filter((p) => !loadedSourcesRef.current.has(p))
    if (toLoad.length === 0) return

    setStatus(`Loading ${toLoad.length} parcel datasets...`)

    // Load in batches of 5 to avoid overwhelming the browser
    const BATCH_SIZE = 5
    for (let i = 0; i < toLoad.length; i += BATCH_SIZE) {
      const batch = toLoad.slice(i, i + BATCH_SIZE)

      await Promise.all(
        batch.map(async (p) => {
          try {
            if (!map.current || map.current.getSource(p)) return

            map.current.addSource(p, {
              type: 'vector',
              url: `pmtiles://${CDN}/parcels/${p}.pmtiles`,
            })

            map.current.addLayer({
              id: `${p}-fill`,
              type: 'fill',
              source: p,
              'source-layer': 'parcels',
              minzoom: 8,
              paint: {
                'fill-color': '#e53935',
                'fill-opacity': [
                  'interpolate', ['linear'], ['zoom'],
                  8, 0.01,
                  10, 0.1,
                  14, 0.25,
                ],
              },
            })

            map.current.addLayer({
              id: `${p}-line`,
              type: 'line',
              source: p,
              'source-layer': 'parcels',
              minzoom: 12,
              paint: {
                'line-color': '#b71c1c',
                'line-width': ['interpolate', ['linear'], ['zoom'], 12, 0.3, 16, 1.5],
              },
            })

            loadedSourcesRef.current.add(p)
          } catch (e) {
            console.warn(`Failed to load parcel: ${p}`, e)
          }
        })
      )

      setLoadedCount(loadedSourcesRef.current.size)

      // Small delay between batches
      if (i + BATCH_SIZE < toLoad.length) {
        await new Promise((resolve) => setTimeout(resolve, 100))
      }
    }

    setStatus(`Loaded ${loadedSourcesRef.current.size} datasets. Zoom in for details.`)
  }

  // Update parcels based on viewport
  const updateParcels = () => {
    if (!map.current) return

    const zoom = map.current.getZoom()
    if (zoom < PARCEL_LOAD_ZOOM) {
      setStatus('Map ready! Zoom in to see parcels.')
      return
    }

    const bounds = map.current.getBounds()
    const parcelsNeeded = getParcelsForViewport(bounds, zoom)

    loadParcelSources(parcelsNeeded)
  }

  // Toggle parcel visibility
  useEffect(() => {
    if (!map.current || loadedSourcesRef.current.size === 0) return

    const visibility = layers.parcels ? 'visible' : 'none'
    loadedSourcesRef.current.forEach((p) => {
      if (map.current?.getLayer(`${p}-fill`)) {
        map.current.setLayoutProperty(`${p}-fill`, 'visibility', visibility)
      }
      if (map.current?.getLayer(`${p}-line`)) {
        map.current.setLayoutProperty(`${p}-line`, 'visibility', visibility)
      }
    })
  }, [layers.parcels])

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

        // Build map style
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

        // Add controls
        map.current.addControl(new maplibregl.NavigationControl(), 'top-right')
        map.current.addControl(new maplibregl.ScaleControl(), 'bottom-right')

        map.current.on('load', () => {
          map.current?.resize()
          setStatus('Map ready! Zoom in to see parcels.')

          // Single delegated click handler
          map.current?.on('click', (e) => {
            if (!map.current) return

            const parcelLayers = Array.from(loadedSourcesRef.current)
              .map((p) => `${p}-fill`)
              .filter((l) => map.current?.getLayer(l))

            if (parcelLayers.length === 0) return

            const features = map.current.queryRenderedFeatures(e.point, {
              layers: parcelLayers,
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
                .setHTML(
                  `<div style="max-height: 250px; overflow-y: auto; font-size: 12px;">${content}</div>`
                )
                .addTo(map.current!)
            }
          })

          // Cursor changes on hover
          map.current?.on('mousemove', (e) => {
            if (!map.current) return

            const parcelLayers = Array.from(loadedSourcesRef.current)
              .map((p) => `${p}-fill`)
              .filter((l) => map.current?.getLayer(l))

            if (parcelLayers.length === 0) return

            const features = map.current.queryRenderedFeatures(e.point, {
              layers: parcelLayers,
            })

            map.current.getCanvas().style.cursor = features.length > 0 ? 'pointer' : ''
          })

          // Viewport-based loading on move
          map.current?.on('moveend', () => {
            updateParcels()
          })

          // Also update on zoom
          map.current?.on('zoomend', () => {
            updateParcels()
          })

          // Initial load
          updateParcels()
        })

        map.current.on('error', (e) => {
          console.error('Map error:', e)
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
  }, [])

  // Handle map style switching
  useEffect(() => {
    if (!map.current) return

    const m = map.current

    const setLayerVisibility = (layerId: string, visible: boolean) => {
      if (m.getLayer(layerId)) {
        m.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none')
      }
    }

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
      <div className="flex-1 relative overflow-hidden">
        <div ref={mapContainer} className="w-full h-full" />

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
              <span className="text-xs text-muted-foreground ml-auto">
                {loadedCount > 0 ? `${loadedCount} loaded` : '150M+'}
              </span>
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
            <p className="text-xs text-muted-foreground">{status}</p>
          </div>
        </div>

        {/* Info Banner */}
        <div className="absolute bottom-4 left-4 right-4 bg-white/90 backdrop-blur rounded-lg shadow-lg p-4 z-10">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Optimized viewport-based loading</p>
              <p className="text-sm text-muted-foreground">
                Only loads parcels visible in your viewport. Zoom 8+ for statewide, 11+ for counties.
              </p>
            </div>
            <Button asChild>
              <Link href="/signup">Start Building Free</Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

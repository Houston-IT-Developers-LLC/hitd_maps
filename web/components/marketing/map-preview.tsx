'use client'

import { useEffect, useRef, useState } from 'react'
import { ArrowRight } from 'lucide-react'
import 'maplibre-gl/dist/maplibre-gl.css'

const CDN = 'https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev'
const PROTOMAPS_URL = `${CDN}/basemap/protomaps_planet.pmtiles`

// Key parcel files for preview (showing major coverage)
const PREVIEW_PARCELS = [
  'parcels_tx_statewide',
  'parcels_fl_statewide',
  'parcels_ca',
  'parcels_ny_statewide',
  'parcels_pa_statewide',
  'parcels_oh_statewide',
  'parcels_il',
  'parcels_nc_statewide',
  'parcels_ga',
  'parcels_va_statewide',
  'parcels_mi',
  'parcels_wa_statewide',
  'parcels_az',
  'parcels_ma_statewide',
  'parcels_tn_statewide',
  'parcels_md_statewide',
  'parcels_wi_statewide',
  'parcels_mn',
  'parcels_co_statewide',
  'parcels_al',
  'parcels_la',
  'parcels_ky',
  'parcels_or',
  'parcels_ok',
  'parcels_ct_statewide',
  'parcels_ia_statewide',
  'parcels_ms',
  'parcels_ar_statewide',
  'parcels_ks',
  'parcels_ut_statewide',
  'parcels_nv_statewide',
  'parcels_nm_statewide',
  'parcels_ne',
  'parcels_wv_statewide',
  'parcels_id_statewide',
  'parcels_hi_statewide',
  'parcels_nh_statewide',
  'parcels_me_statewide',
  'parcels_mt_statewide',
  'parcels_de_statewide',
  'parcels_sd',
  'parcels_nd_statewide',
  'parcels_ak_statewide',
  'parcels_vt_statewide',
  'parcels_wy',
  'parcels_dc',
]

export function MapPreview() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const [isLoaded, setIsLoaded] = useState(false)
  const [isHovering, setIsHovering] = useState(false)

  useEffect(() => {
    if (!mapContainer.current || map.current) return

    const initMap = async () => {
      try {
        const maplibregl = (await import('maplibre-gl')).default
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
          },
          layers: [...protomapsLayers],
        }

        map.current = new maplibregl.Map({
          container: mapContainer.current!,
          style: mapStyleObj,
          center: [-98.5, 39.8], // Center of USA
          zoom: 4,
          interactive: true, // Enable interaction
          attributionControl: false,
        })

        // Disable rotation for simpler preview
        map.current.dragRotate.disable()
        map.current.touchZoomRotate.disableRotation()

        // Load parcels when map is ready
        map.current.on('load', async () => {
          if (!map.current) return

          // Add all preview parcel sources and layers
          for (const p of PREVIEW_PARCELS) {
            try {
              map.current.addSource(p, {
                type: 'vector',
                url: `pmtiles://${CDN}/parcels/${p}.pmtiles`,
              })

              map.current.addLayer({
                id: `${p}-fill`,
                type: 'fill',
                source: p,
                'source-layer': 'parcels',
                minzoom: 8, // Only show parcels when zoomed in to state/regional level
                paint: {
                  'fill-color': '#e53935',
                  'fill-opacity': [
                    'interpolate',
                    ['linear'],
                    ['zoom'],
                    8, 0.05,
                    10, 0.15,
                    14, 0.3,
                  ],
                },
              })

              map.current.addLayer({
                id: `${p}-line`,
                type: 'line',
                source: p,
                'source-layer': 'parcels',
                minzoom: 12, // Only show parcel boundaries at city/neighborhood level
                paint: {
                  'line-color': '#b71c1c',
                  'line-width': [
                    'interpolate',
                    ['linear'],
                    ['zoom'],
                    12, 0.3,
                    16, 1.5,
                  ],
                },
              })
            } catch (e) {
              console.warn(`Failed to load parcel preview: ${p}`, e)
            }
          }

          setIsLoaded(true)
        })
      } catch (err) {
        console.error('Failed to initialize preview map:', err)
      }
    }

    initMap()

    return () => {
      map.current?.remove()
    }
  }, [])

  // Handle click to open full map
  const handleClick = () => {
    window.open('/map', '_blank')
  }

  return (
    <div
      className="relative cursor-pointer group"
      onClick={handleClick}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      {/* Map Container */}
      <div className="rounded-xl overflow-hidden shadow-2xl border aspect-[16/9] relative">
        <div ref={mapContainer} className="w-full h-full" />

        {/* Overlay with text and hover effect */}
        <div
          className={`absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent flex items-end justify-center pb-12 transition-opacity ${
            isHovering ? 'opacity-100' : 'opacity-90'
          }`}
        >
          <div className="text-center text-white">
            <p className="text-xl font-semibold">Interactive Live Map</p>
            <p className="text-white/90 mt-1">Query 167M+ records in real-time</p>
            <div
              className={`mt-3 inline-flex items-center gap-2 font-medium transition-all ${
                isHovering ? 'gap-3' : 'gap-2'
              }`}
            >
              Explore Live Map
              <ArrowRight className="h-5 w-5" />
            </div>
          </div>
        </div>

        {/* Loading state */}
        {!isLoaded && (
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-blue-100 to-indigo-100">
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">Loading map...</p>
            </div>
          </div>
        )}
      </div>

      {/* Click hint on mobile */}
      <div className="mt-3 text-center text-sm text-muted-foreground md:hidden">
        Tap to open full map
      </div>
    </div>
  )
}

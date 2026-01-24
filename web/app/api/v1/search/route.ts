import { NextRequest, NextResponse } from 'next/server'
import { validateApiKey } from '@/lib/api-keys/validate'
import { trackUsage, checkUsageLimits } from '@/lib/usage/track'

const NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'

export async function GET(request: NextRequest) {
  const apiKey = request.headers.get('x-api-key-provided') || ''
  const query = request.nextUrl.searchParams.get('q')
  const type = request.nextUrl.searchParams.get('type') || 'all' // address, poi, parcel
  const bbox = request.nextUrl.searchParams.get('bbox') // minLon,minLat,maxLon,maxLat
  const limit = request.nextUrl.searchParams.get('limit') || '10'

  if (!query) {
    return NextResponse.json(
      { error: 'Missing query parameter "q"' },
      { status: 400 }
    )
  }

  // Validate API key
  const validation = await validateApiKey(apiKey)
  if (!validation.valid) {
    return NextResponse.json(
      { error: validation.error },
      { status: 403 }
    )
  }

  // Check usage limits
  const usage = await checkUsageLimits(validation.userId!, validation.tier!)
  if (usage.exceeded) {
    return NextResponse.json(
      {
        error: 'Monthly usage limit exceeded',
        current: usage.current,
        limits: usage.limits,
        tier: validation.tier,
      },
      { status: 429 }
    )
  }

  try {
    // Build Nominatim request
    const url = new URL(NOMINATIM_URL)
    url.searchParams.set('q', query)
    url.searchParams.set('format', 'json')
    url.searchParams.set('limit', limit)
    url.searchParams.set('countrycodes', 'us')
    url.searchParams.set('addressdetails', '1')

    if (bbox) {
      url.searchParams.set('viewbox', bbox)
      url.searchParams.set('bounded', '1')
    }

    // Filter by type
    if (type === 'address') {
      url.searchParams.set('featuretype', 'house')
    } else if (type === 'poi') {
      url.searchParams.set('featuretype', 'settlement')
    }

    const response = await fetch(url.toString(), {
      headers: {
        'User-Agent': 'MapsForDevelopers/1.0 (contact@mapsfordevelopers.com)',
      },
    })

    if (!response.ok) {
      throw new Error(`Search failed: ${response.status}`)
    }

    const results = await response.json()

    // Track usage
    trackUsage({
      userId: validation.userId!,
      apiKeyId: validation.keyId!,
      endpoint: '/api/v1/search',
    }).catch(console.error)

    // Transform and enhance results
    const transformedResults = results.map((result: Record<string, unknown>) => ({
      id: result.place_id,
      lat: parseFloat(result.lat as string),
      lon: parseFloat(result.lon as string),
      name: result.display_name,
      type: result.type,
      category: result.class,
      address: result.address,
      bbox: result.boundingbox,
      importance: result.importance,
    }))

    return NextResponse.json({
      results: transformedResults,
      query,
      type,
      count: transformedResults.length,
      bbox: bbox || null,
    })
  } catch (error) {
    console.error('Search error:', error)
    return NextResponse.json(
      { error: 'Search failed' },
      { status: 500 }
    )
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'X-API-Key, Content-Type',
    },
  })
}

import { NextRequest, NextResponse } from 'next/server'
import { validateApiKey } from '@/lib/api-keys/validate'
import { trackUsage, checkUsageLimits } from '@/lib/usage/track'

const NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'

export async function GET(request: NextRequest) {
  const apiKey = request.headers.get('x-api-key-provided') || ''
  const query = request.nextUrl.searchParams.get('q')
  const limit = request.nextUrl.searchParams.get('limit') || '5'

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

  // Check permissions
  if (!validation.permissions?.geocode) {
    return NextResponse.json(
      { error: 'API key does not have geocode access permission' },
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
    // Forward to Nominatim
    const url = new URL(NOMINATIM_URL)
    url.searchParams.set('q', query)
    url.searchParams.set('format', 'json')
    url.searchParams.set('limit', limit)
    url.searchParams.set('countrycodes', 'us') // USA only
    url.searchParams.set('addressdetails', '1')

    const response = await fetch(url.toString(), {
      headers: {
        'User-Agent': 'MapsForDevelopers/1.0 (contact@mapsfordevelopers.com)',
      },
    })

    if (!response.ok) {
      throw new Error(`Nominatim returned ${response.status}`)
    }

    const results = await response.json()

    // Track usage
    trackUsage({
      userId: validation.userId!,
      apiKeyId: validation.keyId!,
      endpoint: '/api/v1/geocode',
    }).catch(console.error)

    // Transform results
    const transformedResults = results.map((result: Record<string, unknown>) => ({
      lat: parseFloat(result.lat as string),
      lon: parseFloat(result.lon as string),
      display_name: result.display_name,
      type: result.type,
      address: result.address,
      boundingbox: result.boundingbox,
    }))

    return NextResponse.json({
      results: transformedResults,
      query,
      count: transformedResults.length,
    })
  } catch (error) {
    console.error('Geocode error:', error)
    return NextResponse.json(
      { error: 'Geocoding failed' },
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

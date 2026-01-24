import { NextRequest, NextResponse } from 'next/server'
import { validateApiKey } from '@/lib/api-keys/validate'
import { trackUsage, checkUsageLimits } from '@/lib/usage/track'

const R2_CDN = process.env.R2_CDN_URL || 'https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params
  const apiKey = request.headers.get('x-api-key-provided') || ''

  // Validate API key
  const validation = await validateApiKey(apiKey)
  if (!validation.valid) {
    return NextResponse.json(
      { error: validation.error },
      { status: 403 }
    )
  }

  // Check permissions
  if (!validation.permissions?.tiles) {
    return NextResponse.json(
      { error: 'API key does not have tile access permission' },
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

  // Build the R2 URL
  const tilePath = path.join('/')
  const r2Url = `${R2_CDN}/${tilePath}`

  try {
    // Fetch from R2
    const response = await fetch(r2Url, {
      headers: {
        'Accept-Encoding': 'gzip, deflate, br',
      },
    })

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { error: 'Tile not found' },
          { status: 404 }
        )
      }
      throw new Error(`R2 returned ${response.status}`)
    }

    const contentLength = response.headers.get('content-length')
    const bytesTransferred = contentLength ? parseInt(contentLength, 10) : 0

    // Track usage asynchronously (don't await)
    trackUsage({
      userId: validation.userId!,
      apiKeyId: validation.keyId!,
      endpoint: `/api/v1/tiles/${tilePath}`,
      bytesTransferred,
    }).catch(console.error)

    // Determine content type based on path
    let contentType = 'application/octet-stream'
    if (tilePath.endsWith('.pbf')) {
      contentType = 'application/x-protobuf'
    } else if (tilePath.endsWith('.pmtiles')) {
      contentType = 'application/octet-stream'
    } else if (tilePath.endsWith('.png')) {
      contentType = 'image/png'
    } else if (tilePath.endsWith('.jpg') || tilePath.endsWith('.jpeg')) {
      contentType = 'image/jpeg'
    } else if (tilePath.endsWith('.webp')) {
      contentType = 'image/webp'
    }

    // Return tile with caching headers
    return new NextResponse(response.body, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=86400, stale-while-revalidate=604800',
        'Access-Control-Allow-Origin': '*',
        'X-Tiles-Remaining': String(
          Math.max(0, usage.limits.tiles - usage.current.tiles)
        ),
      },
    })
  } catch (error) {
    console.error('Tile fetch error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch tile' },
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
      'Access-Control-Max-Age': '86400',
    },
  })
}

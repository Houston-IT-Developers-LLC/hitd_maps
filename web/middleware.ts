import { type NextRequest, NextResponse } from 'next/server'
import { updateSession } from '@/lib/supabase/middleware'

export async function middleware(request: NextRequest) {
  // Handle API key authentication for /api/v1/* routes
  if (request.nextUrl.pathname.startsWith('/api/v1/')) {
    const apiKey = request.headers.get('x-api-key') ||
                   request.nextUrl.searchParams.get('api_key')

    if (!apiKey) {
      return NextResponse.json(
        { error: 'API key required. Pass via x-api-key header or api_key query param.' },
        { status: 401 }
      )
    }

    // API key validation happens in the route handlers
    // Pass the key forward in a header for the route to validate
    const requestHeaders = new Headers(request.headers)
    requestHeaders.set('x-api-key-provided', apiKey)

    return NextResponse.next({
      request: {
        headers: requestHeaders,
      },
    })
  }

  // Handle session updates for authenticated routes
  return await updateSession(request)
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (public folder)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}

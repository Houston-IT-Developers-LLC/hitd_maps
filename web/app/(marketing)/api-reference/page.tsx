import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Header } from '@/components/marketing/header'
import { Footer } from '@/components/marketing/footer'
import {
  ArrowRight,
  Key,
  Globe,
  Zap,
  Shield,
  Clock,
  FileJson,
  Code,
  Layers,
} from 'lucide-react'

export const metadata = {
  title: 'API Reference - Maps for Developers',
  description: 'Complete API documentation. RESTful endpoints, authentication, rate limits, and response formats for the Maps for Developers platform.',
}

export default function ApiReferencePage() {
  const endpoints = [
    {
      method: 'GET',
      path: '/v1/tiles/{layer}/{z}/{x}/{y}',
      description: 'Retrieve vector tiles for a specific layer and tile coordinates',
      params: ['layer: parcels, pois, terrain, satellite', 'z: zoom level (0-22)', 'x, y: tile coordinates'],
    },
    {
      method: 'GET',
      path: '/v1/geocode',
      description: 'Convert addresses to coordinates (forward geocoding)',
      params: ['q: address string', 'limit: max results (default 5)'],
    },
    {
      method: 'GET',
      path: '/v1/reverse',
      description: 'Convert coordinates to addresses (reverse geocoding)',
      params: ['lat: latitude', 'lon: longitude'],
    },
    {
      method: 'GET',
      path: '/v1/search',
      description: 'Search POIs and parcels by query',
      params: ['q: search query', 'type: poi, parcel, address', 'bbox: bounding box'],
    },
    {
      method: 'GET',
      path: '/v1/parcel/{id}',
      description: 'Get detailed parcel information by ID',
      params: ['id: parcel identifier'],
    },
  ]

  const rateLimits = [
    { plan: 'Free', requests: '1,000/day', burst: '10/sec' },
    { plan: 'Developer', requests: '100,000/day', burst: '100/sec' },
    { plan: 'Enterprise', requests: 'Unlimited', burst: 'Custom' },
  ]

  return (
    <div className="min-h-screen">
      <Header />

      {/* Hero */}
      <section className="py-20 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold">
            API Reference
          </h1>
          <p className="mt-4 text-xl text-muted-foreground max-w-2xl mx-auto">
            RESTful API with predictable endpoints, consistent responses, and comprehensive documentation.
          </p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Button size="lg" asChild>
              <Link href="/signup">
                Get API Key
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <a href="https://docs.mapsfordevelopers.com" target="_blank" rel="noopener noreferrer">
                Full Documentation
              </a>
            </Button>
          </div>
        </div>
      </section>

      {/* Authentication */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-start">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                  <Key className="h-5 w-5 text-primary" />
                </div>
                <h2 className="text-3xl font-bold">Authentication</h2>
              </div>
              <p className="text-lg text-muted-foreground mb-6">
                All API requests require authentication via API key. Include your key in the request header.
              </p>
              <ul className="space-y-3 text-muted-foreground">
                <li className="flex items-start gap-2">
                  <Shield className="h-5 w-5 text-primary mt-0.5" />
                  <span>API keys are scoped to your account</span>
                </li>
                <li className="flex items-start gap-2">
                  <Shield className="h-5 w-5 text-primary mt-0.5" />
                  <span>Rotate keys anytime from your dashboard</span>
                </li>
                <li className="flex items-start gap-2">
                  <Shield className="h-5 w-5 text-primary mt-0.5" />
                  <span>Separate keys for development and production</span>
                </li>
              </ul>
            </div>
            <div className="bg-gray-900 rounded-xl p-6 overflow-x-auto">
              <div className="text-xs text-gray-500 mb-2">Request Header</div>
              <pre className="text-sm text-gray-300 font-mono">
                <code>{`Authorization: Bearer mfd_live_xxxxxxxxxxxxx

// Or as query parameter
GET /v1/tiles/parcels/12/1234/2345?api_key=mfd_live_xxxxx`}</code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* Endpoints */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold">Core Endpoints</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Base URL: <code className="bg-gray-200 px-2 py-1 rounded text-sm">https://api.mapsfordevelopers.com</code>
            </p>
          </div>

          <div className="space-y-4">
            {endpoints.map((endpoint, i) => (
              <Card key={i}>
                <CardContent className="pt-6">
                  <div className="flex flex-wrap items-start gap-4">
                    <span className={`px-3 py-1 rounded text-sm font-mono font-medium ${
                      endpoint.method === 'GET' ? 'bg-green-100 text-green-700' :
                      endpoint.method === 'POST' ? 'bg-blue-100 text-blue-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {endpoint.method}
                    </span>
                    <code className="text-sm bg-gray-100 px-3 py-1 rounded font-mono flex-1">
                      {endpoint.path}
                    </code>
                  </div>
                  <p className="mt-4 text-muted-foreground">{endpoint.description}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {endpoint.params.map((param, j) => (
                      <span key={j} className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {param}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Response Format */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-start">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                  <FileJson className="h-5 w-5 text-primary" />
                </div>
                <h2 className="text-3xl font-bold">Response Format</h2>
              </div>
              <p className="text-lg text-muted-foreground mb-6">
                All responses are JSON with consistent structure. Tile endpoints return Protobuf for optimal performance.
              </p>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <Zap className="h-5 w-5 text-primary" />
                  <span>Gzip compression enabled by default</span>
                </div>
                <div className="flex items-center gap-3">
                  <Globe className="h-5 w-5 text-primary" />
                  <span>CORS enabled for browser requests</span>
                </div>
                <div className="flex items-center gap-3">
                  <Clock className="h-5 w-5 text-primary" />
                  <span>Cache headers for optimal performance</span>
                </div>
              </div>
            </div>
            <div className="bg-gray-900 rounded-xl p-6 overflow-x-auto">
              <div className="text-xs text-gray-500 mb-2">Example Response</div>
              <pre className="text-sm text-gray-300 font-mono">
                <code>{`{
  "success": true,
  "data": {
    "parcel_id": "TX-DAL-123456",
    "owner": "John Smith",
    "address": "123 Main St",
    "city": "Dallas",
    "state": "TX",
    "assessed_value": 450000,
    "lot_size_sqft": 8500,
    "year_built": 1985,
    "geometry": { "type": "Polygon", ... }
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}`}</code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* Rate Limits */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold">Rate Limits</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Generous limits with clear overage pricing. No surprise bills.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {rateLimits.map((limit) => (
              <Card key={limit.plan}>
                <CardHeader>
                  <CardTitle>{limit.plan}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="text-sm text-muted-foreground">Daily Requests</div>
                      <div className="text-2xl font-bold">{limit.requests}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Burst Rate</div>
                      <div className="text-lg font-medium">{limit.burst}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="mt-8 text-center text-muted-foreground">
            <p>Rate limit headers included in every response: <code className="bg-gray-200 px-2 py-0.5 rounded text-sm">X-RateLimit-Remaining</code></p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold">Ready to integrate?</h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Get your API key and start building in minutes
          </p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Button size="lg" asChild>
              <Link href="/signup">
                Get Started Free
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/quickstart">View Quickstart</Link>
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Header } from '@/components/marketing/header'
import { Footer } from '@/components/marketing/footer'
import {
  ArrowRight,
  Book,
  Code,
  Zap,
  Terminal,
  FileJson,
  Layers,
  Map,
  Search,
  Key,
} from 'lucide-react'

export const metadata = {
  title: 'Documentation - Maps for Developers',
  description: 'Complete documentation for the Maps for Developers API. Guides, tutorials, API reference, and SDK documentation.',
}

export default function DocsPage() {
  const sections = [
    {
      icon: Zap,
      title: 'Quickstart',
      description: 'Get up and running in minutes with our step-by-step guides',
      href: '/quickstart',
      links: [
        { label: 'JavaScript SDK', href: '/quickstart#javascript' },
        { label: 'React SDK', href: '/quickstart#react' },
        { label: 'React Native', href: '/quickstart#react-native' },
        { label: 'iOS & Android', href: '/quickstart#ios-(swift)' },
      ],
    },
    {
      icon: FileJson,
      title: 'API Reference',
      description: 'Complete REST API documentation with endpoints and examples',
      href: '/api-reference',
      links: [
        { label: 'Authentication', href: '/api-reference#authentication' },
        { label: 'Tile Endpoints', href: '/api-reference#endpoints' },
        { label: 'Geocoding', href: '/api-reference#endpoints' },
        { label: 'Rate Limits', href: '/api-reference#rate-limits' },
      ],
    },
    {
      icon: Layers,
      title: 'Data Layers',
      description: 'Learn about available data layers and their properties',
      href: '/features',
      links: [
        { label: 'Property Parcels', href: '/features#parcels' },
        { label: 'Points of Interest', href: '/features#pois' },
        { label: 'Building Footprints', href: '/features#buildings' },
        { label: 'Terrain & Satellite', href: '/features#terrain' },
      ],
    },
    {
      icon: Map,
      title: 'Map Styling',
      description: 'Customize map appearance with styles and themes',
      href: '#styling',
      links: [
        { label: 'Style Specification', href: '#style-spec' },
        { label: 'Custom Themes', href: '#themes' },
        { label: 'Layer Visibility', href: '#layers' },
        { label: 'Interactive Features', href: '#interactions' },
      ],
    },
    {
      icon: Search,
      title: 'Geocoding',
      description: 'Convert addresses to coordinates and vice versa',
      href: '/api-reference#geocoding',
      links: [
        { label: 'Forward Geocoding', href: '/api-reference#geocoding' },
        { label: 'Reverse Geocoding', href: '/api-reference#reverse' },
        { label: 'Batch Geocoding', href: '#batch' },
        { label: 'Address Validation', href: '#validation' },
      ],
    },
    {
      icon: Key,
      title: 'Authentication',
      description: 'API keys, scopes, and security best practices',
      href: '/api-reference#authentication',
      links: [
        { label: 'API Keys', href: '/api-reference#authentication' },
        { label: 'Key Rotation', href: '#rotation' },
        { label: 'Scopes & Permissions', href: '#scopes' },
        { label: 'Security Best Practices', href: '#security' },
      ],
    },
  ]

  const guides = [
    {
      title: 'Display Property Parcels',
      description: 'Add interactive property boundaries to your map',
      time: '5 min',
    },
    {
      title: 'Search for Addresses',
      description: 'Implement geocoding search with autocomplete',
      time: '10 min',
    },
    {
      title: 'Add Custom Markers',
      description: 'Display custom markers and popups on the map',
      time: '5 min',
    },
    {
      title: 'Offline Maps',
      description: 'Download and cache tiles for offline use',
      time: '15 min',
    },
  ]

  return (
    <div className="min-h-screen">
      <Header />

      {/* Hero */}
      <section className="py-20 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <Book className="h-8 w-8 text-primary" />
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold">
            Documentation
          </h1>
          <p className="mt-4 text-xl text-muted-foreground max-w-2xl mx-auto">
            Everything you need to integrate Maps for Developers into your application.
            Guides, API reference, and SDK documentation.
          </p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Button size="lg" asChild>
              <Link href="/quickstart">
                Get Started
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/api-reference">API Reference</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Quick Links */}
      <section className="py-12 bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-center justify-center gap-4">
            <span className="text-gray-400">Jump to:</span>
            <Link href="/quickstart" className="px-4 py-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors">
              Quickstart
            </Link>
            <Link href="/api-reference" className="px-4 py-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors">
              API Reference
            </Link>
            <Link href="/features" className="px-4 py-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors">
              Data Layers
            </Link>
            <Link href="/use-cases" className="px-4 py-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors">
              Use Cases
            </Link>
          </div>
        </div>
      </section>

      {/* Documentation Sections */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {sections.map((section) => (
              <Card key={section.title} className="h-full">
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <section.icon className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle>
                    <Link href={section.href} className="hover:text-primary transition-colors">
                      {section.title}
                    </Link>
                  </CardTitle>
                  <CardDescription>{section.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {section.links.map((link) => (
                      <li key={link.label}>
                        <Link
                          href={link.href}
                          className="text-sm text-muted-foreground hover:text-primary transition-colors"
                        >
                          {link.label}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Popular Guides */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold">Popular Guides</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Step-by-step tutorials for common use cases
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {guides.map((guide) => (
              <Card key={guide.title} className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                    <Terminal className="h-3 w-3" />
                    <span>{guide.time} read</span>
                  </div>
                  <h3 className="font-semibold mb-1">{guide.title}</h3>
                  <p className="text-sm text-muted-foreground">{guide.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold">Simple Integration</h2>
              <p className="mt-4 text-lg text-muted-foreground">
                Add a fully interactive map with property parcels in just a few lines of code.
                Our SDKs handle authentication, caching, and performance optimization.
              </p>
              <ul className="mt-6 space-y-3">
                <li className="flex items-center gap-2 text-sm">
                  <Code className="h-4 w-4 text-primary" />
                  Full TypeScript support
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Code className="h-4 w-4 text-primary" />
                  Tree-shakable for minimal bundle size
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Code className="h-4 w-4 text-primary" />
                  SSR compatible
                </li>
              </ul>
              <Button className="mt-8" asChild>
                <Link href="/quickstart">
                  View All Examples
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
            <div className="bg-gray-900 rounded-xl p-6 overflow-x-auto">
              <pre className="text-sm text-gray-300 font-mono">
                <code>{`import { Map, ParcelLayer } from '@mapsfordevelopers/react'

export default function PropertyMap() {
  return (
    <Map
      apiKey="YOUR_API_KEY"
      center={[-95.37, 29.76]}
      zoom={14}
    >
      <ParcelLayer
        onClick={(parcel) => {
          console.log('Owner:', parcel.properties.owner)
          console.log('Value:', parcel.properties.assessed_value)
        }}
      />
    </Map>
  )
}`}</code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-primary text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold">Ready to start building?</h2>
          <p className="mt-4 text-lg text-blue-100">
            Get your API key and start integrating in minutes.
          </p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Button size="lg" variant="secondary" asChild>
              <Link href="/signup">
                Get API Key
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" className="bg-transparent border-white text-white hover:bg-white/10" asChild>
              <Link href="/quickstart">Quickstart Guide</Link>
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}

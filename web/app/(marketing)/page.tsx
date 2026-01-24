import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  MapPin,
  ArrowRight,
  Layers,
  Globe,
  Download,
  Zap,
  Shield,
  Code,
  Building,
  Mountain,
  Satellite,
  Navigation,
} from 'lucide-react'

export default function LandingPage() {
  const features = [
    {
      icon: Building,
      title: 'Property Parcels',
      description: '150M+ parcels covering 47 states + DC with owner info, values, and boundaries',
    },
    {
      icon: MapPin,
      title: '17M+ POIs',
      description: 'Businesses, restaurants, hospitals, schools, and more with detailed attributes',
    },
    {
      icon: Mountain,
      title: '3D Terrain',
      description: 'High-resolution elevation data with hillshade for immersive experiences',
    },
    {
      icon: Satellite,
      title: 'Satellite Imagery',
      description: 'Up-to-date aerial imagery from multiple sources',
    },
    {
      icon: Download,
      title: 'Offline Support',
      description: 'Download map packages for offline use in mobile apps',
    },
    {
      icon: Zap,
      title: 'Zero Egress Fees',
      description: 'Powered by Cloudflare R2 - no surprise bandwidth bills',
    },
  ]

  const stats = [
    { value: '680GB', label: 'Map Data' },
    { value: '150M+', label: 'Property Parcels' },
    { value: '17M+', label: 'Points of Interest' },
    { value: '47', label: 'States Covered' },
  ]

  const codeExample = `import { MapsForDevelopers } from '@mapsfordevelopers/js'

const map = new MapsForDevelopers({
  apiKey: 'mfd_live_xxxxx',
  container: 'map',
  center: [-95.37, 29.76],
  zoom: 12,
  layers: ['parcels', 'pois', 'terrain']
})

map.on('click', 'parcels', (e) => {
  console.log('Clicked parcel:', e.features[0].properties)
})`

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <MapPin className="h-8 w-8 text-primary" />
              <span className="font-bold text-xl">Maps for Developers</span>
            </Link>
            <div className="hidden md:flex items-center gap-8">
              <Link href="/features" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                Features
              </Link>
              <Link href="/pricing" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                Pricing
              </Link>
              <Link href="/docs" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                Docs
              </Link>
              <Link href="/map" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                Demo
              </Link>
            </div>
            <div className="flex items-center gap-4">
              <Button variant="ghost" asChild>
                <Link href="/login">Log in</Link>
              </Button>
              <Button asChild>
                <Link href="/signup">Get Started</Link>
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-b from-blue-50 to-white py-20 sm:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-5xl sm:text-6xl font-bold tracking-tight">
              The Maps API for{' '}
              <span className="text-primary">Developers</span>
            </h1>
            <p className="mt-6 text-xl text-muted-foreground">
              Build stunning map experiences with 680GB of data. Property parcels,
              POIs, 3D terrain, satellite imagery, and offline support.
              No surprise bills.
            </p>
            <div className="mt-10 flex items-center justify-center gap-4">
              <Button size="lg" asChild>
                <Link href="/signup">
                  Get Started Free
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link href="/map">
                  View Demo
                </Link>
              </Button>
            </div>
          </div>

          {/* Map Preview - Static Image with CTA */}
          <div className="mt-16 relative max-w-5xl mx-auto">
            <Link href="/map" className="block group">
              <div className="rounded-xl overflow-hidden shadow-2xl border bg-gradient-to-br from-blue-100 to-indigo-100 aspect-[16/9] relative">
                {/* Decorative map illustration */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-24 h-24 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-primary/30 transition-colors">
                      <MapPin className="h-12 w-12 text-primary" />
                    </div>
                    <p className="text-xl font-semibold text-gray-800">Interactive Map Demo</p>
                    <p className="text-muted-foreground mt-2">Click to explore 680GB of map data</p>
                    <div className="mt-4 inline-flex items-center gap-2 text-primary font-medium group-hover:gap-3 transition-all">
                      Try the Demo
                      <ArrowRight className="h-5 w-5" />
                    </div>
                  </div>
                </div>
                {/* Decorative grid pattern */}
                <div className="absolute inset-0 opacity-10">
                  <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                      <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                        <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="1"/>
                      </pattern>
                    </defs>
                    <rect width="100%" height="100%" fill="url(#grid)" />
                  </svg>
                </div>
              </div>
            </Link>
            {/* Feature badges */}
            <div className="flex flex-wrap justify-center gap-3 mt-6">
              <span className="inline-flex items-center gap-1.5 bg-white border rounded-full px-4 py-2 text-sm font-medium shadow-sm">
                <Building className="h-4 w-4 text-primary" />
                Property Parcels
              </span>
              <span className="inline-flex items-center gap-1.5 bg-white border rounded-full px-4 py-2 text-sm font-medium shadow-sm">
                <Mountain className="h-4 w-4 text-primary" />
                3D Terrain
              </span>
              <span className="inline-flex items-center gap-1.5 bg-white border rounded-full px-4 py-2 text-sm font-medium shadow-sm">
                <Satellite className="h-4 w-4 text-primary" />
                Satellite
              </span>
              <span className="inline-flex items-center gap-1.5 bg-white border rounded-full px-4 py-2 text-sm font-medium shadow-sm">
                <Layers className="h-4 w-4 text-primary" />
                17M+ POIs
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-4xl font-bold text-primary">{stat.value}</div>
                <div className="mt-2 text-gray-400">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl font-bold">Everything you need to build</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Comprehensive data layers, developer-friendly APIs, and SDKs for every platform
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature) => (
              <Card key={feature.title}>
                <CardContent className="pt-6">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <feature.icon className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold">{feature.title}</h3>
                  <p className="mt-2 text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold">Simple, powerful API</h2>
              <p className="mt-4 text-lg text-muted-foreground">
                Get started in minutes with our JavaScript SDK. Add property parcels,
                POIs, terrain, and more with just a few lines of code.
              </p>
              <ul className="mt-8 space-y-4">
                <li className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                    <Code className="h-4 w-4 text-primary" />
                  </div>
                  <span>SDKs for JavaScript, React, React Native, Flutter, iOS, Android</span>
                </li>
                <li className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                    <Globe className="h-4 w-4 text-primary" />
                  </div>
                  <span>RESTful API with comprehensive documentation</span>
                </li>
                <li className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                    <Shield className="h-4 w-4 text-primary" />
                  </div>
                  <span>Enterprise-grade security and reliability</span>
                </li>
              </ul>
              <Button className="mt-8" asChild>
                <Link href="/docs">
                  Read the docs
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
            <div className="bg-gray-900 rounded-xl p-6 overflow-x-auto">
              <pre className="text-sm text-gray-300 font-mono">
                <code>{codeExample}</code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-primary rounded-2xl p-12 text-center text-white">
            <h2 className="text-3xl font-bold">Ready to build?</h2>
            <p className="mt-4 text-lg text-blue-100 max-w-2xl mx-auto">
              Start with our free tier - no credit card required.
              Upgrade when you&apos;re ready to scale.
            </p>
            <div className="mt-8 flex items-center justify-center gap-4">
              <Button size="lg" variant="secondary" asChild>
                <Link href="/signup">
                  Get Started Free
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" className="bg-transparent border-white text-white hover:bg-white/10" asChild>
                <Link href="/pricing">
                  View Pricing
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 text-white">
                <MapPin className="h-6 w-6" />
                <span className="font-bold">Maps for Developers</span>
              </div>
              <p className="mt-4 text-sm">
                The most developer-friendly maps API.
                Built for modern applications.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/features" className="hover:text-white">Features</Link></li>
                <li><Link href="/pricing" className="hover:text-white">Pricing</Link></li>
                <li><Link href="/docs" className="hover:text-white">Documentation</Link></li>
                <li><Link href="/map" className="hover:text-white">Demo</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Compare</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/alternatives/google-maps" className="hover:text-white">vs Google Maps</Link></li>
                <li><Link href="/alternatives/mapbox" className="hover:text-white">vs Mapbox</Link></li>
                <li><Link href="/alternatives/here-maps" className="hover:text-white">vs HERE Maps</Link></li>
                <li><Link href="/alternatives/maptiler" className="hover:text-white">vs MapTiler</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/about" className="hover:text-white">About</Link></li>
                <li><Link href="/contact" className="hover:text-white">Contact</Link></li>
                <li><Link href="/privacy" className="hover:text-white">Privacy</Link></li>
                <li><Link href="/terms" className="hover:text-white">Terms</Link></li>
              </ul>
            </div>
          </div>
          <div className="mt-12 pt-8 border-t border-gray-800 text-sm text-center">
            &copy; {new Date().getFullYear()} Maps for Developers. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}

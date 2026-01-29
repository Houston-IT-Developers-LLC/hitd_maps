import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Header } from '@/components/marketing/header'
import { Footer } from '@/components/marketing/footer'
import { MapPreview } from '@/components/marketing/map-preview'
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
} from 'lucide-react'

export default function LandingPage() {
  const features = [
    {
      icon: Building,
      title: 'Property Parcels',
      description: '150M+ parcels covering 47 states + DC with owner info, assessed values, and legal boundaries',
    },
    {
      icon: MapPin,
      title: '17M+ POIs',
      description: 'Verified business listings, restaurants, hospitals, schools with rich metadata',
    },
    {
      icon: Mountain,
      title: '3D Terrain',
      description: 'High-resolution elevation data with hillshade rendering for immersive visualization',
    },
    {
      icon: Satellite,
      title: 'Satellite Imagery',
      description: 'Current aerial imagery updated regularly for accurate visual context',
    },
    {
      icon: Download,
      title: 'Offline Support',
      description: 'Enterprise-grade offline packages for field applications and mobile deployment',
    },
    {
      icon: Zap,
      title: 'Predictable Pricing',
      description: 'Zero egress fees and transparent pricing - no surprise bills at scale',
    },
  ]

  const stats = [
    { value: '167M+', label: 'Total Records' },
    { value: '150M+', label: 'Property Parcels' },
    { value: '17M+', label: 'Points of Interest' },
    { value: '47', label: 'States + DC' },
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
      <Header />

      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-b from-blue-50 to-white py-20 sm:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-5xl sm:text-6xl font-bold tracking-tight">
              The Maps API for{' '}
              <span className="text-primary">Developers</span>
            </h1>
            <p className="mt-6 text-xl text-muted-foreground">
              Access 167M+ verified records through our enterprise-grade API.
              Property parcels, POIs, 3D terrain, and satellite imagery.
              Trusted by thousands of developers.
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
                  Live Map
                </Link>
              </Button>
            </div>
          </div>

          {/* Interactive Map Preview */}
          <div className="mt-16 relative max-w-5xl mx-auto">
            <MapPreview />
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
            <h2 className="text-3xl font-bold">Enterprise-Grade Data Platform</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Production-ready data layers, battle-tested APIs, and native SDKs for every platform
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
              <h2 className="text-3xl font-bold">Built for Production</h2>
              <p className="mt-4 text-lg text-muted-foreground">
                Integrate in minutes with our battle-tested SDKs. Add property parcels,
                POIs, terrain, and more with just a few lines of code.
              </p>
              <ul className="mt-8 space-y-4">
                <li className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                    <Code className="h-4 w-4 text-primary" />
                  </div>
                  <span>Native SDKs for JavaScript, React, React Native, Flutter, iOS, Android</span>
                </li>
                <li className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                    <Globe className="h-4 w-4 text-primary" />
                  </div>
                  <span>RESTful API with 99.9% uptime SLA</span>
                </li>
                <li className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                    <Shield className="h-4 w-4 text-primary" />
                  </div>
                  <span>Global CDN with edge caching for low-latency responses</span>
                </li>
              </ul>
              <Button className="mt-8" asChild>
                <Link href="/docs">
                  Read the Docs
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
            <h2 className="text-3xl font-bold">Join Thousands of Developers</h2>
            <p className="mt-4 text-lg text-blue-100 max-w-2xl mx-auto">
              Start building today with our free tier. No credit card required.
              Scale seamlessly as your application grows.
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

      <Footer />
    </div>
  )
}

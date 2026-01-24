import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Header } from '@/components/marketing/header'
import { Footer } from '@/components/marketing/footer'
import {
  MapPin,
  ArrowRight,
  Building,
  Navigation,
  Mountain,
  Satellite,
  Download,
  Layers,
  Shield,
  Trees,
  Droplets,
  School,
  Hospital,
  Building2,
  Flame,
  Train,
} from 'lucide-react'

export const metadata = {
  title: 'Features',
  description: 'Comprehensive map data for developers. Property parcels, POIs, terrain, satellite imagery, and more.',
}

export default function FeaturesPage() {
  const dataLayers = [
    {
      icon: Building,
      title: 'Property Parcels',
      description: '150M+ property boundaries across 47 states + DC',
      details: [
        'Owner names and addresses',
        'Property values and assessments',
        'Lot sizes and dimensions',
        'Zoning information',
        'Year built and improvements',
      ],
    },
    {
      icon: MapPin,
      title: 'Points of Interest',
      description: '17M+ businesses, restaurants, services, and landmarks',
      details: [
        'Business names and categories',
        'Addresses and coordinates',
        'Phone numbers and websites',
        'Hours of operation',
        'Ratings and reviews',
      ],
    },
    {
      icon: Building2,
      title: 'Building Footprints',
      description: 'Accurate building outlines for the entire USA',
      details: [
        '3D extrusion support',
        'Building heights',
        'Roof types',
        'Construction dates',
        'Building classifications',
      ],
    },
    {
      icon: Navigation,
      title: 'Addresses',
      description: 'Comprehensive address database with geocoding',
      details: [
        'Full street addresses',
        'Unit and suite numbers',
        'Postal codes',
        'Coordinate precision',
        'Address validation',
      ],
    },
  ]

  const infrastructure = [
    {
      icon: Hospital,
      title: 'Hospitals',
      count: '8,000+',
      description: 'Medical facilities with bed counts and specialties',
    },
    {
      icon: School,
      title: 'Schools',
      count: '125,000+',
      description: 'K-12 schools, both public and private',
    },
    {
      icon: Building2,
      title: 'Colleges',
      count: '6,600+',
      description: 'Universities and community colleges',
    },
    {
      icon: Shield,
      title: 'Police Stations',
      count: '18,000+',
      description: 'Law enforcement facilities',
    },
    {
      icon: Flame,
      title: 'Fire & EMS',
      count: '3,600+',
      description: 'Fire departments and emergency services',
    },
    {
      icon: Train,
      title: 'Transit',
      count: 'Growing',
      description: 'Bus routes, rail lines, and stops',
    },
  ]

  const environment = [
    {
      icon: Trees,
      title: 'Public Lands (PAD-US)',
      description: 'National parks, forests, BLM lands, wildlife refuges',
    },
    {
      icon: Droplets,
      title: 'Water Bodies',
      description: 'Rivers, lakes, streams, and coastal features',
    },
    {
      icon: Layers,
      title: 'Wetlands',
      description: 'National Wetlands Inventory data',
    },
    {
      icon: Flame,
      title: 'Fire Perimeters',
      description: 'Historical wildfire boundaries',
    },
  ]

  return (
    <div className="min-h-screen">
      <Header />

      {/* Hero */}
      <section className="py-20 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold">
            680GB of map data at your fingertips
          </h1>
          <p className="mt-4 text-xl text-muted-foreground max-w-2xl mx-auto">
            The most comprehensive maps API for developers. Property data, POIs,
            terrain, satellite imagery, and more. Always up-to-date.
          </p>
          <Button size="lg" className="mt-8" asChild>
            <Link href="/signup">
              Start Building Free
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </Button>
        </div>
      </section>

      {/* Core Data Layers */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold">Core Data Layers</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Rich, detailed data for every use case
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {dataLayers.map((layer) => (
              <Card key={layer.title}>
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <layer.icon className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle>{layer.title}</CardTitle>
                  <CardDescription>{layer.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {layer.details.map((detail) => (
                      <li key={detail} className="flex items-center gap-2 text-sm">
                        <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                        {detail}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Terrain & Imagery */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold">3D Terrain & Satellite</h2>
              <p className="mt-4 text-lg text-muted-foreground">
                Bring your maps to life with high-resolution terrain data and
                satellite imagery.
              </p>
              <div className="mt-8 space-y-6">
                <div className="flex gap-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Mountain className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold">3D Terrain</h3>
                    <p className="text-muted-foreground">
                      High-resolution elevation data with hillshade for immersive
                      terrain visualization.
                    </p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Satellite className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Satellite Imagery</h3>
                    <p className="text-muted-foreground">
                      Up-to-date aerial imagery from multiple sources for detailed
                      visual context.
                    </p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Download className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Offline Support</h3>
                    <p className="text-muted-foreground">
                      Download map packages for offline use in mobile applications.
                      Perfect for fieldwork.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-gray-200 rounded-xl aspect-square flex items-center justify-center">
              <span className="text-muted-foreground">3D Terrain Preview</span>
            </div>
          </div>
        </div>
      </section>

      {/* Infrastructure */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold">Infrastructure Data</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              HIFLD-sourced data on critical infrastructure
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {infrastructure.map((item) => (
              <Card key={item.title}>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                      <item.icon className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{item.count}</p>
                      <p className="font-medium">{item.title}</p>
                    </div>
                  </div>
                  <p className="mt-4 text-sm text-muted-foreground">
                    {item.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Environment */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold">Environmental Data</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Public lands, water features, and environmental boundaries
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {environment.map((item) => (
              <Card key={item.title}>
                <CardContent className="pt-6 text-center">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <item.icon className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="font-semibold">{item.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {item.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold">Ready to explore?</h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Try our interactive demo or start building with the free tier
          </p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Button size="lg" asChild>
              <Link href="/signup">
                Get Started Free
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/map">View Demo</Link>
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}

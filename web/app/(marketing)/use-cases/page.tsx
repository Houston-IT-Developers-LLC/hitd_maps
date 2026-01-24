import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Header } from '@/components/marketing/header'
import { Footer } from '@/components/marketing/footer'
import {
  ArrowRight,
  Building2,
  Shield,
  Truck,
  Home,
  BarChart3,
  MapPin,
  Zap,
  CheckCircle,
} from 'lucide-react'

export const metadata = {
  title: 'Use Cases - Maps for Developers',
  description: 'Discover how developers use Maps for Developers to build real estate platforms, insurance tools, logistics systems, and property technology applications.',
}

export default function UseCasesPage() {
  const useCases = [
    {
      icon: Home,
      title: 'Real Estate & Property Tech',
      description: 'Build property search platforms, valuation tools, and market analysis dashboards with accurate parcel boundaries and ownership data.',
      features: [
        'Property boundary visualization',
        'Owner lookup and history',
        'Assessed value data',
        'Comparable property analysis',
      ],
      companies: 'Property listing sites, MLS integrations, investment platforms',
    },
    {
      icon: Shield,
      title: 'Insurance & Risk Assessment',
      description: 'Underwrite policies with precise property data. Assess flood zones, property conditions, and coverage requirements.',
      features: [
        'Accurate property boundaries',
        'Lot size verification',
        'Building footprints',
        'Terrain and elevation data',
      ],
      companies: 'Home insurance, commercial property, risk analytics',
    },
    {
      icon: Truck,
      title: 'Logistics & Delivery',
      description: 'Optimize delivery routes and service areas with detailed address data and POI locations.',
      features: [
        '17M+ points of interest',
        'Address geocoding',
        'Service area mapping',
        'Route optimization',
      ],
      companies: 'Last-mile delivery, fleet management, field services',
    },
    {
      icon: Building2,
      title: 'Commercial Real Estate',
      description: 'Analyze commercial properties, zoning, and market opportunities with comprehensive parcel data.',
      features: [
        'Zoning information',
        'Commercial property data',
        'Market analysis tools',
        'Site selection support',
      ],
      companies: 'CRE brokerages, investment firms, developers',
    },
    {
      icon: BarChart3,
      title: 'Financial Services',
      description: 'Support mortgage origination, property valuation, and portfolio analysis with verified property data.',
      features: [
        'Property valuation data',
        'Ownership verification',
        'Lien and tax records',
        'Portfolio mapping',
      ],
      companies: 'Mortgage lenders, appraisers, asset managers',
    },
    {
      icon: MapPin,
      title: 'Government & Public Sector',
      description: 'Power civic applications with authoritative parcel data, address validation, and facility mapping.',
      features: [
        'Address standardization',
        'Emergency response mapping',
        'Infrastructure planning',
        'Public records integration',
      ],
      companies: 'State/local governments, utilities, emergency services',
    },
  ]

  const testimonials = [
    {
      quote: "The parcel data quality is exceptional. We reduced our property verification time by 80%.",
      author: "Senior Engineer",
      company: "Property Tech Startup",
    },
    {
      quote: "Finally, an API with predictable pricing. No more surprise bills at the end of the month.",
      author: "CTO",
      company: "Real Estate Platform",
    },
    {
      quote: "The coverage is incredible. 150M+ parcels with actual owner data - exactly what we needed.",
      author: "Data Engineer",
      company: "Insurance Analytics",
    },
  ]

  return (
    <div className="min-h-screen">
      <Header />

      {/* Hero */}
      <section className="py-20 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold">
            Built for Every Industry
          </h1>
          <p className="mt-4 text-xl text-muted-foreground max-w-2xl mx-auto">
            From real estate to insurance, logistics to fintech. See how developers
            are building with 167M+ verified property records.
          </p>
          <Button size="lg" className="mt-8" asChild>
            <Link href="/signup">
              Start Building
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </Button>
        </div>
      </section>

      {/* Use Cases Grid */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {useCases.map((useCase) => (
              <Card key={useCase.title} className="h-full">
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <useCase.icon className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle>{useCase.title}</CardTitle>
                  <CardDescription>{useCase.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 mb-4">
                    {useCase.features.map((feature) => (
                      <li key={feature} className="flex items-center gap-2 text-sm">
                        <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <p className="text-xs text-muted-foreground">
                    <span className="font-medium">Used by:</span> {useCase.companies}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold">Trusted by Developers Worldwide</h2>
          </div>
          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-4xl font-bold text-primary">150M+</div>
              <div className="mt-2 text-gray-400">Property Parcels</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary">17M+</div>
              <div className="mt-2 text-gray-400">Points of Interest</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary">47</div>
              <div className="mt-2 text-gray-400">States + DC</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary">99.9%</div>
              <div className="mt-2 text-gray-400">Uptime SLA</div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold">What Developers Say</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, i) => (
              <Card key={i}>
                <CardContent className="pt-6">
                  <p className="text-muted-foreground italic">"{testimonial.quote}"</p>
                  <div className="mt-4">
                    <div className="font-medium">{testimonial.author}</div>
                    <div className="text-sm text-muted-foreground">{testimonial.company}</div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Integration Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold">Integrate in Minutes</h2>
              <p className="mt-4 text-lg text-muted-foreground">
                Native SDKs for every platform. RESTful API with comprehensive documentation.
                Get from signup to production in hours, not weeks.
              </p>
              <ul className="mt-8 space-y-4">
                <li className="flex items-center gap-3">
                  <Zap className="h-5 w-5 text-primary" />
                  <span>JavaScript, React, React Native, Flutter, iOS, Android</span>
                </li>
                <li className="flex items-center gap-3">
                  <Zap className="h-5 w-5 text-primary" />
                  <span>Full TypeScript support with autocomplete</span>
                </li>
                <li className="flex items-center gap-3">
                  <Zap className="h-5 w-5 text-primary" />
                  <span>Comprehensive code examples and tutorials</span>
                </li>
              </ul>
              <div className="mt-8 flex gap-4">
                <Button asChild>
                  <Link href="/quickstart">
                    View Quickstart
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button variant="outline" asChild>
                  <Link href="/api-reference">API Reference</Link>
                </Button>
              </div>
            </div>
            <div className="bg-gray-900 rounded-xl p-6 overflow-x-auto">
              <pre className="text-sm text-gray-300 font-mono">
                <code>{`import { MapsForDevelopers } from '@mapsfordevelopers/js'

const map = new MapsForDevelopers({
  apiKey: 'YOUR_API_KEY',
  container: 'map',
  layers: ['parcels', 'pois']
})

// Query parcel data on click
map.on('click', 'parcels', async (e) => {
  const parcel = e.features[0]

  console.log('Address:', parcel.properties.address)
  console.log('Owner:', parcel.properties.owner)
  console.log('Value:', parcel.properties.assessed_value)
  console.log('Lot Size:', parcel.properties.lot_size_sqft)
})`}</code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-primary text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold">Ready to build?</h2>
          <p className="mt-4 text-lg text-blue-100">
            Start with our free tier. 1,000 requests per day, no credit card required.
          </p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Button size="lg" variant="secondary" asChild>
              <Link href="/signup">
                Get Started Free
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" className="bg-transparent border-white text-white hover:bg-white/10" asChild>
              <Link href="/pricing">View Pricing</Link>
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}

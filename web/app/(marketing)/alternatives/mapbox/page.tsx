import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Header } from '@/components/marketing/header'
import { Footer } from '@/components/marketing/footer'
import { ArrowRight, Check, X } from 'lucide-react'

export const metadata = {
  title: 'Maps for Developers vs Mapbox - Best Alternative in 2024',
  description: 'Compare Maps for Developers to Mapbox. Get property parcel data, zero egress fees, and simpler pricing. The best Mapbox alternative for developers.',
  keywords: ['mapbox alternative', 'mapbox api alternative', 'maps api', 'property parcels api'],
}

export default function MapboxAlternativePage() {
  const comparison = [
    {
      feature: 'Property Parcel Data',
      us: true,
      competitor: false,
      note: '150M+ parcels with owner info',
    },
    {
      feature: 'Zero Egress Fees',
      us: true,
      competitor: false,
      note: 'Cloudflare R2 powered',
    },
    {
      feature: 'Simple Flat Pricing',
      us: true,
      competitor: false,
      note: '$49.99/mo vs usage-based',
    },
    {
      feature: 'MapLibre GL Compatible',
      us: true,
      competitor: true,
      note: 'Same SDK, different source',
    },
    {
      feature: 'Vector Tiles',
      us: true,
      competitor: true,
      note: 'PMTiles format',
    },
    {
      feature: '3D Terrain',
      us: true,
      competitor: true,
      note: 'High-resolution elevation',
    },
    {
      feature: 'Custom Styles',
      us: true,
      competitor: true,
      note: 'Full style customization',
    },
    {
      feature: 'Offline Maps',
      us: true,
      competitor: true,
      note: 'Download packages',
    },
    {
      feature: 'Self-Hosted Option',
      us: true,
      competitor: false,
      note: 'Your infrastructure',
    },
  ]

  const faqs = [
    {
      q: 'Is Maps for Developers compatible with Mapbox GL JS?',
      a: 'We use MapLibre GL JS, which is an open-source fork of Mapbox GL JS. The APIs are nearly identical, making migration straightforward.',
    },
    {
      q: 'How does pricing compare to Mapbox?',
      a: 'Mapbox uses complex usage-based pricing that can be unpredictable. We offer a simple $49.99/mo plan with clear limits. No surprise bills.',
    },
    {
      q: 'Can I use my existing Mapbox styles?',
      a: 'Yes! MapLibre GL is compatible with Mapbox style specifications. Most styles work with minimal or no changes.',
    },
    {
      q: 'What about Mapbox Studio?',
      a: 'We provide pre-built styles and you can use any MapLibre-compatible style editor. Our styles are based on Protomaps themes.',
    },
  ]

  return (
    <div className="min-h-screen">
      <Header />

      {/* Hero */}
      <section className="py-20 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-6">
            Mapbox Alternative
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold">
            Maps for Developers vs Mapbox
          </h1>
          <p className="mt-6 text-xl text-muted-foreground">
            Same great developer experience, plus property data and simpler pricing.
            The MapLibre-powered Mapbox alternative.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Button size="lg" asChild>
              <Link href="/signup">
                Try Free
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/map">View Demo</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">
            Feature Comparison
          </h2>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-4 px-4">Feature</th>
                  <th className="text-center py-4 px-4">Maps for Developers</th>
                  <th className="text-center py-4 px-4">Mapbox</th>
                </tr>
              </thead>
              <tbody>
                {comparison.map((row) => (
                  <tr key={row.feature} className="border-b">
                    <td className="py-4 px-4">
                      <div className="font-medium">{row.feature}</div>
                      <div className="text-sm text-muted-foreground">{row.note}</div>
                    </td>
                    <td className="text-center py-4 px-4">
                      {row.us ? (
                        <Check className="h-6 w-6 text-green-500 mx-auto" />
                      ) : (
                        <X className="h-6 w-6 text-red-500 mx-auto" />
                      )}
                    </td>
                    <td className="text-center py-4 px-4">
                      {row.competitor ? (
                        <Check className="h-6 w-6 text-green-500 mx-auto" />
                      ) : (
                        <X className="h-6 w-6 text-red-500 mx-auto" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Key Differences */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">
            Why switch from Mapbox?
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            <Card>
              <CardContent className="pt-6">
                <h3 className="text-lg font-semibold mb-2">Property Data</h3>
                <p className="text-muted-foreground">
                  Mapbox doesn&apos;t offer property parcel data. We have 150M+
                  parcels with owner names, property values, and boundaries.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <h3 className="text-lg font-semibold mb-2">Simpler Pricing</h3>
                <p className="text-muted-foreground">
                  No more calculating MAUs and load factors. $49.99/mo gets you
                  100,000 requests/day. Zero egress fees.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <h3 className="text-lg font-semibold mb-2">Open Source Core</h3>
                <p className="text-muted-foreground">
                  Built on MapLibre GL JS. No proprietary lock-in. Self-host on
                  your infrastructure with PMTiles.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Migration */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-8">
            Easy Migration from Mapbox
          </h2>
          <p className="text-center text-muted-foreground mb-12">
            Since we use MapLibre GL JS (a Mapbox GL fork), migration is straightforward
          </p>

          <div className="bg-gray-900 rounded-xl p-6 overflow-x-auto">
            <pre className="text-sm text-gray-300 font-mono">
              <code>{`// Before (Mapbox)
import mapboxgl from 'mapbox-gl'
mapboxgl.accessToken = 'pk.xxx'
const map = new mapboxgl.Map({ ... })

// After (Maps for Developers)
import { MapsForDevelopers } from '@mapsfordevelopers/js'
const map = new MapsForDevelopers({
  apiKey: 'mfd_live_xxx',
  ...
})`}</code>
            </pre>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">
            Frequently Asked Questions
          </h2>

          <div className="space-y-8">
            {faqs.map((faq, i) => (
              <div key={i}>
                <h3 className="font-semibold text-lg">{faq.q}</h3>
                <p className="mt-2 text-muted-foreground">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-primary text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold">Ready to switch?</h2>
          <p className="mt-4 text-lg text-blue-100">
            Start with our free tier. No credit card required.
          </p>
          <Button size="lg" variant="secondary" className="mt-8" asChild>
            <Link href="/signup">
              Get Started Free
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </Button>
        </div>
      </section>

      <Footer />

      {/* JSON-LD Schema */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            mainEntity: faqs.map((faq) => ({
              '@type': 'Question',
              name: faq.q,
              acceptedAnswer: {
                '@type': 'Answer',
                text: faq.a,
              },
            })),
          }),
        }}
      />
    </div>
  )
}

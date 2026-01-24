import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Header } from '@/components/marketing/header'
import { Footer } from '@/components/marketing/footer'
import { ArrowRight, Check, X } from 'lucide-react'

export const metadata = {
  title: 'Maps for Developers vs Google Maps - Best Alternative in 2024',
  description: 'Compare Maps for Developers to Google Maps. Get property parcel data, zero egress fees, and developer-friendly pricing. The best Google Maps alternative for developers.',
  keywords: ['google maps alternative', 'google maps api alternative', 'maps api', 'property parcels api'],
}

export default function GoogleMapsAlternativePage() {
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
      feature: 'Predictable Pricing',
      us: true,
      competitor: false,
      note: '$49.99/mo flat rate',
    },
    {
      feature: 'Offline Support',
      us: true,
      competitor: true,
      note: 'Download map packages',
    },
    {
      feature: '3D Terrain',
      us: true,
      competitor: true,
      note: 'High-resolution elevation',
    },
    {
      feature: 'Satellite Imagery',
      us: true,
      competitor: true,
      note: 'ESRI imagery',
    },
    {
      feature: 'POI Data',
      us: true,
      competitor: true,
      note: '17M+ points of interest',
    },
    {
      feature: 'On-Premise Option',
      us: true,
      competitor: false,
      note: 'Enterprise deployment available',
    },
    {
      feature: 'No Vendor Lock-in',
      us: true,
      competitor: false,
      note: 'Standard formats, easy migration',
    },
  ]

  const faqs = [
    {
      q: 'Is Maps for Developers a drop-in replacement for Google Maps?',
      a: 'Our platform provides similar core functionality with additional features like property parcel data. Our SDK makes migration straightforward with comprehensive documentation and migration guides.',
    },
    {
      q: 'How does pricing compare to Google Maps?',
      a: 'Google Maps charges per API call with complex pricing tiers. We offer transparent flat-rate pricing at $49.99/mo with 100,000 requests/day included. No surprise bills.',
    },
    {
      q: 'Do you have property boundary data?',
      a: 'Yes. This is our key differentiator. We provide 150M+ verified property parcels covering 47 states + DC with owner information, assessed values, and legal boundaries.',
    },
    {
      q: 'Do you offer enterprise deployment options?',
      a: 'Yes. Enterprise customers can deploy on-premise or use our dedicated infrastructure. Contact our sales team for custom deployment options.',
    },
  ]

  return (
    <div className="min-h-screen">
      <Header />

      {/* Hero */}
      <section className="py-20 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-6">
            Google Maps Alternative
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold">
            Maps for Developers vs Google Maps
          </h1>
          <p className="mt-6 text-xl text-muted-foreground">
            Get property parcel data, zero egress fees, and simple pricing.
            The developer-friendly Google Maps alternative.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Button size="lg" asChild>
              <Link href="/signup">
                Try Free
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/map">Live Map</Link>
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
                  <th className="text-center py-4 px-4">Google Maps</th>
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
            Why switch from Google Maps?
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            <Card>
              <CardContent className="pt-6">
                <h3 className="text-lg font-semibold mb-2">Property Data</h3>
                <p className="text-muted-foreground">
                  Google Maps doesn&apos;t offer property parcel data. We have 150M+
                  parcels with owner names, property values, and boundaries.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <h3 className="text-lg font-semibold mb-2">Predictable Pricing</h3>
                <p className="text-muted-foreground">
                  No more surprise bills. $49.99/mo gets you 100,000 requests/day.
                  Zero egress fees thanks to Cloudflare R2.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <h3 className="text-lg font-semibold mb-2">Self-Hosted Option</h3>
                <p className="text-muted-foreground">
                  Run on your own infrastructure with PMTiles. No vendor lock-in.
                  Keep your data where you want it.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* FAQ Schema */}
      <section className="py-20">
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

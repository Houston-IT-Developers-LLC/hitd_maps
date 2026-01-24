import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Header } from '@/components/marketing/header'
import { Footer } from '@/components/marketing/footer'
import { Check, ArrowRight } from 'lucide-react'
import { PLANS } from '@/lib/stripe/plans'

export const metadata = {
  title: 'Pricing',
  description: 'Simple, transparent pricing. Start free, upgrade when ready.',
}

export default function PricingPage() {
  return (
    <div className="min-h-screen">
      <Header />

      {/* Hero */}
      <section className="py-20 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold">
            Simple, transparent pricing
          </h1>
          <p className="mt-4 text-xl text-muted-foreground max-w-2xl mx-auto">
            Start free, upgrade when you&apos;re ready. No hidden fees, no surprises.
            Zero egress costs thanks to Cloudflare R2.
          </p>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-8">
            {/* Free */}
            <Card>
              <CardHeader>
                <CardTitle>{PLANS.free.name}</CardTitle>
                <CardDescription>{PLANS.free.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-8">
                  <span className="text-4xl font-bold">$0</span>
                  <span className="text-muted-foreground">/month</span>
                </div>
                <ul className="space-y-3">
                  {PLANS.free.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-3">
                      <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                <Button variant="outline" className="w-full" asChild>
                  <Link href="/signup">Get Started</Link>
                </Button>
              </CardFooter>
            </Card>

            {/* Pro */}
            <Card className="border-primary relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="bg-primary text-white text-sm font-medium px-3 py-1 rounded-full">
                  Most Popular
                </span>
              </div>
              <CardHeader>
                <CardTitle>{PLANS.pro.name}</CardTitle>
                <CardDescription>{PLANS.pro.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-8">
                  <span className="text-4xl font-bold">$49</span>
                  <span className="text-muted-foreground">/month</span>
                </div>
                <ul className="space-y-3">
                  {PLANS.pro.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-3">
                      <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                <Button className="w-full" asChild>
                  <Link href="/signup">
                    Get Started
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
              </CardFooter>
            </Card>

            {/* Enterprise */}
            <Card>
              <CardHeader>
                <CardTitle>{PLANS.enterprise.name}</CardTitle>
                <CardDescription>{PLANS.enterprise.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-8">
                  <span className="text-4xl font-bold">$199</span>
                  <span className="text-muted-foreground">/month</span>
                </div>
                <ul className="space-y-3">
                  {PLANS.enterprise.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-3">
                      <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                <Button variant="outline" className="w-full" asChild>
                  <Link href="/signup">Get Started</Link>
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">
            Frequently asked questions
          </h2>
          <div className="space-y-8">
            <div>
              <h3 className="font-semibold text-lg">What happens if I exceed my limits?</h3>
              <p className="mt-2 text-muted-foreground">
                We&apos;ll notify you when you&apos;re approaching your limits. If you exceed them,
                requests will be rate-limited until the next billing cycle. Upgrade to avoid interruptions.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-lg">Can I cancel anytime?</h3>
              <p className="mt-2 text-muted-foreground">
                Yes! Cancel anytime from your dashboard. You&apos;ll keep access until the end of your
                billing period, then automatically switch to the free tier.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-lg">Do you offer a free trial?</h3>
              <p className="mt-2 text-muted-foreground">
                The free tier is your trial! Build and test with real data before committing.
                No credit card required to start.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-lg">What payment methods do you accept?</h3>
              <p className="mt-2 text-muted-foreground">
                We accept all major credit cards via Stripe. Enterprise customers can pay by invoice.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-lg">Why no egress fees?</h3>
              <p className="mt-2 text-muted-foreground">
                We use Cloudflare R2 for storage, which has zero egress fees. This means we can offer
                predictable pricing without surprise bandwidth bills.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold">Ready to get started?</h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Join thousands of developers building with Maps for Developers
          </p>
          <Button size="lg" className="mt-8" asChild>
            <Link href="/signup">
              Start Building Free
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </Button>
        </div>
      </section>

      <Footer />
    </div>
  )
}

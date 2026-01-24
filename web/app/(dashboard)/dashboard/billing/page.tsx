'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { createClient } from '@/lib/supabase/client'
import { Check, CreditCard, Zap, Building, ArrowRight, Loader2 } from 'lucide-react'

const plans = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    period: '/month',
    description: 'For testing and evaluation',
    features: [
      '10,000 tile requests/month',
      '1,000 API calls/month',
      'Property parcels (47 states)',
      'Community support',
    ],
    limits: { tiles: 10000, api: 1000 },
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '$49',
    period: '/month',
    description: 'For production applications',
    features: [
      '5M tile requests/month',
      '500K API calls/month',
      'All data layers',
      'Offline packages',
      'Email support',
      'Usage analytics',
    ],
    limits: { tiles: 5000000, api: 500000 },
    popular: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: '$199',
    period: '/month',
    description: 'For high-volume applications',
    features: [
      '25M tile requests/month',
      '2.5M API calls/month',
      'Dedicated support',
      'Custom SLA',
      'Priority bug fixes',
      'Custom integrations',
    ],
    limits: { tiles: 25000000, api: 2500000 },
  },
]

function BillingContent() {
  const searchParams = useSearchParams()
  const [loading, setLoading] = useState(true)
  const [upgradeLoading, setUpgradeLoading] = useState(false)
  const [portalLoading, setPortalLoading] = useState(false)
  const [profile, setProfile] = useState<{
    subscription_tier: string
    subscription_status: string
    stripe_customer_id: string | null
  } | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    if (searchParams.get('success') === 'true') {
      setMessage({ type: 'success', text: 'Subscription activated successfully!' })
    } else if (searchParams.get('canceled') === 'true') {
      setMessage({ type: 'error', text: 'Checkout was canceled.' })
    }
  }, [searchParams])

  useEffect(() => {
    async function loadProfile() {
      const supabase = createClient()
      const { data: { user } } = await supabase.auth.getUser()

      if (user) {
        const { data } = await supabase
          .from('profiles')
          .select('subscription_tier, subscription_status, stripe_customer_id')
          .eq('id', user.id)
          .single()

        setProfile(data)
      }
      setLoading(false)
    }
    loadProfile()
  }, [])

  const handleUpgrade = async (planId: string) => {
    setUpgradeLoading(true)
    const priceId = planId === 'pro'
      ? process.env.NEXT_PUBLIC_STRIPE_PRO_PRICE_ID
      : process.env.NEXT_PUBLIC_STRIPE_ENTERPRISE_PRICE_ID
    try {
      const response = await fetch('/api/billing/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ priceId }),
      })

      const data = await response.json()

      if (data.url) {
        window.location.href = data.url
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to start checkout' })
      }
    } catch {
      setMessage({ type: 'error', text: 'Something went wrong' })
    } finally {
      setUpgradeLoading(false)
    }
  }

  const handleManageBilling = async () => {
    setPortalLoading(true)
    try {
      const response = await fetch('/api/billing/create-portal', {
        method: 'POST',
      })

      const data = await response.json()

      if (data.url) {
        window.location.href = data.url
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to open billing portal' })
      }
    } catch {
      setMessage({ type: 'error', text: 'Something went wrong' })
    } finally {
      setPortalLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const currentTier = profile?.subscription_tier || 'free'
  const isActive = profile?.subscription_status === 'active'

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Billing</h1>
        <p className="text-muted-foreground mt-1">
          Manage your subscription and billing settings
        </p>
      </div>

      {/* Messages */}
      {message && (
        <div
          className={`p-4 rounded-lg ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Current Plan */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Current Plan
          </CardTitle>
          <CardDescription>
            Your subscription status and usage limits
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-bold capitalize">{currentTier}</p>
              <p className="text-sm text-muted-foreground">
                Status: <span className={isActive ? 'text-green-600' : 'text-yellow-600'}>
                  {isActive ? 'Active' : profile?.subscription_status || 'Active'}
                </span>
              </p>
            </div>
            {currentTier !== 'free' && profile?.stripe_customer_id && (
              <Button
                variant="outline"
                onClick={handleManageBilling}
                disabled={portalLoading}
              >
                {portalLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : null}
                Manage Subscription
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Plans */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Available Plans</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {plans.map((plan) => {
            const isCurrent = currentTier === plan.id
            const canUpgradeToPro = currentTier === 'free' && plan.id === 'pro'
            const canUpgradeToEnterprise = (currentTier === 'free' || currentTier === 'pro') && plan.id === 'enterprise'
            const canUpgrade = canUpgradeToPro || canUpgradeToEnterprise

            return (
              <Card
                key={plan.id}
                className={`relative ${plan.popular ? 'border-primary shadow-lg' : ''} ${
                  isCurrent ? 'bg-primary/5' : ''
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="bg-primary text-primary-foreground text-xs font-medium px-3 py-1 rounded-full">
                      Most Popular
                    </span>
                  </div>
                )}
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {plan.id === 'free' && <Zap className="h-5 w-5" />}
                    {plan.id === 'pro' && <CreditCard className="h-5 w-5" />}
                    {plan.id === 'enterprise' && <Building className="h-5 w-5" />}
                    {plan.name}
                  </CardTitle>
                  <div className="mt-2">
                    <span className="text-3xl font-bold">{plan.price}</span>
                    <span className="text-muted-foreground">{plan.period}</span>
                  </div>
                  <CardDescription>{plan.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 mb-6">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>

                  {isCurrent ? (
                    <Button className="w-full" disabled>
                      Current Plan
                    </Button>
                  ) : canUpgrade ? (
                    <Button
                      className="w-full"
                      onClick={() => handleUpgrade(plan.id)}
                      disabled={upgradeLoading}
                    >
                      {upgradeLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : null}
                      Upgrade Now
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  ) : plan.id === 'free' && currentTier !== 'free' ? (
                    <Button className="w-full" variant="outline" disabled>
                      Downgrade via Portal
                    </Button>
                  ) : (
                    <Button className="w-full" variant="outline" disabled>
                      {currentTier === 'enterprise' ? 'Current tier is higher' : 'Upgrade'}
                    </Button>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>

      {/* FAQ */}
      <Card>
        <CardHeader>
          <CardTitle>Billing FAQ</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium">How do I cancel my subscription?</h4>
            <p className="text-sm text-muted-foreground">
              Click &quot;Manage Subscription&quot; above to access the billing portal where you can cancel anytime.
            </p>
          </div>
          <div>
            <h4 className="font-medium">What happens if I exceed my limits?</h4>
            <p className="text-sm text-muted-foreground">
              API requests will return a 429 status code. Consider upgrading to Pro for 500x more requests.
            </p>
          </div>
          <div>
            <h4 className="font-medium">Can I switch plans mid-billing cycle?</h4>
            <p className="text-sm text-muted-foreground">
              Yes. Upgrades take effect immediately with prorated billing. Downgrades apply at the end of your billing period.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default function BillingPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    }>
      <BillingContent />
    </Suspense>
  )
}

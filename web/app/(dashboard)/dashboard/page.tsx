import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { Key, BarChart3, Zap, ArrowRight, Copy } from 'lucide-react'

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  // Get user profile
  const { data: profile } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user.id)
    .single()

  // Get API keys count
  const { count: keyCount } = await supabase
    .from('api_keys')
    .select('*', { count: 'exact', head: true })
    .eq('user_id', user.id)
    .eq('is_active', true)

  // Get today's usage
  const today = new Date().toISOString().split('T')[0]
  const { data: usage } = await supabase
    .from('usage_daily')
    .select('tile_requests, api_requests')
    .eq('user_id', user.id)
    .eq('date', today)
    .single()

  const tier = profile?.subscription_tier || 'free'
  const tierLimits = {
    free: { tiles: 1000, api: 100 },
    developer: { tiles: 100000, api: 10000 },
    enterprise: { tiles: Infinity, api: Infinity },
  }

  const limits = tierLimits[tier as keyof typeof tierLimits]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Welcome back! Here&apos;s an overview of your API usage.
        </p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active API Keys</CardTitle>
            <Key className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{keyCount || 0}</div>
            <p className="text-xs text-muted-foreground">
              <Link href="/dashboard/api-keys" className="text-primary hover:underline">
                Manage keys
              </Link>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Tile Requests Today</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(usage?.tile_requests || 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              of {limits.tiles === Infinity ? 'unlimited' : limits.tiles.toLocaleString()} daily limit
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">API Calls Today</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(usage?.api_requests || 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              of {limits.api === Infinity ? 'unlimited' : limits.api.toLocaleString()} daily limit
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Start */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Start</CardTitle>
          <CardDescription>
            Get started with Maps for Developers in seconds
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg bg-gray-900 p-4 font-mono text-sm text-white overflow-x-auto">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">// Install the SDK</span>
              <button className="text-gray-400 hover:text-white">
                <Copy className="h-4 w-4" />
              </button>
            </div>
            <code>npm install @mapsfordevelopers/js</code>

            <div className="flex items-center justify-between mt-4 mb-2">
              <span className="text-gray-400">// Initialize the map</span>
            </div>
            <pre className="text-green-400">{`import { MapsForDevelopers } from '@mapsfordevelopers/js'

const map = new MapsForDevelopers({
  apiKey: 'YOUR_API_KEY',
  container: 'map',
  center: [-95.37, 29.76],
  zoom: 12,
  layers: ['parcels', 'pois', 'terrain']
})`}</pre>
          </div>

          <div className="flex gap-4">
            <Button asChild>
              <Link href="/dashboard/api-keys">
                Get API Key
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/docs">
                View Documentation
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Plan Status */}
      {tier === 'free' && (
        <Card className="border-primary">
          <CardHeader>
            <CardTitle>Upgrade to Developer</CardTitle>
            <CardDescription>
              Unlock 100x more requests, all data layers, and offline packages
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link href="/dashboard/billing">
                Upgrade for $49.99/mo
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

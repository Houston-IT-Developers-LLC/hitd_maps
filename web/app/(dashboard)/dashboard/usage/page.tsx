import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart3, TrendingUp, Calendar, Zap } from 'lucide-react'

export const dynamic = 'force-dynamic'

export default async function UsagePage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  // Get user profile for tier info
  const { data: profile } = await supabase
    .from('profiles')
    .select('subscription_tier')
    .eq('id', user.id)
    .single()

  // Get last 30 days of usage
  const thirtyDaysAgo = new Date()
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

  const { data: usageData } = await supabase
    .from('usage_daily')
    .select('date, tile_requests, api_requests, bytes_transferred')
    .eq('user_id', user.id)
    .gte('date', thirtyDaysAgo.toISOString().split('T')[0])
    .order('date', { ascending: true })

  // Calculate totals
  const totals = (usageData || []).reduce(
    (acc, day) => ({
      tiles: acc.tiles + (day.tile_requests || 0),
      api: acc.api + (day.api_requests || 0),
      bytes: acc.bytes + (day.bytes_transferred || 0),
    }),
    { tiles: 0, api: 0, bytes: 0 }
  )

  // Get today's usage
  const today = new Date().toISOString().split('T')[0]
  const todayUsage = usageData?.find((d) => d.date === today)

  const tier = profile?.subscription_tier || 'free'
  const tierLimits = {
    free: { tiles: 1000, api: 100 },
    developer: { tiles: 100000, api: 10000 },
    enterprise: { tiles: Infinity, api: Infinity },
  }
  const limits = tierLimits[tier as keyof typeof tierLimits]

  // Format bytes
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // Calculate usage percentage
  const tilePercent = limits.tiles === Infinity ? 0 : ((todayUsage?.tile_requests || 0) / limits.tiles) * 100
  const apiPercent = limits.api === Infinity ? 0 : ((todayUsage?.api_requests || 0) / limits.api) * 100

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Usage Analytics</h1>
        <p className="text-muted-foreground mt-1">
          Monitor your API usage and track consumption patterns
        </p>
      </div>

      {/* Today's Usage */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Tile Requests Today</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(todayUsage?.tile_requests || 0).toLocaleString()}
            </div>
            <div className="mt-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                <span>
                  {limits.tiles === Infinity ? 'Unlimited' : `${tilePercent.toFixed(1)}% used`}
                </span>
                <span>
                  {limits.tiles === Infinity ? '∞' : limits.tiles.toLocaleString()}
                </span>
              </div>
              {limits.tiles !== Infinity && (
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      tilePercent > 90 ? 'bg-red-500' : tilePercent > 75 ? 'bg-yellow-500' : 'bg-primary'
                    }`}
                    style={{ width: `${Math.min(tilePercent, 100)}%` }}
                  />
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">API Calls Today</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(todayUsage?.api_requests || 0).toLocaleString()}
            </div>
            <div className="mt-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                <span>
                  {limits.api === Infinity ? 'Unlimited' : `${apiPercent.toFixed(1)}% used`}
                </span>
                <span>
                  {limits.api === Infinity ? '∞' : limits.api.toLocaleString()}
                </span>
              </div>
              {limits.api !== Infinity && (
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      apiPercent > 90 ? 'bg-red-500' : apiPercent > 75 ? 'bg-yellow-500' : 'bg-primary'
                    }`}
                    style={{ width: `${Math.min(apiPercent, 100)}%` }}
                  />
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Data Transferred</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatBytes(todayUsage?.bytes_transferred || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Today&apos;s bandwidth usage
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Current Plan</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">{tier}</div>
            <p className="text-xs text-muted-foreground mt-2">
              {tier === 'free' ? 'Upgrade for more requests' : 'Thank you for subscribing!'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 30-Day Summary */}
      <Card>
        <CardHeader>
          <CardTitle>30-Day Summary</CardTitle>
          <CardDescription>Your total usage over the past 30 days</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <p className="text-sm text-muted-foreground">Total Tile Requests</p>
              <p className="text-3xl font-bold">{totals.tiles.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total API Calls</p>
              <p className="text-3xl font-bold">{totals.api.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total Data Transferred</p>
              <p className="text-3xl font-bold">{formatBytes(totals.bytes)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Daily Usage Table */}
      <Card>
        <CardHeader>
          <CardTitle>Daily Breakdown</CardTitle>
          <CardDescription>Usage by day for the past 30 days</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium">Date</th>
                  <th className="text-right py-3 px-4 font-medium">Tile Requests</th>
                  <th className="text-right py-3 px-4 font-medium">API Calls</th>
                  <th className="text-right py-3 px-4 font-medium">Data Transferred</th>
                </tr>
              </thead>
              <tbody>
                {(usageData || []).length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-muted-foreground">
                      No usage data yet. Start making API requests to see analytics.
                    </td>
                  </tr>
                ) : (
                  [...(usageData || [])].reverse().map((day) => (
                    <tr key={day.date} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4">
                        {new Date(day.date).toLocaleDateString('en-US', {
                          weekday: 'short',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </td>
                      <td className="text-right py-3 px-4">
                        {(day.tile_requests || 0).toLocaleString()}
                      </td>
                      <td className="text-right py-3 px-4">
                        {(day.api_requests || 0).toLocaleString()}
                      </td>
                      <td className="text-right py-3 px-4">
                        {formatBytes(day.bytes_transferred || 0)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

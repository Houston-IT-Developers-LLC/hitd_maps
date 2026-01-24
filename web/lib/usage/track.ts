import { createClient } from '@/lib/supabase/server'

export interface UsageEvent {
  userId: string
  apiKeyId: string
  endpoint: string
  bytesTransferred?: number
}

/**
 * Tracks API usage for billing purposes
 */
export async function trackUsage(event: UsageEvent): Promise<void> {
  const supabase = await createClient()
  const today = new Date().toISOString().split('T')[0] // YYYY-MM-DD

  const isTileRequest = event.endpoint.includes('/tiles/')
  const isApiRequest = !isTileRequest

  // Upsert daily usage record
  const { error } = await supabase.rpc('increment_usage', {
    p_user_id: event.userId,
    p_api_key_id: event.apiKeyId,
    p_date: today,
    p_tile_requests: isTileRequest ? 1 : 0,
    p_api_requests: isApiRequest ? 1 : 0,
    p_bytes_transferred: event.bytesTransferred || 0,
  })

  if (error) {
    console.error('Failed to track usage:', error)
  }
}

export type SubscriptionTier = 'free' | 'pro' | 'enterprise'

/**
 * Gets usage limits based on subscription tier (monthly limits)
 */
export function getUsageLimits(tier: SubscriptionTier) {
  const limits = {
    free: {
      tileRequestsPerMonth: 10000,      // 10K tiles/month
      apiRequestsPerMonth: 1000,        // 1K API calls/month
    },
    pro: {
      tileRequestsPerMonth: 5000000,    // 5M tiles/month
      apiRequestsPerMonth: 500000,      // 500K API calls/month
    },
    enterprise: {
      tileRequestsPerMonth: 25000000,   // 25M tiles/month
      apiRequestsPerMonth: 2500000,     // 2.5M API calls/month
    },
  }

  return limits[tier] || limits.free
}

/**
 * Checks if user has exceeded their monthly usage limits
 */
export async function checkUsageLimits(
  userId: string,
  tier: SubscriptionTier
): Promise<{ exceeded: boolean; current: { tiles: number; api: number }; limits: { tiles: number; api: number } }> {
  const supabase = await createClient()
  const limits = getUsageLimits(tier)

  // Get first day of current month
  const now = new Date()
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)
  const monthStartStr = monthStart.toISOString().split('T')[0]

  // Sum all usage for the current month
  const { data } = await supabase
    .from('usage_daily')
    .select('tile_requests, api_requests')
    .eq('user_id', userId)
    .gte('date', monthStartStr)

  // Sum up all daily records for the month
  const current = (data || []).reduce(
    (acc, day) => ({
      tiles: acc.tiles + (day.tile_requests || 0),
      api: acc.api + (day.api_requests || 0),
    }),
    { tiles: 0, api: 0 }
  )

  const exceeded =
    current.tiles >= limits.tileRequestsPerMonth ||
    current.api >= limits.apiRequestsPerMonth

  return {
    exceeded,
    current,
    limits: {
      tiles: limits.tileRequestsPerMonth,
      api: limits.apiRequestsPerMonth,
    },
  }
}

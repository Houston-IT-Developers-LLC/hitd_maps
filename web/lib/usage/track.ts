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

/**
 * Gets usage limits based on subscription tier
 */
export function getUsageLimits(tier: 'free' | 'developer' | 'enterprise') {
  const limits = {
    free: {
      tileRequestsPerDay: 1000,
      apiRequestsPerDay: 100,
    },
    developer: {
      tileRequestsPerDay: 100000,
      apiRequestsPerDay: 10000,
    },
    enterprise: {
      tileRequestsPerDay: Infinity,
      apiRequestsPerDay: Infinity,
    },
  }

  return limits[tier]
}

/**
 * Checks if user has exceeded their usage limits
 */
export async function checkUsageLimits(
  userId: string,
  tier: 'free' | 'developer' | 'enterprise'
): Promise<{ exceeded: boolean; current: { tiles: number; api: number } }> {
  const supabase = await createClient()
  const today = new Date().toISOString().split('T')[0]
  const limits = getUsageLimits(tier)

  const { data } = await supabase
    .from('usage_daily')
    .select('tile_requests, api_requests')
    .eq('user_id', userId)
    .eq('date', today)
    .single()

  const current = {
    tiles: data?.tile_requests || 0,
    api: data?.api_requests || 0,
  }

  const exceeded =
    current.tiles >= limits.tileRequestsPerDay ||
    current.api >= limits.apiRequestsPerDay

  return { exceeded, current }
}

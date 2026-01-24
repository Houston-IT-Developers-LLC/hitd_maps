import { createClient } from '@/lib/supabase/server'
import { hashApiKey } from './generate'
import { SubscriptionTier } from '@/lib/usage/track'

export interface ApiKeyValidation {
  valid: boolean
  userId?: string
  keyId?: string
  tier?: SubscriptionTier
  permissions?: {
    tiles: boolean
    parcels: boolean
    geocode: boolean
  }
  error?: string
}

/**
 * Validates an API key and returns user info if valid
 */
export async function validateApiKey(apiKey: string): Promise<ApiKeyValidation> {
  if (!apiKey || !apiKey.startsWith('mfd_live_')) {
    return { valid: false, error: 'Invalid API key format' }
  }

  const hash = hashApiKey(apiKey)
  const supabase = await createClient()

  // Look up the key by hash
  const { data: keyData, error } = await supabase
    .from('api_keys')
    .select(`
      id,
      user_id,
      permissions,
      is_active,
      profiles!inner (
        subscription_tier,
        subscription_status
      )
    `)
    .eq('key_hash', hash)
    .single()

  if (error || !keyData) {
    return { valid: false, error: 'API key not found' }
  }

  if (!keyData.is_active) {
    return { valid: false, error: 'API key is deactivated' }
  }

  // Handle profiles which could be an array or single object from the join
  const profileData = keyData.profiles as unknown
  const profile = Array.isArray(profileData) ? profileData[0] : profileData
  const typedProfile = profile as { subscription_tier: string; subscription_status: string }

  if (typedProfile.subscription_status !== 'active') {
    return { valid: false, error: 'Subscription is not active' }
  }

  // Update last_used_at
  await supabase
    .from('api_keys')
    .update({ last_used_at: new Date().toISOString() })
    .eq('id', keyData.id)

  // Map legacy 'developer' tier to 'pro'
  let tier = typedProfile.subscription_tier as SubscriptionTier
  if (tier === 'developer' as unknown) {
    tier = 'pro'
  }

  return {
    valid: true,
    userId: keyData.user_id,
    keyId: keyData.id,
    tier,
    permissions: keyData.permissions as { tiles: boolean; parcels: boolean; geocode: boolean },
  }
}

import { createHash, randomBytes } from 'crypto'

export interface GeneratedApiKey {
  key: string      // Full key (only shown once)
  prefix: string   // First part for display (mfd_live_xxxx)
  hash: string     // SHA-256 hash for storage
}

/**
 * Generates a new API key with the format: mfd_live_[32 random bytes base64url]
 */
export function generateApiKey(): GeneratedApiKey {
  // Generate 32 random bytes
  const keyBytes = randomBytes(32)
  const key = `mfd_live_${keyBytes.toString('base64url')}`

  // Prefix for display (first 16 chars)
  const prefix = key.substring(0, 16) + '...'

  // SHA-256 hash for storage
  const hash = createHash('sha256').update(key).digest('hex')

  return { key, prefix, hash }
}

/**
 * Hashes an API key for comparison with stored hash
 */
export function hashApiKey(key: string): string {
  return createHash('sha256').update(key).digest('hex')
}

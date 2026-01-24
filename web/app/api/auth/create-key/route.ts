import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { generateApiKey } from '@/lib/api-keys/generate'

export async function POST(request: NextRequest) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { name } = await request.json()

  if (!name || typeof name !== 'string') {
    return NextResponse.json({ error: 'Name is required' }, { status: 400 })
  }

  // Generate API key
  const { key, prefix, hash } = generateApiKey()

  // Store in database (only the hash, not the actual key)
  const { error } = await supabase.from('api_keys').insert({
    user_id: user.id,
    name: name.trim(),
    key_prefix: prefix,
    key_hash: hash,
    is_active: true,
    permissions: { tiles: true, parcels: true, geocode: true },
  })

  if (error) {
    console.error('Failed to create API key:', error)
    return NextResponse.json({ error: 'Failed to create key' }, { status: 500 })
  }

  // Return the actual key (only time it's shown)
  return NextResponse.json({ key })
}

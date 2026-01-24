import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  // Safe check for SSG/SSR - only create client on browser
  if (typeof window === 'undefined') {
    // Return a dummy object during SSR/SSG that won't be used
    return null as unknown as ReturnType<typeof createBrowserClient>
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (!supabaseUrl || !supabaseKey) {
    console.error('Missing Supabase environment variables')
    return null as unknown as ReturnType<typeof createBrowserClient>
  }

  return createBrowserClient(supabaseUrl, supabaseKey)
}

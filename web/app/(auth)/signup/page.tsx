'use client'

import { useState } from 'react'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { MapPin, ArrowRight, Check, Zap, Globe, Lock } from 'lucide-react'

export default function SignupPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    const supabase = createClient()
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    })

    if (error) {
      setError(error.message)
      setLoading(false)
    } else {
      setSent(true)
      setLoading(false)
    }
  }

  const features = [
    { icon: Zap, text: 'Get started in seconds' },
    { icon: Globe, text: '150M+ property parcels' },
    { icon: Lock, text: 'No credit card required' },
  ]

  return (
    <div className="min-h-screen flex bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Left side - Benefits */}
      <div className="hidden lg:flex lg:w-1/2 bg-primary p-12 flex-col justify-center text-white">
        <h1 className="text-4xl font-bold mb-6">
          Start building with the most comprehensive maps API
        </h1>
        <p className="text-lg text-blue-100 mb-8">
          Access 680GB of map data including property parcels, POIs, 3D terrain,
          and satellite imagery. Zero egress fees, unlimited potential.
        </p>
        <ul className="space-y-4">
          {features.map((feature, i) => (
            <li key={i} className="flex items-center gap-3">
              <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                <feature.icon className="h-4 w-4" />
              </div>
              <span>{feature.text}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Right side - Form */}
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <Link href="/" className="flex items-center justify-center gap-2 mb-8">
            <MapPin className="h-8 w-8 text-primary" />
            <span className="text-2xl font-bold">Maps for Developers</span>
          </Link>

          <Card>
            <CardHeader className="text-center">
              <CardTitle>Create your account</CardTitle>
              <CardDescription>
                Start with the free tier - no credit card required
              </CardDescription>
            </CardHeader>
            <CardContent>
              {sent ? (
                <div className="text-center py-4">
                  <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Check className="h-6 w-6 text-green-600" />
                  </div>
                  <h3 className="font-semibold text-lg mb-2">Check your email</h3>
                  <p className="text-muted-foreground text-sm">
                    We sent a magic link to <strong>{email}</strong>
                  </p>
                  <p className="text-muted-foreground text-sm mt-2">
                    Click the link to complete your signup.
                  </p>
                  <Button
                    variant="ghost"
                    className="mt-4"
                    onClick={() => {
                      setSent(false)
                      setEmail('')
                    }}
                  >
                    Use a different email
                  </Button>
                </div>
              ) : (
                <form onSubmit={handleSignup} className="space-y-4">
                  <div>
                    <Input
                      type="email"
                      placeholder="you@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      disabled={loading}
                    />
                  </div>
                  {error && (
                    <p className="text-sm text-destructive">{error}</p>
                  )}
                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? 'Sending...' : 'Get started for free'}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                  <p className="text-xs text-muted-foreground text-center">
                    By signing up, you agree to our{' '}
                    <Link href="/terms" className="underline hover:text-primary">
                      Terms of Service
                    </Link>{' '}
                    and{' '}
                    <Link href="/privacy" className="underline hover:text-primary">
                      Privacy Policy
                    </Link>
                  </p>
                </form>
              )}
            </CardContent>
          </Card>

          <p className="text-center text-sm text-muted-foreground mt-6">
            Already have an account?{' '}
            <Link href="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

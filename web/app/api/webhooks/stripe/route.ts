import { NextRequest, NextResponse } from 'next/server'
import Stripe from 'stripe'
import { createClient, SupabaseClient } from '@supabase/supabase-js'

// Lazy initialization to avoid build-time errors
function getStripe() {
  return new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: '2025-02-24.acacia',
  })
}

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  )
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnySupabaseClient = SupabaseClient<any, any, any>

export async function POST(request: NextRequest) {
  const stripe = getStripe()
  const supabase = getSupabase()

  const body = await request.text()
  const signature = request.headers.get('stripe-signature')!

  let event: Stripe.Event

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    )
  } catch (err) {
    console.error('Webhook signature verification failed:', err)
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 })
  }

  try {
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session
        await handleCheckoutCompleted(stripe, supabase, session)
        break
      }

      case 'customer.subscription.updated': {
        const subscription = event.data.object as Stripe.Subscription
        await handleSubscriptionUpdated(supabase, subscription)
        break
      }

      case 'customer.subscription.deleted': {
        const subscription = event.data.object as Stripe.Subscription
        await handleSubscriptionDeleted(supabase, subscription)
        break
      }

      case 'invoice.payment_succeeded': {
        const invoice = event.data.object as Stripe.Invoice
        await handlePaymentSucceeded(supabase, invoice)
        break
      }

      case 'invoice.payment_failed': {
        const invoice = event.data.object as Stripe.Invoice
        await handlePaymentFailed(supabase, invoice)
        break
      }
    }

    return NextResponse.json({ received: true })
  } catch (error) {
    console.error('Webhook handler error:', error)
    return NextResponse.json(
      { error: 'Webhook handler failed' },
      { status: 500 }
    )
  }
}

async function handleCheckoutCompleted(
  stripe: Stripe,
  supabase: AnySupabaseClient,
  session: Stripe.Checkout.Session
) {
  const customerId = session.customer as string
  const subscriptionId = session.subscription as string

  // Get subscription details
  const subscription = await stripe.subscriptions.retrieve(subscriptionId)
  const plan = subscription.metadata.plan || 'developer'

  // Update user profile
  await supabase
    .from('profiles')
    .update({
      stripe_customer_id: customerId,
      subscription_tier: plan,
      subscription_status: 'active',
      updated_at: new Date().toISOString(),
    })
    .eq('stripe_customer_id', customerId)
}

async function handleSubscriptionUpdated(
  supabase: AnySupabaseClient,
  subscription: Stripe.Subscription
) {
  const customerId = subscription.customer as string
  const status = subscription.status

  let subscriptionStatus: 'active' | 'canceled' | 'past_due' = 'active'
  if (status === 'canceled' || status === 'unpaid') {
    subscriptionStatus = 'canceled'
  } else if (status === 'past_due') {
    subscriptionStatus = 'past_due'
  }

  await supabase
    .from('profiles')
    .update({
      subscription_status: subscriptionStatus,
      updated_at: new Date().toISOString(),
    })
    .eq('stripe_customer_id', customerId)
}

async function handleSubscriptionDeleted(
  supabase: AnySupabaseClient,
  subscription: Stripe.Subscription
) {
  const customerId = subscription.customer as string

  await supabase
    .from('profiles')
    .update({
      subscription_tier: 'free',
      subscription_status: 'active',
      updated_at: new Date().toISOString(),
    })
    .eq('stripe_customer_id', customerId)
}

async function handlePaymentSucceeded(
  supabase: AnySupabaseClient,
  invoice: Stripe.Invoice
) {
  const customerId = invoice.customer as string

  // Record the invoice
  await supabase.from('invoices').insert({
    stripe_invoice_id: invoice.id,
    amount_cents: invoice.amount_paid,
    status: 'paid',
    period_start: invoice.period_start
      ? new Date(invoice.period_start * 1000).toISOString().split('T')[0]
      : null,
    period_end: invoice.period_end
      ? new Date(invoice.period_end * 1000).toISOString().split('T')[0]
      : null,
  })

  // Ensure subscription is active
  await supabase
    .from('profiles')
    .update({
      subscription_status: 'active',
      updated_at: new Date().toISOString(),
    })
    .eq('stripe_customer_id', customerId)
}

async function handlePaymentFailed(
  supabase: AnySupabaseClient,
  invoice: Stripe.Invoice
) {
  const customerId = invoice.customer as string

  await supabase
    .from('profiles')
    .update({
      subscription_status: 'past_due',
      updated_at: new Date().toISOString(),
    })
    .eq('stripe_customer_id', customerId)
}

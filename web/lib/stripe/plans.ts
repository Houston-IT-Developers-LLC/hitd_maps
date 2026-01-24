export const PLANS = {
  free: {
    id: 'free',
    name: 'Free',
    description: 'For testing and evaluation',
    price: 0,
    priceId: null,
    features: [
      '10,000 tile requests/month',
      '1,000 API calls/month',
      'Property parcels (47 states)',
      'Community support',
    ],
    limits: {
      tileRequestsPerMonth: 10000,
      apiRequestsPerMonth: 1000,
      offlinePackages: false,
    },
  },
  pro: {
    id: 'pro',
    name: 'Pro',
    description: 'For production applications',
    price: 4900, // $49 in cents
    priceId: process.env.STRIPE_PRO_PRICE_ID,
    features: [
      '5,000,000 tile requests/month',
      '500,000 API calls/month',
      'All data layers',
      'Property parcels (150M+)',
      'POIs & addresses',
      '3D terrain & satellite',
      'Offline packages',
      'Email support',
    ],
    limits: {
      tileRequestsPerMonth: 5000000,
      apiRequestsPerMonth: 500000,
      offlinePackages: true,
    },
  },
  enterprise: {
    id: 'enterprise',
    name: 'Enterprise',
    description: 'For high-volume applications',
    price: 19900, // $199 in cents
    priceId: process.env.STRIPE_ENTERPRISE_PRICE_ID,
    features: [
      '25,000,000 tile requests/month',
      '2,500,000 API calls/month',
      'Dedicated support',
      'Custom SLA',
      'Priority bug fixes',
      'Custom data integrations',
    ],
    limits: {
      tileRequestsPerMonth: 25000000,
      apiRequestsPerMonth: 2500000,
      offlinePackages: true,
    },
  },
} as const

export type PlanId = keyof typeof PLANS

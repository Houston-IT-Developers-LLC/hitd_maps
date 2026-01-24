export const PLANS = {
  free: {
    id: 'free',
    name: 'Free',
    description: 'For testing and small projects',
    price: 0,
    priceId: null,
    features: [
      '1,000 tile requests/day',
      '100 API calls/day',
      'Basic map layers',
      'Community support',
    ],
    limits: {
      tileRequestsPerDay: 1000,
      apiRequestsPerDay: 100,
      offlinePackages: false,
    },
  },
  developer: {
    id: 'developer',
    name: 'Developer',
    description: 'For production applications',
    price: 4999, // $49.99 in cents
    priceId: process.env.STRIPE_DEVELOPER_PRICE_ID,
    features: [
      '100,000 tile requests/day',
      '10,000 API calls/day',
      'All data layers',
      'Property parcels (150M+)',
      'POIs (17M+)',
      '3D terrain & satellite',
      'Offline packages',
      'Email support',
    ],
    limits: {
      tileRequestsPerDay: 100000,
      apiRequestsPerDay: 10000,
      offlinePackages: true,
    },
  },
  enterprise: {
    id: 'enterprise',
    name: 'Enterprise',
    description: 'For high-volume applications',
    price: null, // Custom pricing
    priceId: null,
    features: [
      'Unlimited requests',
      'Dedicated infrastructure',
      'Custom SLA',
      'On-premise option',
      'Priority support',
      'Custom data integrations',
    ],
    limits: {
      tileRequestsPerDay: Infinity,
      apiRequestsPerDay: Infinity,
      offlinePackages: true,
    },
  },
} as const

export type PlanId = keyof typeof PLANS

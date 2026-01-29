# Maps for Developers - Product Vision & Business Model

## Mission

**Make mapsfordevelopers.com the go-to Google Maps/Mapbox alternative** - affordable, self-hosted, with comprehensive US property data that nobody else has.

---

## Business Model (Simple Version)

### What We're Building

A **map API service** that anyone can use in their websites and apps, similar to Google Maps API or Mapbox, but:
- **Way cheaper** (we host on Cloudflare R2 with zero egress costs)
- **More data** (property parcels, 3D terrain, POI, addresses, navigation)
- **Offline capable** (users can download map regions for offline use)

### How It Works

1. **User signs up** at mapsfordevelopers.com
2. **Gets an API key** (like Google Maps API key)
3. **Integrates into their app/website** (we provide SDK/docs)
4. **Chooses what data layers they want:**
   - 3D terrain
   - Satellite imagery
   - Property parcels (our unique selling point!)
   - POI (points of interest - businesses, landmarks)
   - Addresses
   - Roads and navigation
   - Public lands

5. **Usage-based pricing** (or tiered plans)
   - Free tier: X requests/month
   - Pro: $X/month for Y requests
   - Enterprise: Custom pricing

### Offline Mode

- Users can download specific map regions to their device
- App works offline with downloaded data
- **Every 30 days, app checks API key is still valid** when online
- If subscription cancelled, offline data stops working after validation period

---

## Target Customers

### Primary Use Cases

1. **Real estate apps** - Show property boundaries, ownership data
2. **Outdoor/hunting apps** - Terrain, public lands, navigation (like My G-Spot Outdoors)
3. **Logistics/delivery apps** - Routing, addresses, offline operation
4. **Construction/surveying** - Property data, terrain analysis
5. **Local government** - Planning, zoning, public services

### First Customer: My G-Spot Outdoors

**What it is:** Hunting and outdoor recreation app

**What it needs from mapsfordevelopers.com:**
- 3D terrain (find hills, valleys for hunting)
- Property parcels (know where you can legally hunt)
- Public lands data (national forests, BLM land, state parks)
- Offline maps (hunters are often in areas with no cell service)
- POI (trailheads, campsites, boat ramps)
- Navigation

**Why we're perfect:**
- No one else offers property parcel data in a consumer API
- Offline mode is essential for outdoor apps
- Way cheaper than Google Maps for high-usage apps

---

## Technical Architecture

### Public Website (mapsfordevelopers.com)

**Must be accessible to anyone:**
- Homepage explaining the service
- Live interactive demo map
- Pricing page
- Documentation/API reference
- Sign up / Login (Supabase Auth)
- Dashboard to manage API keys
- Usage analytics

### API Service

```
User's App → API Key → Our API → Cloudflare R2 → Map Data
```

**Authentication flow:**
1. User makes request with API key in header
2. We validate key against Supabase database
3. Check if subscription is active
4. Serve PMTiles data from R2 CDN
5. Log usage for billing

**Offline validation:**
1. User downloads map region with API key
2. Data cached locally on device
3. Every 30 days (when online), app checks: `GET /api/validate?key=xxx`
4. If valid → continue working offline
5. If invalid/expired → disable offline maps

### Data Layers (What Users Can Choose)

| Layer | Source | Size | Use Case |
|-------|--------|------|----------|
| **Property Parcels** | Our unique dataset | 70 GB | Real estate, land ownership |
| **Basemap** | Protomaps | 233 GB | Streets, cities, labels |
| **Terrain** | USGS | 44 GB | 3D elevation, hillshade |
| **Satellite** | (TBD - need to source) | ? | Aerial imagery |
| **POI** | Overture Maps | 15 GB | Businesses, landmarks |
| **Addresses** | Overture Maps | 7 GB | Geocoding, routing |
| **Public Lands** | PAD-US | 616 MB | National parks, forests |
| **Roads** | Overture Maps | 18 GB | Navigation, routing |

Users can enable/disable layers via dashboard, pay only for what they use.

---

## What Needs to Be Built

### Phase 1: MVP (Minimum Viable Product)

1. **Public website** (Next.js, already started in `/web`)
   - Homepage with demo
   - Sign up / Login (Supabase)
   - Pricing page
   - Documentation

2. **API authentication** (Next.js API routes)
   - Generate API keys
   - Validate keys on requests
   - Rate limiting
   - Usage tracking

3. **Payments** (Stripe, already configured)
   - Subscription plans
   - Usage-based billing
   - Dashboard to show current usage

4. **SDK/Documentation**
   - JavaScript SDK for easy integration
   - Code examples
   - Integration guides

### Phase 2: Advanced Features

5. **Offline mode validation**
   - 30-day check endpoint
   - Mobile SDK with offline caching
   - Downloadable region manager

6. **Layer selection**
   - Dashboard to enable/disable layers
   - Custom pricing based on layers used
   - Layer preview in dashboard

7. **Analytics**
   - Usage dashboard
   - Performance monitoring
   - Cost tracking per layer

### Phase 3: Scale & Optimize

8. **Performance**
   - CDN optimization
   - Caching strategies
   - Global edge deployment

9. **Advanced features**
   - Custom styling (like Mapbox Studio)
   - Routing API
   - Geocoding API
   - Data uploads (user-provided layers)

---

## My G-Spot Outdoors Integration

### What the hunting app needs:

**Map Component:**
```javascript
import { MapsForDevelopers } from '@mapsfordevelopers/sdk';

const map = new MapsForDevelopers({
  apiKey: 'mfd_xxx...',
  container: 'map',
  layers: [
    'terrain-3d',
    'parcels',
    'public-lands',
    'poi'
  ],
  offline: true, // Enable offline mode
  offlineRegions: ['montana', 'wyoming'] // Pre-download these states
});
```

**Features needed:**
1. **Property boundaries overlay** - Show where hunters can legally be
2. **Public lands highlight** - National forests, BLM, state parks
3. **3D terrain** - Topographic view for planning
4. **Offline maps** - Download hunting areas before trip
5. **POI markers** - Trailheads, campsites, game check stations
6. **GPS tracking** - Real-time location even offline

**Business benefit:**
- My G-Spot Outdoors is the perfect showcase customer
- Proves the technology works
- Can use for marketing: "Powers My G-Spot Outdoors, a hunting app used by X users"
- Dogfooding - we'll discover bugs and needed features

---

## Developer Quick Start

### For new dev joining the project:

1. **Clone the repo**
2. **Get credentials** from CREDENTIALS.md (ask team lead)
3. **Set up environment:**
   ```bash
   cd web
   cp .env.local.example .env.local
   # Add real Supabase and Stripe keys
   npm install
   npm run dev
   ```

4. **Understand the stack:**
   - Frontend: Next.js 15 (in `/web`)
   - Auth: Supabase
   - Payments: Stripe
   - Maps: MapLibre GL JS
   - Data: PMTiles on Cloudflare R2
   - Data Pipeline: Python scripts (in `/data-pipeline`)

5. **Current status:**
   - We have the map data (72% US coverage, 263 counties)
   - We have basic map demo working
   - Need to build: API authentication, payments, dashboard

6. **First tasks:**
   - Set up Supabase database schema for users/API keys
   - Build API key generation and validation
   - Create user dashboard
   - Implement basic usage tracking

---

## Key Differentiators

**Why customers will choose us over Google Maps/Mapbox:**

1. **Property parcel data** - Nobody else has this
2. **Way cheaper** - No egress fees, flat pricing
3. **Offline-first** - Built for apps that need offline mode
4. **Self-hostable** - Data on Cloudflare R2, customers can even self-host
5. **Transparent pricing** - No surprise bills like Google Maps
6. **Developer-friendly** - Clear docs, simple API, open source tools

---

## Revenue Model (Simple Math)

**Pricing ideas:**
- Free: 10,000 map loads/month
- Starter: $29/month - 100,000 loads
- Pro: $99/month - 500,000 loads
- Enterprise: Custom pricing

**Example customer:**
- Real estate app with 10,000 users
- Each user views 20 properties/day with maps
- 200,000 map loads/day = 6M/month
- Would cost $15,000/month on Google Maps
- We charge $299/month → massive savings for them

**Path to profitability:**
- R2 costs: ~$30/month for storage + bandwidth
- 100 customers at $99/month = $9,900/month
- Profit: ~$9,800/month (after R2 costs)

---

## Questions for Dev to Consider

1. **Database schema** - How to structure users, API keys, usage tracking?
2. **Rate limiting** - What's fair for each tier?
3. **Offline validation** - Best UX for 30-day checks?
4. **SDK design** - What would make integration easiest?
5. **Layer switching** - How do users enable/disable layers efficiently?

---

## Next Steps

1. Review this document
2. Set up local development environment
3. Design database schema for users/API keys/subscriptions
4. Build MVP authentication flow
5. Create simple dashboard
6. Integrate with My G-Spot Outdoors as first test customer

---

**Questions?** Ask in team chat or schedule sync meeting.

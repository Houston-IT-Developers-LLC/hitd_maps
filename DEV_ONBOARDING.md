# Developer Onboarding - Maps for Developers

**Welcome!** This guide will get you up and running on the project.

---

## TL;DR - What You're Building

**A Google Maps alternative API** that developers can use in their apps. Think Mapbox or Google Maps API, but:
- Way cheaper
- Has property parcel data (unique to us)
- Works offline
- First customer: My G-Spot Outdoors (hunting app)

---

## Quick Setup (30 minutes)

### 1. Get the Code
```bash
cd ~/projects
git clone git@github.com:RORHITD/hitd_maps.git
cd hitd_maps
```

### 2. Get Credentials
**Ask your team lead for:**
- `CREDENTIALS.md` file (has all API keys)
- Supabase project access
- Stripe dashboard access
- Cloudflare R2 access (optional, for data pipeline)

Put CREDENTIALS.md in the project root (it's gitignored).

### 3. Setup Web App (Frontend)
```bash
cd web
npm install

# Copy environment template
cp .env.local.example .env.local

# Edit .env.local with real values from CREDENTIALS.md
nano .env.local

# Start dev server
npm run dev
```

Visit http://localhost:3000 - you should see the homepage.

### 4. Test the Map
Click on the map demo. You should see:
- Interactive map of USA
- Property parcel boundaries when you zoom in
- Working pan/zoom/rotate controls

If map doesn't load, check:
- R2 CDN URL is correct in .env.local
- Browser console for errors

---

## Project Structure (What's Where)

```
hitd_maps/
├── web/                          # Next.js frontend (THIS IS YOUR MAIN WORK AREA)
│   ├── app/                      # Next.js 15 app router
│   │   ├── (marketing)/         # Public pages (homepage, pricing, docs)
│   │   ├── map/                 # Map demo page
│   │   └── api/                 # API routes (YOU'LL BUILD THESE)
│   ├── components/              # React components
│   └── .env.local               # Your local config (not committed)
│
├── data-pipeline/               # Python scripts for processing map data
│   ├── scripts/                 # Data download/processing (mostly done)
│   └── data/                    # Tracking files
│
├── docs/                        # Documentation
│   ├── DATA_INVENTORY.md        # What data we have
│   └── DEVELOPER_GUIDE.md       # Technical details
│
├── PRODUCT_VISION.md            # Business model & roadmap (READ THIS)
├── CREDENTIALS.md               # API keys (GET FROM TEAM LEAD)
└── CLAUDE.md                    # Project context for AI assistant
```

---

## Your First Tasks

### Task 1: Understand What We Have (1 hour)

1. Read [PRODUCT_VISION.md](PRODUCT_VISION.md) - Understand the business model
2. Play with the map demo at http://localhost:3000/map
3. Look at the current codebase:
   - `web/app/map/page.tsx` - Map component
   - `web/app/(marketing)/page.tsx` - Homepage
4. Explore our data on R2: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/

### Task 2: Set Up Supabase (2 hours)

**Goal:** Create database schema for users, API keys, and usage tracking.

1. Log into Supabase dashboard (get invite from team lead)
2. Create tables:

```sql
-- Users table (already created by Supabase Auth)
-- We'll extend it with profiles

-- API Keys table
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  key TEXT UNIQUE NOT NULL,
  name TEXT, -- User-friendly name like "My App Production"
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_used_at TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT TRUE
);

-- Subscriptions table
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_customer_id TEXT,
  stripe_subscription_id TEXT,
  plan_name TEXT, -- 'free', 'starter', 'pro', 'enterprise'
  status TEXT, -- 'active', 'cancelled', 'past_due'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Usage tracking table
CREATE TABLE api_usage (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  api_key_id UUID REFERENCES api_keys(id) ON DELETE CASCADE,
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  endpoint TEXT, -- '/api/tiles', '/api/geocode', etc.
  requests_count INTEGER DEFAULT 1,
  bytes_transferred BIGINT,
  layer TEXT -- 'parcels', 'terrain', 'basemap', etc.
);

-- Create indexes for performance
CREATE INDEX idx_api_usage_timestamp ON api_usage(timestamp);
CREATE INDEX idx_api_usage_api_key_id ON api_usage(api_key_id);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
```

3. Test with some dummy data in Supabase dashboard

### Task 3: Build API Key Generation (3 hours)

**Goal:** Users can generate API keys from dashboard.

Create: `web/app/api/keys/generate/route.ts`

```typescript
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';
import { nanoid } from 'nanoid';

export async function POST(request: Request) {
  const supabase = createRouteHandlerClient({ cookies });

  // Check if user is authenticated
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { name } = await request.json();

  // Generate API key (format: mfd_xxxxxxxxxxxxx)
  const apiKey = `mfd_${nanoid(32)}`;

  // Save to database
  const { data, error } = await supabase
    .from('api_keys')
    .insert({
      user_id: session.user.id,
      key: apiKey,
      name: name || 'Untitled API Key',
    })
    .select()
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ apiKey: data.key });
}
```

### Task 4: Build API Key Validation Middleware (2 hours)

**Goal:** Validate API keys on every map request.

Create: `web/lib/auth.ts`

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY! // Use service role for server-side
);

export async function validateApiKey(apiKey: string) {
  if (!apiKey || !apiKey.startsWith('mfd_')) {
    return { valid: false, error: 'Invalid API key format' };
  }

  // Look up key in database
  const { data: keyData, error } = await supabase
    .from('api_keys')
    .select('*, subscriptions(*)')
    .eq('key', apiKey)
    .eq('is_active', true)
    .single();

  if (error || !keyData) {
    return { valid: false, error: 'API key not found' };
  }

  // Check if subscription is active
  const subscription = keyData.subscriptions?.[0];
  if (!subscription || subscription.status !== 'active') {
    return { valid: false, error: 'Subscription inactive' };
  }

  // Update last_used_at
  await supabase
    .from('api_keys')
    .update({ last_used_at: new Date().toISOString() })
    .eq('id', keyData.id);

  return {
    valid: true,
    keyId: keyData.id,
    userId: keyData.user_id,
    plan: subscription.plan_name
  };
}
```

### Task 5: Build User Dashboard (4 hours)

**Goal:** Page where users can see and manage their API keys.

Create: `web/app/dashboard/page.tsx`

Should show:
- User's current plan
- List of API keys with usage stats
- Button to generate new key
- Usage charts (requests over time)
- Link to documentation

Use Shadcn UI components (already configured in project).

### Task 6: Test with My G-Spot Outdoors (2 hours)

1. Generate an API key in your dashboard
2. Create a simple test HTML page:

```html
<!DOCTYPE html>
<html>
<head>
  <script src='https://unpkg.com/maplibre-gl/dist/maplibre-gl.js'></script>
  <link href='https://unpkg.com/maplibre-gl/dist/maplibre-gl.css' rel='stylesheet' />
</head>
<body>
  <div id='map' style='width: 100%; height: 100vh;'></div>
  <script>
    const API_KEY = 'mfd_your_key_here';

    const map = new maplibregl.Map({
      container: 'map',
      style: {
        version: 8,
        sources: {
          parcels: {
            type: 'vector',
            url: `pmtiles://https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels_tx_statewide.pmtiles?key=${API_KEY}`,
          }
        },
        layers: [{
          id: 'parcels',
          type: 'fill',
          source: 'parcels',
          'source-layer': 'parcels',
          paint: {
            'fill-color': '#088',
            'fill-opacity': 0.3
          }
        }]
      },
      center: [-99.9018, 31.9686], // Texas
      zoom: 10
    });
  </script>
</body>
</html>
```

3. Make sure parcels load correctly with API key validation

---

## Tech Stack Reference

| Technology | Purpose | Docs |
|------------|---------|------|
| **Next.js 15** | Frontend framework | nextjs.org |
| **React 19** | UI library | react.dev |
| **Supabase** | Auth & database | supabase.com/docs |
| **Stripe** | Payments | stripe.com/docs |
| **MapLibre GL JS** | Map rendering | maplibre.org |
| **PMTiles** | Map tile format | github.com/protomaps/PMTiles |
| **Cloudflare R2** | Data storage/CDN | developers.cloudflare.com/r2 |
| **Tailwind CSS** | Styling | tailwindcss.com |
| **Shadcn UI** | Components | ui.shadcn.com |

---

## Common Commands

```bash
# Frontend development
cd web
npm run dev          # Start dev server
npm run build        # Build for production
npm run lint         # Check for errors

# Data pipeline (if needed)
cd data-pipeline
python3 scripts/generate_coverage_report.py  # Check data coverage
make status          # Pipeline status
```

---

## Getting Help

**Documentation:**
- [PRODUCT_VISION.md](PRODUCT_VISION.md) - Business model & features
- [CLAUDE.md](CLAUDE.md) - Project context & commands
- [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) - Technical details

**Resources:**
- Supabase dashboard: [Your project URL]
- Stripe dashboard: [Your account]
- R2 data browser: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/

**Questions:**
- Team lead for credentials/access
- Project Slack/Discord for technical questions
- This codebase has Claude Code context - use AI assistant for code questions

---

## Success Criteria

**You're ready to ship when:**

1. ✅ Users can sign up and log in
2. ✅ Users can generate API keys from dashboard
3. ✅ API keys are validated on map requests
4. ✅ Usage is tracked in database
5. ✅ Dashboard shows usage statistics
6. ✅ Test integration works with My G-Spot Outdoors
7. ✅ Basic rate limiting prevents abuse
8. ✅ Documentation explains how to integrate

---

## Timeline Estimate

| Phase | Tasks | Time |
|-------|-------|------|
| **Setup** | Environment, credentials, exploration | 1 day |
| **Database** | Schema, migrations, test data | 1 day |
| **API** | Key generation, validation, middleware | 2 days |
| **Dashboard** | UI for managing keys and usage | 3 days |
| **Integration** | Test with My G-Spot Outdoors | 1 day |
| **Polish** | Error handling, docs, testing | 2 days |
| **Total** | MVP ready to launch | **10 days** |

---

## Next Phase (After MVP)

- Stripe payment integration
- Offline mode validation endpoint
- Layer selection in dashboard
- Advanced analytics
- Mobile SDK
- Geocoding API
- Routing API

---

Good luck! You're building something developers will love. 🗺️

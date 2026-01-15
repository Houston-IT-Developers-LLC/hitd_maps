# Parcel Data Acquisition Roadmap

Prioritized acquisition strategy for all 50 US states based on hunting popularity, data availability, and acquisition difficulty.

## Executive Summary

| Tier | States | Effort per State | Total States |
|------|--------|------------------|--------------|
| Tier 1: Free Statewide | 35 | 2-4 hours | 35 |
| Tier 2: County Portals | 14 | 4-8 hours | 14 |
| Tier 3: FOIA Required | 1 | 30+ days | 1 |
| **Total** | **50** | **~200-400 hours** | **50** |

**Cost comparison:** This approach costs ~$0 in data fees vs $80K+/year for commercial aggregators (Regrid, CoreLogic, etc.)

## Phase 1: Free Statewide Downloads (Immediate)

These states have confirmed free statewide parcel downloads. Acquire immediately.

### Priority A: Top Hunting States with Free Data

| Rank | State | Source | Parcels | Hunting Rank |
|------|-------|--------|---------|--------------|
| 1 | **TX** | TxGIO | ~28M | #1 |
| 2 | **WI** | WI SCO | ~3.5M | #4 |
| 3 | **PA** | PASDA | ~5M | #2 |
| 4 | **OH** | OGRIP | ~6M | #7 |
| 5 | **MN** | MN Geospatial | ~3M | #10 |
| 6 | **IN** | IndianaMap | ~3M | #12 |
| 7 | **NY** | NYS GIS | ~6M | #6 |
| 8 | **NC** | NC OneMap | ~4.5M | #14 |
| 9 | **VA** | VGIN | ~4M | #11 |
| 10 | **AR** | GeoStor | ~1.5M | #15 |

**Effort:** 2-4 hours per state
**Total:** ~30 hours for top 10

### Priority B: Remaining Free Statewide States

| State | Source | Notes |
|-------|--------|-------|
| AK | AK DNR | Sparse population, large parcels |
| CO | DOLA | Good skiing/hunting state |
| CT | CT DEEP | Small state |
| DE | FirstMap | 3 counties only |
| FL | FGDL | Popular hunting state |
| HI | HI GeoPortal | Limited hunting |
| ID | ID Geospatial | Great hunting |
| IA | Iowa Geodata | Midwest hunting |
| KS | DASC | Upland bird hunting |
| KY | KY GeoPortal | Deer hunting |
| ME | GeoLibrary | Great hunting |
| MD | iMap | Eastern deer |
| MA | MassGIS | Limited hunting |
| MT | Cadastral | Excellent hunting |
| NE | NEGIS | Pheasant hunting |
| NH | GRANIT | Deer hunting |
| NJ | NJGIN | Deer management |
| ND | ND GIS Hub | Waterfowl/upland |
| OR | GEOHub | Western hunting |
| RI | RIGIS | Small state |
| SD | SD GIS | Pheasant capital |
| UT | UGRC | Western big game |
| VT | VCGI | Deer hunting |
| WA | geo.wa.gov | Western hunting |
| WV | WVU GIS | Deer hunting |

**Effort:** 2-4 hours per state
**Total:** ~75 hours for remaining 25 states

## Phase 2: High-Priority Hunting States (County Acquisition)

These top hunting states don't have statewide downloads but are worth the extra effort.

### Top 10 US States by Deer Hunting Licenses

| Rank | State | Licenses | Data Tier | Priority |
|------|-------|----------|-----------|----------|
| 1 | TX | 1.2M | Tier 1 | **DONE** |
| 2 | PA | 950K | Tier 1 | Phase 1 |
| 3 | MI | 800K | Tier 2 | **HIGH** |
| 4 | WI | 700K | Tier 1 | Phase 1 |
| 5 | GA | 600K | Tier 2 | **HIGH** |
| 6 | NY | 590K | Tier 1 | Phase 1 |
| 7 | OH | 500K | Tier 1 | Phase 1 |
| 8 | MO | 480K | Tier 2 | MEDIUM |
| 9 | AL | 450K | Tier 3 | LOW |
| 10 | MN | 440K | Tier 1 | Phase 1 |

### Michigan (83 Counties)

**Strategy:** County-by-county with automation
- Many counties have ArcGIS REST endpoints
- Target populous counties first (Wayne, Oakland, Kent, etc.)
- Estimated effort: 16-24 hours

### Georgia (159 Counties)

**Strategy:** Georgia GIS Clearinghouse + county portals
- Large number of counties, but many have open portals
- Focus on North Georgia hunting counties first
- Estimated effort: 24-40 hours

### Missouri (114 Counties + St. Louis City)

**Strategy:** MSDIS has county-level data
- Check for aggregated datasets first
- Estimated effort: 16-24 hours

## Phase 3: Remaining Tier 2 States (County-Level)

Lower priority states requiring county-by-county acquisition.

| State | Counties | Strategy | Effort |
|-------|----------|----------|--------|
| AZ | 15 | AZGEO + county portals | 8 hours |
| CA | 58 | Focus on rural hunting counties | 40 hours |
| IL | 102 | ISGS + county portals | 20 hours |
| LA | 64 parishes | LSU Atlas | 16 hours |
| MS | 82 | MARIS limited data | 20 hours |
| NV | 17 | Focus on hunting counties | 8 hours |
| NM | 33 | RGIS + county portals | 12 hours |
| OK | 77 | OKMaps + county portals | 16 hours |
| SC | 46 | Limited availability | 16 hours |
| TN | 95 | TNMAP + county portals | 20 hours |
| WY | 23 | Large federal land % | 8 hours |

## Phase 4: FOIA States

States where most counties require formal records requests.

### Alabama (67 Counties)

**Strategy:**
1. Send batch FOIA requests to all 67 counties
2. Use template from [foia_template.md](./foia_template.md)
3. Expect 30-60 day turnaround
4. Budget $0-200 per county

**Effort:** 4 hours to send requests + wait time

## Effort Estimates

### Per-Tier Breakdown

| Tier | Hours/State | Wait Time | Cost | Total Hours |
|------|-------------|-----------|------|-------------|
| Tier 1 | 2-4 | None | $0 | 70-140 |
| Tier 2 | 4-8 | None | $0 | 56-112 |
| Tier 3 | 4 + wait | 30+ days | $0-200/county | 4+ |
| **Total** | | | **$0-13,400** | **~130-260** |

### Time Investment vs Commercial Cost

| Approach | Time | Annual Cost |
|----------|------|-------------|
| DIY Acquisition | ~200 hours | $0 |
| DIY + Some FOIA | ~250 hours | ~$5,000 |
| Commercial (Regrid) | 0 hours | $80,000+/year |
| Commercial (CoreLogic) | 0 hours | $50,000+/year |

**Break-even:** If your time is worth <$250-400/hour, DIY wins.

## Recommended Acquisition Order

### Week 1-2: Texas + Scripts

- [x] Texas download/load scripts
- [ ] Run Texas full import
- [ ] Validate data quality
- [ ] Generate Texas tiles

### Week 3-4: Top 5 Free States

- [ ] Pennsylvania (PASDA)
- [ ] Wisconsin (WI SCO)
- [ ] Ohio (OGRIP)
- [ ] Minnesota (MN Geospatial)
- [ ] Indiana (IndianaMap)

### Week 5-6: Next 10 Free States

- [ ] New York, North Carolina, Virginia
- [ ] Florida, Arkansas, Oregon
- [ ] Montana, Kentucky, Iowa

### Week 7-8: Remaining Free States

- [ ] All remaining Tier 1 states

### Week 9-12: High-Priority Tier 2

- [ ] Michigan (county by county)
- [ ] Georgia (county by county)
- [ ] Missouri (county by county)

### Ongoing: FOIA Requests

- [ ] Send Alabama batch requests
- [ ] Follow up on pending requests
- [ ] Process received data

## Quality Metrics

Track these metrics for each state:

| Metric | Target |
|--------|--------|
| Coverage | >95% of counties |
| Geometry validity | >99% valid |
| Owner name populated | >80% |
| Address populated | >70% |
| Freshness | <2 years old |

## Success Criteria

- [ ] All 50 states have some parcel coverage
- [ ] Top 10 hunting states have >90% coverage
- [ ] Data is <2 years old for active hunting states
- [ ] Vector tiles generated for all loaded states
- [ ] Total cost stays under $10,000

---

*Last updated: 2026-01-10*
*Estimated total effort: 200-400 hours*
*Estimated total cost: $0-$10,000 (mostly from FOIA fees if needed)*

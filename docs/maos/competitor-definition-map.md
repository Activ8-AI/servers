# Competitor Definition Map

## Purpose
Establish a single canonical record for every client ↔ competitor relationship so MAOS can drive surveillance, comparison, governance, and actioning with zero ambiguity. The Definition Map lives simultaneously in:
- **Notion** – Operational workspace used by Client Delivery, Growth, and Custodian teams.  
- **Codex** – Reference view consumed by MAOS for grounding, governance, and automated planning.

## Data Sources
| Source | Role |
| --- | --- |
| **Client Matrix** | Primary roster of active clients, industries, squads, SLAs, and KPI→Revenue coefficients. |
| **Onboarding Data** | Client positioning, ICP, historical wins/losses, pricing tiers. |
| **CRM** | Competitive notes captured by Sales/CS, active opportunities, renewal stages. |
| **Existing Briefs** | Algorithm briefs, marketing strategies, Custodian memos. |

## Core Objects & Fields
### 1. `client_profile`
| Field | Type | Description |
| --- | --- | --- |
| `client_id` | UUID | Canonical ID (matches Action Matrix + Portal). |
| `name` | Text | Display label. |
| `industry` | Enum (SaaS, Commerce, etc.) | Drives benchmark selection. |
| `tier` | Enum (Prime, Growth, Watch) | Determines surveillance frequency. |
| `kpi_revenue_map` | JSON | Mapping of KPI deltas → revenue impact. |
| `custodian_owner` | Person | Primary governance owner. |

### 2. `competitor_profile`
| Field | Type | Description |
| --- | --- | --- |
| `competitor_id` | UUID | Unique reference across MAOS. |
| `name` | Text | Official brand name. |
| `category` | Enum (Direct, Indirect, Emerging) | Threat posture. |
| `hq_region` | Enum | Helps with regulatory nuance + timezones. |
| `primary_channels` | Multi-select | e.g., Paid Search, Paid Social, Organic, Product-Led. |
| `pricing_model` | Enum (Seat, Usage, Hybrid, Freemium) | Baseline for comparison. |
| `tracking_surfaces` | JSON array | URLs + API endpoints for agents. |
| `alert_thresholds` | JSON | Channel-specific triggers (e.g., price change %, ad spend delta). |

### 3. `client_competitor_link`
| Field | Type | Description |
| --- | --- | --- |
| `client_id` | Ref | Links to `client_profile`. |
| `competitor_id` | Ref | Links to `competitor_profile`. |
| `priority_tier` | Enum (Tier 0, Tier 1, Tier 2) | Controls polling cadence. |
| `focus_vectors` | Multi-select | Pricing, Product, Positioning, Campaigns, Support, Tech. |
| `risk_notes` | Rich text | Manual analyst context, updated weekly. |
| `playbook_refs` | Links | Action Matrix playbooks relevant to this matchup. |

### 4. `governance_route`
| Field | Type | Description |
| --- | --- | --- |
| `client_competitor_link_id` | Ref | The specific pairing. |
| `custodian_primary` | Person | Must approve high-impact deltas. |
| `custodian_backup` | Person | Escalation contact. |
| `review_sla_hours` | Integer | SLA for manual validation. |
| `teamwork_project_id` | Text | Destination for Reflex-created tasks. |
| `portal_segment` | Text | Portal data partition for this client. |

## Derived Tables / Views
- **Alert Matrix**: Prioritized list of upcoming surveillance windows, sorted by priority tier + SLA.  
- **Context Rollups**: Summaries grouped by industry, competitor category, or client segment.  
- **Readiness Scorecard**: Flags missing data (e.g., absent pricing URL) and blocks deployment until complete.

## Sync & Governance Rules
1. **Source of Truth** – Notion is writable by humans; Codex is append-only, auto-synced every 15 minutes.  
2. **Change Control** – Any change to `tracking_surfaces`, `alert_thresholds`, or `teamwork_project_id` requires Custodian approval (Notion workflow + Codex hash).  
3. **Versioning** – Each sync produces a Custodian hash recorded in Codex; MAOS references the latest approved hash before running agents.  
4. **Completeness Gates** – Reflex will refuse to launch Competitor Engine for a client until required fields (URLs, thresholds, governance routes) exist.  
5. **Access** – Delivery + Growth teams have edit rights; Engineering + MAOS have read-only via Codex export.

## Implementation Steps
1. **Schema Build (Day 0-1)** – Create Notion databases with relations and rollups; expose mirrored views for analysts vs custodians.  
2. **Codex Export (Day 1)** – Configure automated export (JSON) into Codex, normalized to MAOS schema.  
3. **Data Backfill (Day 1-3)** – Leverage Client Matrix + CRM to populate Tier 0 and Tier 1 competitors; assign custodians.  
4. **Validation (Day 3)** – Run MAOS lint script to confirm every pairing has URLs, thresholds, Teamwork target, and portal segment.  
5. **Ongoing Ops** – Weekly review meetings to update risk notes; Reflex automatically flags stale entries (>30 days) for refresh.

## Data Contracts for Agents
Agents consume Definition Map slices with the following structure:
```json
{
  "client_id": "cli_123",
  "competitor_id": "comp_456",
  "priority_tier": "Tier 0",
  "tracking_surfaces": {
    "product": ["https://competitor.com/product", "..."],
    "pricing": ["https://competitor.com/pricing"],
    "blog": ["https://competitor.com/blog/rss"],
    "ads": {
      "meta": "library://competitor/meta/id",
      "google": "library://competitor/google/id"
    }
  },
  "alert_thresholds": {
    "pricing_percent": 0.02,
    "ad_spend_jump": 25000,
    "keyword_overlap": 5
  },
  "governance": {
    "custodian_primary": "person_789",
    "teamwork_project_id": "TW-CLIENT-OPS",
    "review_sla_hours": 12
  }
}
```
All downstream systems treat this as immutable within a run; updates require new Custodian hash.

## KPIs & Success Metrics
- 100% of active clients mapped to at least Tier 1 competitors.  
- Definition Map freshness <7 days for Tier 0, <14 days for Tier 1.  
- Zero agent runs blocked due to missing tracking surfaces once live.  
- Custodian approval latency under SLA for 95% of changes.

With this Definition Map in place, the Competitive Intelligence Engine knows **who** to watch, **where** to collect, **how often** to run, and **who** receives the resulting actions.

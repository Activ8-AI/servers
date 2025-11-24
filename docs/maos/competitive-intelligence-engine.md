# Competitive Intelligence Engine (v1)

## Charter Snapshot
- **Classification**: MAOS → Intelligence Plane → Web Analysis Agents → Client Portal  
- **Status**: Required (Charter-mandated)  
- **Objective**: Provide continuous external market surveillance so MAOS decisions are grounded in both internal telemetry (Reflex DAG → Teamwork → Action Matrix) and external competitive signals.  
- **Primary Consumers**: Client Portal, Codex, Teamwork, Heartbeats, KPI→Revenue mapping, Strategy Sprints, Reflex responses, Custodian visibility.

## Operating Objectives
1. **Perimeter Visibility** – Auto-track every known competitor per client across web, ad, product, and sentiment channels.  
2. **Comparative Insight** – Continuously score threats, openings, pricing deltas, positioning moves, and campaign shifts against each client’s operating posture.  
3. **Action Packaging** – Convert detected deltas directly into Reflex-triggered Teamwork tasks; no passive summaries.  
4. **Governance & Traceability** – Charter-standard briefs with confidence scoring, custody hashes, and governance notes for every surfaced event.  
5. **Portal Delivery** – Surface Competitor Intelligence tabs, Industry Radars, Risk levels, Trend watches, and Revenue impact projections per client.

## Architecture Overview
| Layer | Description | Key Assets |
| --- | --- | --- |
| **Data Definition** | Canonical Competitor Definition Map (Notion DB + Codex view) enumerating competitors, tracking surfaces, metrics, and custodians per client. | `/docs/maos/competitor-definition-map.md` |
| **Acquisition & Agents** | Dedicated web-analysis agents (surveillance, research, competitor_watch, web_crawler, signal_harvester, content_diff) orchestrated via Agent Hub. | `/docs/maos/agents.md` |
| **Processing Bus** | Signal harvester normalizes raw captures → content_diff isolates deltas → comparator scores severity/impact → governance formatter emits briefs. | Reflex DAG “External Intelligence Spine” |
| **Action Layer** | Reflex skills convert briefs into Teamwork-ready tasks with assignment, due dates, and escalation metadata. | Teamwork Reflex Pipelines (below) |
| **Experience Layer** | Client Portal ingest API + Codex governance surfaces for Portal dashboards, heartbeats, and KPI overlays. | Client Portal Integration (below) |

Signals travel asynchronously: Agent outputs → Signal queue → Comparative model → Reflex actions → Client Portal caches. The same payload is copied to Custodian ledger for audit.

## Coverage & Collection Rules
| Surface | Collection Method | Cadence | Notes |
| --- | --- | --- | --- |
| Websites / Product pages | `web_crawler_agent` with targeted sitemap diffing | 3× daily baseline; burst to hourly during launch windows | Use content hash per section to shortcut downloads. |
| Pricing / Packaging | `research_agent` + structured table parser | Hourly snapshots; alert on >2% price moves or bundle changes | Normalize currency + discount logic before comparison. |
| Blogs / PR / Launch notes | `surveillance_agent` RSS + newsroom scraping | Near real-time (webhooks) | Tag product area + release stage. |
| Ad libraries / PPC | `competitor_watch_agent` hooking Meta, Google, LinkedIn public libs | Twice daily baseline, hourly on high-spend alerts | Capture creative metadata + spend tiers. |
| Social / Sentiment | `signal_harvester_agent` tapping official handles + brand mentions | Continuous stream via social APIs | Derive sentiment + velocity; flag viral spikes. |
| SEO / SERP / Rankings | `research_agent` w/ SEO API connectors | Daily, with weekly deep dive | Track share-of-voice for each client keyword cluster. |
| Feature docs / Changelogs | `content_diff_agent` diffing docs + changelogs | Continuous monitor | Classify change type (security, UX, infra, etc.). |

## Processing Stages
1. **Ingest** – Agent-specific adapters normalize payloads into the Competitor Intelligence Event (`CIE`) schema.  
2. **Compare** – Comparator maps CIE metrics to client baselines (pricing, SKU count, channel spend, SERP rank).  
3. **Score** – Threat, opportunity, urgency, revenue impact, and confidence computed using heuristics + telemetry from Action Matrix.  
4. **Package** – Charter brief produced with: Summary, Market Impact, Strategic Implication, Recommended Actions, Governance Notes, Confidence Score, Custodian Hash.  
5. **Dispatch** –  
   - Reflex → Teamwork: creates/updates tasks with explicit action verbs.  
   - Portal Cache: pushes structured JSON to Client Portal data views.  
   - Codex: writes governance record referencing Custodian hash.

## Competitor Definition Map Dependency
All agent runs reference the canonical Competitor Definition Map for:
- Competitor URLs, assets, pricing anchors, channel mix, alert thresholds.  
- Client-to-competitor pairing plus priority tiers (Tier 0 strategic, Tier 1 revenue-adjacent, Tier 2 watchlist).  
- Custodian + reviewer routing rules.  
Specification lives in `/docs/maos/competitor-definition-map.md`.

## Web Analysis Agent Wiring
- Each agent registers in `agents.md` with role, trigger, inputs, outputs, and escalation policies.  
- Agents run inside MAOS Web Intelligence pod with shared logging, rate limiting, and credential vault.  
- Output contract: `CIE payload` with `event_id`, `client_id`, `competitor_id`, `channel`, `detected_change`, `raw_artifacts`, `confidence`, `recommended_action_stub`.  
- Agents publish to `external_intel.events` queue; comparator subscribes with retry + dedupe (idempotency via `event_id`).  
- Fail-safe: if an agent misses SLA twice, send Reflex heartbeat warning.

## Agent Hub Integration (agents.md highlights)
- Assignment rules map triggers (schedule, webhook, manual) to specific agents or ensembles.  
- Trigger logic ensures high-impact events (price change, ad launch) run accelerated follow-up sweeps.  
- Output contracts enforce Charter brief sections + Custodian Hash generation.  
- Governance hooks capture reviewer, timestamp, evidence bundle, and Teamwork task IDs.  
See `/docs/maos/agents.md` for detailed policies.

## Teamwork Reflex Pipelines
1. **Event Qualification**  
   - Input: Scored CIE payload.  
   - Filter: Confidence ≥ 0.65 + Impact ≥ Medium.  
   - Outcome: `competitor_delta` object with action template ID.
2. **Action Template Expansion**  
   - Templates for: New SKU, Price move, Ad campaign, Keyword hijack, Sentiment crisis, Feature launch.  
   - Each template defines: task title, checklist, default owner persona, SLA, escalation tags.
3. **Task Emission**  
   - Reflex writes to Teamwork via API with: client, squad, due date, severity color.  
   - Auto-attach evidence bundle + Custodian hash.  
4. **Feedback Loop**  
   - Task status updates feed back into MAOS Heartbeats + KPI→Revenue mapping to measure closed-loop impact.  
   - Missed SLAs trigger Reflex escalation runbook.

## Client Portal Integration
- **Competitor Intelligence Tab**: Lists active deltas, charter briefs, evidence, and next actions.  
- **Industry Radar**: Rolling 30/90-day heatmap of competitor initiatives vs client posture.  
- **Trend Watch**: Narrative summary auto-refreshed every 12h, grouped by theme (Pricing, Positioning, Product, Campaigns, Sentiment, Algorithms, Market).  
- **Risk Levels**: Computed from threat score + unresolved tasks; bubbled into Portal alerts (Red/Yellow).  
- **Revenue Impact Model**: Links each competitor move to estimated revenue-at-risk/opportunity using KPI map.  
- **Progressive Summaries**: Portal stores excerpted briefs for exec view; clicking expands full Charter-standard write-up.

Data delivery path: Reflex publishes JSON to `client_portal.intel` bucket (with versioning) → Portal ingestion worker syncs every 5 minutes → UI components pull via GraphQL. Cache invalidation occurs on new Custodian hash detection.

## Implementation Phasing
| Phase | Focus | Exit Criteria |
| --- | --- | --- |
| **P0 – Foundation (Week 1)** | Stand up Competitor Definition Map, baseline agent runners, shared schemas. | All Tier 0 clients populated; agents healthy; sample CIE payload validated. |
| **P1 – Reflex Wiring (Week 2)** | Comparator scoring, Reflex templates, Teamwork API plumbing. | ≥3 competitor deltas auto-create Teamwork tasks end-to-end. |
| **P2 – Portal Surfaces (Week 3)** | Client Portal data model, dashboards, alerts. | Clients see live Competitor Intelligence tab + radar data. |
| **P3 – Optimization (Week 4+)** | Confidence tuning, KPI impact modeling, governance automation. | False-positive rate <10%, Custodian compliance 100%. |

## Governance, Telemetry & QA
- **Confidence Scoring**: Weighted blend of source reliability, delta magnitude, historical accuracy. Stored with each CIE.  
- **Custodian Hash**: SHA-256 over structured payload + evidence URIs; required before dispatch.  
- **Reviewer Workflow**: High-impact events (impact ≥ High) require Custodian sign-off before Teamwork emission; others auto-publish with retro review.  
- **Observability**: Agent logs to centralized stack, Reflex metrics exported to Heartbeats (success/failure counts, SLA).  
- **Testing**:  
  - Simulation harness that replays historical competitor moves to validate scoring + task templates.  
  - Portal snapshot tests for radar/alerts.  
  - Governance audit verifying each event traceable to evidence.

## Dependencies & Open Items
- API creds for ad/library sources, SEO data, and social monitors.  
- Teamwork service account with scoped permissions.  
- Portal ingestion worker update to accept `client_portal.intel` payloads.  
- Custodian review roster (per client) loaded into Definition Map.  
- KPI → Revenue coefficients per client (supplied by Finance) to unlock revenue impact modeling.

Charter integrity now demands execution: once these docs are implemented, MAOS gains full-spectrum awareness and can drive predictive, adaptive, and autonomous client strategy updates.

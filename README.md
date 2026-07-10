# AutoTube — Headless YouTube Channel Empire

A local-first, **multi-agent** platform that runs faceless YouTube Shorts channels end-to-end —
from idea to published, monetized, promoted, and analyzed video — with zero day-to-day intervention.
Built to operate **many channels at once** (a "channel empire") with per-channel autonomy,
revenue optimization, paid promotion, and a polished operator dashboard.

---

## Table of contents
- [What it does](#what-it-does)
- [Tech stack](#tech-stack)
- [Quick start](#quick-start)
- [Architecture](#architecture)
- [The multi-agent pipeline](#the-multi-agent-pipeline)
- [Web app (UX)](#web-app-ux)
- [Revenue streams](#revenue-streams)
- [Ad spend & paid-promotion planning](#ad-spend--paid-promotion-planning)
- [Video quality](#video-quality)
- [Scaling to many channels](#scaling-to-many-channels)
- [Scheduling & autonomy](#scheduling--autonomy)
- [Cost guardrails](#cost-guardrails)
- [Configuration (.env)](#configuration-env)
- [API overview](#api-overview)
- [Data model](#data-model)
- [Security & compliance notes](#security--compliance-notes)
- [Roadmap (shipped)](#roadmap-shipped)

---

## What it does
- **Connect** existing YouTube channels via OAuth (a guided onboarding wizard).
- **Produce** faceless Shorts automatically: trend research → script → AI voiceover → visuals
  (stock + AI images + optional AI-video hero clips) → word-level captions → background music →
  Remotion render → SEO metadata → thumbnail → monetization → QA/brand-safety.
- **Publish** to YouTube on a schedule, with an optional per-channel human-approval gate.
- **Repurpose** each Short to TikTok & Instagram Reels with platform-tailored captions.
- **Monetize** via affiliate links, sponsor ad-reads, CTAs/lead magnets, and pinned comments.
- **Promote** top videos with paid ads and track true ROI/ROAS.
- **Grow** with A/B title experiments (auto-winner) and AI community engagement (comment replies).
- **Analyze** per-channel and per-video performance, revenue, and profit — and **auto-plan**
  the next uploads from what's working.

> **Note:** YouTube's API cannot *create* new channels (ToS). AutoTube onboards and fully
> automates **existing** channels you connect via OAuth.

---

## Tech stack
- **Backend:** Python 3.11 + FastAPI, custom agent orchestrator, Celery + Redis (queue & beat)
- **Render:** Remotion (Node) service — vertical 1080×1920 composition, word-level captions,
  Ken Burns motion, background-music mixing
- **Web UI:** React (Vite + TypeScript) with a custom design system
- **Data:** PostgreSQL (SQLAlchemy) · Redis · MinIO (S3-compatible object storage)
- **AI providers:** OpenAI (scripts, SEO, images, thumbnails, moderation), ElevenLabs (voice),
  Google Veo 3 / Runway / Luma / Kling (pluggable AI-video hero clips), Pexels (stock),
  faster-whisper (local captions)
- **Orchestration:** Docker Compose for the full local stack

---

## Quick start
```bash
cp .env.example .env        # fill in your API keys + YouTube OAuth credentials
docker compose up --build   # postgres, redis, minio, backend, worker, render, web
```
- **Web UI:** http://localhost:5173  (default login `admin` / the `ADMIN_PASSWORD` in `.env`)
- **API docs:** http://localhost:8000/docs
- **MinIO console:** http://localhost:9001

First run: open the web app → **Channels → Setup wizard** → connect a channel → pick a niche
preset → set cadence & monetization → done.

---

## Architecture
```
docker-compose.yml        Postgres · Redis · MinIO · backend · worker · render · web
backend/                  FastAPI app
  app/
    agents/               the specialized agents (see below)
    orchestrator/         runner: pipeline, approval gate, scheduler, experiments
    integrations/         youtube, openai, elevenlabs, pexels, whisper, video providers, social, google_ads
    services/             storage, cost_guard, distribution, engagement, ads
    api/routes/           channels, videos, jobs, calendar, analytics, distribution,
                          bulk, experiments, engagement, ads, system, auth
    models/               SQLAlchemy models
    workers/              Celery app + tasks + beat schedule
render/                   Remotion Node service (HTTP /render → mp4)
web/                      React dashboard (Vite + TS)
```

---

## The multi-agent pipeline
Each agent is a focused specialist. The orchestrator (`app/orchestrator/runner.py`) runs them in
order, persists state per step, enforces the approval gate, and retries on failure.

| # | Agent | Responsibility |
|---|-------|----------------|
| 1 | **Research** | Picks the topic (explicit → calendar entry → AI trend suggestion) |
| 2 | **Script** | Hook + narration + visual beats; inserts sponsor ad-reads |
| 3 | **Voiceover** | ElevenLabs TTS → audio |
| 4 | **Visuals** | Per-beat stock (Pexels) / AI image (DALL·E) / AI-video hero clip |
| 5 | **Captions** | Local faster-whisper word-level alignment |
| 6 | **Render** | Calls the Remotion service → final vertical MP4 (with music) |
| 7 | **SEO** | Title, description, tags + A/B title variants |
| 8 | **Thumbnail** | Generates an eye-catching thumbnail, set on publish |
| 9 | **Monetize** | Affiliate links, CTA/lead magnet, pinned comment |
| 10 | **QA** | Moderation brand-safety + duration/caption/metadata checks (hard-gate) |
| 11 | **Publish** | Uploads to YouTube, schedules, pins comment, cross-posts |
| — | **Analytics** | Pulls YouTube analytics + revenue (scheduled) |
| — | **Strategy** | Re-plans the content calendar from performance (scheduled) |

---

## Web app (UX)
A multi-section dashboard with a custom design system (toasts, modals, drawers, skeletons,
empty states, light/dark theme):

- **Dashboard** — empire overview: cross-channel KPIs, profit leaderboard, live activity feed
- **Channels** — onboard/configure, per-channel settings, bulk ops, onboarding wizard
- **Library** — filter/search all videos, preview, per-video analytics drill-down, thumbnail regen
- **Insights** — per-channel views, watch time, CTR, revenue, ROI, daily chart
- **Calendar** — drag-and-drop 14-day board to reschedule; add/override uploads; auto-plan
- **Monetization** — affiliate links, sponsor reads, CTAs, pinned comments
- **Paid Promotion** — ad campaign planner, launch/track, ROAS
- **Experiments** — A/B title variants with auto-winner
- **Engagement** — AI comment replies with a channel persona
- **Approvals** — live pipeline stepper + approval queue
- **Settings** — provider status, cost caps, ad budget, theme

---

## Revenue streams
AutoTube is designed to stack multiple monetization paths per channel:

1. **YouTube ad revenue** — tracked via the YouTube Analytics monetary API (CPM/RPM/estimated
   revenue) and rolled into the profit dashboard.
2. **Affiliate links** — the Monetize agent injects keyword-matched (or evergreen) affiliate
   links into descriptions and a pinned comment.
3. **Sponsorships** — configure a sponsor ad-read that gets voiced into the video, plus a sponsor
   credit in the description.
4. **Lead magnets / products** — CTA + lead URL drive viewers to a newsletter, digital product,
   or merch.
5. **Cross-platform reach** — the same Short is repurposed to TikTok & Reels to multiply
   impressions (and thus revenue).

All spend (production + ads) is recorded in a **cost ledger**, so every view of revenue is shown
as **net profit = revenue − total spend**.

---

## Ad spend & paid-promotion planning
Paid promotion amplifies organic winners and jump-starts reach. It is a first-class,
budget-governed subsystem.

**Where ad spend integrates**
- Campaigns promote **published** videos (typically your best organic performers).
- Every dollar of ad spend is written to the **cost ledger** (`provider="ads"`), so it flows
  straight into the ROI/profit math and yields true **ROAS** (revenue ÷ ad spend).
- A **monthly ad budget** and a **target ROAS** live in Settings (`AppSettings`).

**How the planner decides (amplify winners, not losers)**
```
score = 0.6 * retention + 0.3 * engagement + 0.1 * recency
  retention  = avg_view_duration / ~45s
  engagement = (likes + comments) / views
  recency    = 1 − age_days / 30
```
The monthly budget is split across the top-scoring published videos **weighted by score**, with a
suggested daily budget per campaign. Videos already being promoted are skipped.

**Lifecycle**
1. **Plan** — `POST /ads/plan` (or the "Generate plan" button) creates `planned` campaigns from
   the budget.
2. **Launch** — activates a campaign (via the Google Ads API if configured, else manual).
3. **Track** — a daily `sync_ads` job pulls live stats and records incremental spend to the
   ledger; when a campaign's total budget is exhausted it auto-completes.
4. **Optimize** — with `ad_auto_promote` on, the scheduler re-plans daily within budget.

**Manual mode (no Google Ads account):** campaigns stay in `planned`/`active` and you record spend
with `+ Spend` on the Ads page — it still counts toward ROI/ROAS. To go fully automatic, set
`GOOGLE_ADS_DEVELOPER_TOKEN` and `GOOGLE_ADS_CUSTOMER_ID` and wire `integrations/google_ads.py`.

**Recommended ad strategy**
- Start manual: promote 2–3 of your best-retention videos with a small daily budget.
- Keep **target ROAS ≥ 2** and let the planner concentrate budget on proven winners.
- Use the **Paid Promotion** page's ROAS card to prune underperformers.

---

## Video quality
- **Hybrid visuals:** Pexels stock backbone + DALL·E images (Ken Burns) + optional AI-video hero
  clips from **Veo 3 / Runway / Luma / Kling** (pluggable, per-channel).
- **Word-level captions** (TikTok-style highlight) via local faster-whisper.
- **Background music** mixed under narration at a configurable volume.
- **QA/brand-safety agent** blocks unsafe content (OpenAI moderation) and validates duration,
  captions, and metadata before publish.
- **Thumbnails** generated by DALL·E and applied on publish (regenerate any time).

---

## Scaling to many channels
- **Niche presets** (Scary Stories, Fun Facts, Motivation, History, Tech, Money) configure a
  channel instantly and seed its calendar.
- **Bulk operations:** multi-select channels → apply preset, run pipelines, toggle autonomy.
- **Per-channel settings:** cadence, voice, cost cap, cross-post targets, music, AI-video
  provider, engagement persona.

---

## Scheduling & autonomy
Celery beat drives hands-off operation:
- **`scheduler_tick`** (every 5 min) — runs due calendar entries for autonomous channels.
- **`daily_maintenance`** (03:00 UTC) — refresh analytics + re-plan calendars.
- **`rotate_experiments`** (every 6 h) — advance A/B title tests, settle winners.
- **`engage_comments`** (every 4 h) — AI comment replies for opted-in channels.
- **`sync_ads`** (04:00 UTC) — sync ad spend and auto-plan promotions within budget.

Per channel you can set **autonomous** (auto-run on schedule) and **require approval**
(pause before publish for review).

---

## Cost guardrails
Every paid API call is pre-checked against caps (env defaults, overridable at runtime in Settings):
- **Per-video**, **per-channel/day**, and **global/day** USD caps.
- A **cost ledger** records actual spend per provider/operation for ROI and enforcement.

---

## Configuration (.env)
Key variables (see `.env.example` for the full list):

| Group | Vars |
|-------|------|
| Core | `SECRET_KEY`, `TOKEN_ENCRYPTION_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` |
| Data | `DATABASE_URL`, `REDIS_URL`, `S3_*` |
| AI | `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`, `PEXELS_API_KEY`, `WHISPER_MODEL` |
| AI video | `VIDEO_PROVIDER`, `VEO_ENABLED`, `VERTEX_*`, `RUNWAY_API_KEY`, `LUMA_API_KEY`, `KLING_*` |
| YouTube | `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REDIRECT_URI`, `WEB_APP_URL` |
| Distribution | `TIKTOK_ACCESS_TOKEN`, `INSTAGRAM_ACCESS_TOKEN` |
| Ads | `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CUSTOMER_ID` |
| Cost caps | `COST_CAP_PER_VIDEO_USD`, `COST_CAP_PER_CHANNEL_DAILY_USD`, `COST_CAP_GLOBAL_DAILY_USD` |

Generate a token-encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## API overview
All endpoints are under `/api` and protected by HTTP Basic (single-user local auth).

| Prefix | Purpose |
|--------|---------|
| `/auth/youtube/*` | OAuth onboarding (start + callback) |
| `/channels` | List/update channels, voices, per-channel monetization |
| `/videos` | List, detail, media URLs, thumbnail regen |
| `/jobs` | Trigger runs, approve/reject |
| `/calendar` | CRUD + auto-plan the content calendar |
| `/analytics` | Channel summary, daily series, revenue/ROI, per-video drill-down |
| `/distribution` | Cross-platform repurposing |
| `/experiments` | A/B title experiments |
| `/engagement` | Comment engagement |
| `/ads` | Campaign plan/launch/spend/summary (ROAS) |
| `/bulk` | Presets + bulk channel operations |
| `/system` | Status, empire overview, runtime config |

Interactive docs at `/docs`.

---

## Data model
`Channel`, `Video`, `Job`, `CalendarEntry`, `AnalyticsSnapshot`, `CostLedgerEntry`,
`Monetization`, `Distribution`, `TitleExperiment`, `CommentReply`, `AppSettings`, `AdCampaign`.

---

## Security & compliance notes
- **OAuth refresh tokens are encrypted at rest** (Fernet, `TOKEN_ENCRYPTION_KEY`).
- Single-user HTTP Basic auth for the local dashboard; keep it on `localhost`.
- **Respect platform ToS:** YouTube channel *creation* is manual; TikTok/Reels/Google Ads
  automation requires approved apps/accounts — otherwise use the manual export/record flows.
- QA agent runs **OpenAI moderation** to avoid publishing unsafe content.
- Set strong `ADMIN_PASSWORD`, `SECRET_KEY`, and `TOKEN_ENCRYPTION_KEY` before any non-local use.

---

## Roadmap (shipped)
- **P0–P5** — foundation, OAuth onboarding, content pipeline, approval gate, analytics + strategy,
  full autonomy.
- **E1–E7** — monetization analytics/ROI, revenue agents, multi-platform distribution, music + QA,
  multi-provider AI video, niche presets + bulk ops, A/B title experiments.
- **U1–U6** — design system, empire dashboard, video library, live job progress, thumbnail agent,
  comment engagement.
- **C1–C5** — onboarding wizard, global settings, per-video drill-down, drag-drop calendar,
  paid ad-spend planning + ROAS.

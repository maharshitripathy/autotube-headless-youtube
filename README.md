# AutoTube — Headless YouTube Automation

A local-first, multi-agent system that runs faceless YouTube Shorts channels end-to-end:
research → script → voiceover → visuals → captions → render → SEO → publish → analytics → strategy.

## Stack
- **Backend:** Python 3.11 + FastAPI, LangGraph orchestrator, Celery workers
- **Render:** Remotion (Node) service for video assembly + word-level captions
- **Web UI:** React (Vite + TypeScript)
- **Infra:** Postgres, Redis, MinIO (S3-compatible object storage) via Docker Compose
- **Providers:** OpenAI (scripts, images), ElevenLabs (voice), Google Veo 3 via Vertex AI (optional hero clips), Pexels (stock), faster-whisper (local captions)

## Quick start
```bash
cp .env.example .env        # fill in your API keys
docker compose up --build   # starts postgres, redis, minio, backend, render, web
```
- Web UI: http://localhost:5173
- API docs: http://localhost:8000/docs
- MinIO console: http://localhost:9001

## Architecture
```
backend/   FastAPI app, agents, orchestrator
render/    Remotion Node service
web/       React dashboard
workers/   Celery tasks + scheduler
infra/     compose + local service config
```

## Phases
- **P0** Foundation (this scaffold)
- **P1** YouTube OAuth onboarding + channel selector
- **P2** Content pipeline (agents 1–6)
- **P3** Publish + approval gate
- **P4** Analytics + strategy calendar
- **P5** Full autonomy

> Note: YouTube's API cannot create new channels (ToS). The onboarding wizard connects existing channels via OAuth.

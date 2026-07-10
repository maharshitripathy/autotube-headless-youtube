"""OpenAI integration: scripts, SEO metadata, and images."""
from __future__ import annotations

import base64
import json

from openai import OpenAI

from app.config import settings

# Rough price estimates (USD) used only for pre-flight cost-cap checks.
EST_SCRIPT_USD = 0.03
EST_IMAGE_USD = 0.04  # dall-e-3 standard 1024x1792


def _client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def generate_script(topic: str, niche: str | None, max_seconds: int = 45) -> dict:
    """Return {hook, script, beats[]} for a faceless Short."""
    system = (
        "You are an expert short-form scriptwriter for faceless YouTube Shorts. "
        "Write punchy, retention-optimized narration with a strong 3-second hook. "
        "Return strict JSON."
    )
    user = (
        f"Topic: {topic}\nNiche: {niche or 'general'}\n"
        f"Target length: {max_seconds}s of narration.\n"
        'Return JSON: {"hook": str, "script": str, '
        '"beats": [{"text": str, "visual_query": str}]}'
    )
    resp = _client().chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    return json.loads(resp.choices[0].message.content)


def generate_metadata(topic: str, script: str) -> dict:
    """Return {title, description, tags[]} optimized for YouTube SEO."""
    system = "You are a YouTube SEO expert. Return strict JSON."
    user = (
        f"Topic: {topic}\nScript: {script}\n"
        'Return JSON: {"title": str (<=70 chars, includes hook), '
        '"description": str (with hashtags), "tags": [str]}'
    )
    resp = _client().chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    return json.loads(resp.choices[0].message.content)


def generate_image(prompt: str, size: str = "1024x1792") -> bytes:
    """Generate a vertical image for a beat. Returns PNG bytes."""
    resp = _client().images.generate(
        model="dall-e-3", prompt=prompt, size=size, response_format="b64_json", n=1
    )
    return base64.b64decode(resp.data[0].b64_json)


def generate_title_variants(topic: str, script: str, n: int = 3) -> list[str]:
    """Generate N distinct, high-CTR title variants for A/B testing."""
    system = "You are a YouTube title strategist. Return strict JSON."
    user = (
        f"Topic: {topic}\nScript: {script}\n"
        f'Generate {n} DISTINCT high-CTR titles (<=70 chars each) with different '
        'angles (curiosity, list, bold claim). Return JSON: {"titles": [str]}'
    )
    resp = _client().chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    return json.loads(resp.choices[0].message.content).get("titles", [])


def moderate(text: str) -> dict:
    """Run OpenAI moderation. Returns {flagged: bool, categories: [str]}."""
    try:
        resp = _client().moderations.create(model="omni-moderation-latest", input=text)
        result = resp.results[0]
        flagged_cats = [k for k, v in result.categories.__dict__.items() if v]
        return {"flagged": bool(result.flagged), "categories": flagged_cats}
    except Exception:
        return {"flagged": False, "categories": []}


def suggest_topics(niche: str, recent_titles: list[str], count: int = 5) -> list[str]:
    """Ask the model for trending topic ideas given the niche and history."""
    system = "You are a viral content strategist. Return strict JSON."
    user = (
        f"Niche: {niche}\nRecent titles: {recent_titles}\n"
        f'Suggest {count} fresh, non-duplicate Short topics. '
        'Return JSON: {"topics": [str]}'
    )
    resp = _client().chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    return json.loads(resp.choices[0].message.content).get("topics", [])

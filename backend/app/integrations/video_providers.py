"""Pluggable AI-video providers for hero clips.

Each provider exposes a uniform interface:
  - name: str
  - is_enabled() -> bool
  - estimate_cost(seconds) -> float
  - generate_clip(prompt, seconds) -> bytes  (9:16 MP4)

`select_provider(channel)` returns the provider chosen per-channel (or the
global default), or None when no provider is enabled.
"""
from __future__ import annotations

import time

import httpx

from app.config import settings


class VideoProvider:
    name = "base"

    def is_enabled(self) -> bool:
        raise NotImplementedError

    def estimate_cost(self, seconds: int) -> float:
        raise NotImplementedError

    def generate_clip(self, prompt: str, seconds: int = 5) -> bytes:
        raise NotImplementedError


class VeoProvider(VideoProvider):
    name = "veo"

    def is_enabled(self) -> bool:
        from app.integrations import vertex_veo
        return vertex_veo.is_enabled()

    def estimate_cost(self, seconds: int) -> float:
        from app.integrations import vertex_veo
        return vertex_veo.EST_VEO_USD_PER_CLIP

    def generate_clip(self, prompt: str, seconds: int = 5) -> bytes:
        from app.integrations import vertex_veo
        return vertex_veo.generate_clip(prompt, seconds)


class RunwayProvider(VideoProvider):
    name = "runway"
    _BASE = "https://api.dev.runwayml.com/v1"

    def is_enabled(self) -> bool:
        return bool(settings.runway_api_key)

    def estimate_cost(self, seconds: int) -> float:
        return 0.25 * seconds

    def generate_clip(self, prompt: str, seconds: int = 5) -> bytes:
        headers = {"Authorization": f"Bearer {settings.runway_api_key}",
                   "X-Runway-Version": "2024-11-06"}
        with httpx.Client(timeout=600) as client:
            resp = client.post(
                f"{self._BASE}/text_to_video",
                headers=headers,
                json={"promptText": prompt, "duration": seconds,
                      "ratio": "720:1280", "model": "gen4_turbo"},
            )
            resp.raise_for_status()
            task_id = resp.json()["id"]
            url = self._poll(client, headers, task_id)
            return client.get(url, timeout=300).content

    def _poll(self, client: httpx.Client, headers: dict, task_id: str) -> str:
        for _ in range(120):
            r = client.get(f"{self._BASE}/tasks/{task_id}", headers=headers)
            r.raise_for_status()
            data = r.json()
            if data["status"] == "SUCCEEDED":
                return data["output"][0]
            if data["status"] in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"Runway task {data['status']}")
            time.sleep(5)
        raise TimeoutError("Runway task timed out")


class LumaProvider(VideoProvider):
    name = "luma"
    _BASE = "https://api.lumalabs.ai/dream-machine/v1"

    def is_enabled(self) -> bool:
        return bool(settings.luma_api_key)

    def estimate_cost(self, seconds: int) -> float:
        return 0.20 * seconds

    def generate_clip(self, prompt: str, seconds: int = 5) -> bytes:
        headers = {"Authorization": f"Bearer {settings.luma_api_key}",
                   "Content-Type": "application/json"}
        with httpx.Client(timeout=600) as client:
            resp = client.post(
                f"{self._BASE}/generations",
                headers=headers,
                json={"prompt": prompt, "aspect_ratio": "9:16", "model": "ray-2"},
            )
            resp.raise_for_status()
            gen_id = resp.json()["id"]
            url = self._poll(client, headers, gen_id)
            return client.get(url, timeout=300).content

    def _poll(self, client: httpx.Client, headers: dict, gen_id: str) -> str:
        for _ in range(120):
            r = client.get(f"{self._BASE}/generations/{gen_id}", headers=headers)
            r.raise_for_status()
            data = r.json()
            if data["state"] == "completed":
                return data["assets"]["video"]
            if data["state"] == "failed":
                raise RuntimeError("Luma generation failed")
            time.sleep(5)
        raise TimeoutError("Luma generation timed out")


class KlingProvider(VideoProvider):
    name = "kling"

    def is_enabled(self) -> bool:
        return bool(settings.kling_access_key and settings.kling_secret_key)

    def estimate_cost(self, seconds: int) -> float:
        return 0.30 * seconds

    def generate_clip(self, prompt: str, seconds: int = 5) -> bytes:
        # Kling requires JWT signing with access/secret keys; wire up when used.
        raise NotImplementedError("Kling provider not yet wired to live API.")


_PROVIDERS: dict[str, VideoProvider] = {
    "veo": VeoProvider(),
    "runway": RunwayProvider(),
    "luma": LumaProvider(),
    "kling": KlingProvider(),
}


def get_provider(name: str | None) -> VideoProvider | None:
    if not name or name == "none":
        return None
    return _PROVIDERS.get(name)


def select_provider(channel) -> VideoProvider | None:
    """Pick the per-channel provider, else the global default; must be enabled."""
    preferred = getattr(channel, "hero_video_provider", None) or settings.video_provider
    provider = get_provider(preferred)
    if provider and provider.is_enabled():
        return provider
    return None

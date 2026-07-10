"""Google Veo 3 (via Vertex AI) optional hero-clip generation.

Disabled unless VEO_ENABLED=true and Vertex credentials are configured.
Kept as a pluggable provider so the pipeline works without it.
"""
from __future__ import annotations

import time

from app.config import settings

EST_VEO_USD_PER_CLIP = 0.75  # ~5s clip, coarse estimate for cost caps


class VeoDisabled(RuntimeError):
    pass


def is_enabled() -> bool:
    return bool(settings.veo_enabled and settings.vertex_project_id)


def generate_clip(prompt: str, seconds: int = 5) -> bytes:
    """Generate a short hero clip with Veo 3. Returns MP4 bytes.

    Uses Vertex AI's video generation model. Raises VeoDisabled if not configured.
    """
    if not is_enabled():
        raise VeoDisabled("Veo is disabled or Vertex project is not configured.")

    # Imported lazily so the dependency is optional at runtime.
    import vertexai
    from vertexai.preview.vision_models import VideoGenerationModel

    vertexai.init(project=settings.vertex_project_id, location=settings.vertex_location)
    model = VideoGenerationModel.from_pretrained("veo-3.0-generate-preview")

    operation = model.generate_videos(
        prompt=prompt,
        number_of_videos=1,
        duration_seconds=seconds,
        aspect_ratio="9:16",
    )
    # Poll until the long-running operation completes.
    while not operation.done:
        time.sleep(5)
        operation.refresh()

    videos = operation.result.generated_videos
    if not videos:
        raise RuntimeError("Veo returned no video.")
    return videos[0].video.video_bytes

import os
import time
from typing import Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import vertexai
from vertexai.preview.vision_models import VideoGenerationModel

class VeoClient:
    def __init__(self):
        self.project = os.environ["GCP_PROJECT"]
        self.location = os.environ.get("VERTEX_LOCATION", "us-central1")
        self.model_name = os.environ.get("VEO_MODEL", "veo-3.0")
        vertexai.init(project=self.project, location=self.location)
        self.model = VideoGenerationModel(self.model_name)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=16),
        retry=retry_if_exception_type(Exception),
    )
    def generate_video(self, prompt: str, duration_seconds: int = 45) -> Tuple[bytes, int]:
        """
        Synchronously generate a single MP4 clip; returns (mp4_bytes, latency_ms)
        (If your project has async long-running ops, you can adapt to poll Operation.)
        """
        start = time.time()
        result = self.model.generate_video(
            prompt=prompt,
            duration_seconds=duration_seconds,
            # optional params: fps, aspect_ratio, style_preset, etc.
        )
        # Normalization across SDK versions:
        if hasattr(result, "video_bytes"):
            mp4_bytes = result.video_bytes
        else:
            mp4_bytes = result[0].video_bytes  # type: ignore
        latency_ms = int((time.time() - start) * 1000)
        return mp4_bytes, latency_ms

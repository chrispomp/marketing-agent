import os
import base64
import time
from typing import Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import vertexai
from vertexai.vision_models import ImageGenerationModel

class ImagenClient:
    def __init__(self):
        self.project = os.environ["GCP_PROJECT"]
        self.location = os.environ.get("VERTEX_LOCATION", "us-central1")
        self.model_name = os.environ.get("IMAGEN_MODEL", "imagen-4.0-generate")
        vertexai.init(project=self.project, location=self.location)
        self.model = ImageGenerationModel(self.model_name)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=16),
        retry=retry_if_exception_type(Exception),
    )
    def generate_image(self, prompt: str, image_size: str = "1024x1024") -> Tuple[bytes, int]:
        """
        Returns (image_bytes_png, latency_ms)
        """
        start = time.time()
        result = self.model.generate_images(
            prompt=prompt,
            number_of_images=1,
            image_size=image_size,
            # optional: safety filter tuning, style, etc.
        )
        img = result.images[0]
        # SDK returns PIL Image-like or bytes depending on version; normalize to bytes
        if hasattr(img, "to_bytes"):
            png_bytes = img.to_bytes()
        elif hasattr(img, "image_bytes"):
            png_bytes = img.image_bytes
        else:
            # some versions provide base64
            png_bytes = base64.b64decode(img.base64_data)  # type: ignore
        latency_ms = int((time.time() - start) * 1000)
        return png_bytes, latency_ms

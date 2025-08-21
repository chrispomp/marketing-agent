import os
import time
from typing import Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import vertexai
from vertexai.vision_models import ImageGenerationModel, Image

class ImagenClient:
    def __init__(self):
        self.project = os.environ["GCP_PROJECT"]
        self.location = os.environ.get("VERTEX_LOCATION", "us-central1")
        self.model_name = os.environ.get("IMAGEN_MODEL", "imagen-4.0-generate")
        vertexai.init(project=self.project, location=self.location)
        self.model = ImageGenerationModel.from_pretrained(self.model_name)

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

        width, height = map(int, image_size.split("x"))

        response = self.model.generate_images(
            prompt=prompt,
            number_of_images=1,
            width=width,
            height=height,
        )

        img: Image = response.images[0]
        png_bytes = img._image_bytes

        latency_ms = int((time.time() - start) * 1000)
        return png_bytes, latency_ms

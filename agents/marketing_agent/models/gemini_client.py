import os
import time
from typing import Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from vertexai.generative_models import GenerativeModel, SafetySetting
import vertexai

class GeminiClient:
    def __init__(self):
        self.project = os.environ["GCP_PROJECT"]
        self.location = os.environ.get("VERTEX_LOCATION", "us-central1")
        self.model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
        vertexai.init(project=self.project, location=self.location)
        self.model = GenerativeModel(self.model_name)

        # Conservative safety defaults; adjust per policy.
        self.safety = [
            SafetySetting.HarmBlockThreshold.HARM_BLOCK_THRESHOLD_MEDIUM  # type: ignore
        ]

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
    )
    def generate(self, prompt: str, system_instruction: str = "") -> Tuple[str, int, int, int]:
        """
        Returns text, tokens_in, tokens_out, latency_ms
        """
        start = time.time()
        content = []
        if system_instruction:
            content.append({"role": "user", "parts": [system_instruction + "\n\n" + prompt]})
        else:
            content.append({"role": "user", "parts": [prompt]})

        resp = self.model.generate_content(
            content,
            safety_settings=self.safety,
            generation_config={"temperature": 0.4, "top_p": 0.9, "top_k": 40, "max_output_tokens": 2048},
        )
        text = resp.text or ""
        usage = getattr(resp, "usage_metadata", None)
        tokens_in = getattr(usage, "prompt_token_count", 0) if usage else 0
        tokens_out = getattr(usage, "candidates_token_count", 0) if usage else 0
        latency_ms = int((time.time() - start) * 1000)
        return text, tokens_in, tokens_out, latency_ms

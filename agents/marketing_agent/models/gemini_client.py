import os
import time
from typing import Tuple, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from vertexai.generative_models import (
    GenerativeModel,
    SafetySetting,
    HarmCategory,
    HarmBlockThreshold,
    GenerationConfig,
)
import vertexai

class GeminiClient:
    def __init__(self):
        self.project = os.environ["GCP_PROJECT"]
        self.location = os.environ.get("VERTEX_LOCATION", "us-central1")
        self.model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
        vertexai.init(project=self.project, location=self.location)

        # Conservative safety defaults; adjust per policy.
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
    )
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> Tuple[str, int, int, int]:
        """
        Returns text, tokens_in, tokens_out, latency_ms
        """
        start = time.time()

        model = GenerativeModel(
            self.model_name, system_instruction=system_instruction
        )

        generation_config = GenerationConfig(
            temperature=0.4,
            top_p=0.9,
            top_k=40,
            max_output_tokens=2048,
        )

        resp = model.generate_content(
            [prompt],
            generation_config=generation_config,
            safety_settings=self.safety_settings,
        )

        text = resp.text or ""
        usage = getattr(resp, "usage_metadata", None)
        tokens_in = getattr(usage, "prompt_token_count", 0) if usage else 0
        tokens_out = getattr(usage, "candidates_token_count", 0) if usage else 0
        latency_ms = int((time.time() - start) * 1000)
        return text, tokens_in, tokens_out, latency_ms

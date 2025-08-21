import time
import json
import concurrent.futures
from typing import List
from agents.marketing_agent.models.gemini_client import GeminiClient
from agents.marketing_agent.models.imagen_client import ImagenClient
from agents.marketing_agent.models.veo_client import VeoClient
from agents.marketing_agent.storage.gcs import upload_bytes, gcs_path
from agents.marketing_agent.utils import slugify

BRIEF_SYS = """You are a senior marketing strategist. Produce a concise, structured marketing brief in Markdown with:
- Objective
- Target Audience
- Key Message
- Tone of Voice
- Mandatories
Keep it crisp, actionable, and brand-agnostic unless specified.
"""

SCRIPT_SYS = """You are a senior copywriter. Produce a 30s TVC screenplay in standard format:
- Scene Heading (INT/EXT – LOCATION – TIME)
- Action
- Character: DIALOGUE
Use 3-4 scenes, concise lines, cinematic pacing, and include brief SFX/VFX cues where helpful.
"""

SCENE_SYS = """You split a TV script into visual scenes. For each scene: a short, vivid image prompt suitable for a photorealistic storyboard frame (no text overlay, cinematic lighting, camera angle).
Respond with a JSON array of strings, where each string is a scene prompt. Example:
["A close up of a coffee cup.", "A person smiling."]
"""

ANIMATIC_SYS = """You are a storyboard-to-animatic producer. Produce a single concise prompt describing the overall commercial visuals, pacing, camera moves, transitions, and mood to generate a ~30-60s video."""
 
class MarketingAgent:
    def __init__(
        self,
        gemini_client: GeminiClient,
        imagen_client: ImagenClient,
        veo_client: VeoClient,
    ):
        self.gemini = gemini_client
        self.imagen = imagen_client
        self.veo = veo_client

    # FR-01
    def generate_brief(self, user_prompt: str):
        text, in_toks, out_toks, latency = self.gemini.generate(
            prompt=user_prompt, system_instruction=BRIEF_SYS
        )
        return text, in_toks, out_toks, latency

    # FR-02
    def generate_script(self, prompt: str = "", brief_markdown: str = ""):
        compound = ""
        if brief_markdown:
            compound += "=== PRIOR BRIEF ===\n" + brief_markdown + "\n\n"
        if prompt:
            compound += "=== REQUEST ===\n" + prompt
        else:
            compound += "Generate a 30-second script based on the brief."
        text, in_toks, out_toks, latency = self.gemini.generate(
            prompt=compound, system_instruction=SCRIPT_SYS
        )
        return text, in_toks, out_toks, latency

    # FR-03
    def generate_storyboard(self, script: str, image_size: str = "1024x1024"):
        scenes_text, _, _, _ = self.gemini.generate(
            prompt=script, system_instruction=SCENE_SYS
        )

        try:
            # Clean up the response from the model, which might be wrapped in ```json ... ```
            if scenes_text.strip().startswith("```json"):
                scenes_text = scenes_text.strip()[7:-3].strip()
            prompts = json.loads(scenes_text)
        except (json.JSONDecodeError, IndexError):
            print(f"Warning: Failed to parse JSON from scene generation: {scenes_text}")
            # Fallback to simple line splitting if JSON parsing fails
            prompts = [line.strip() for line in scenes_text.splitlines() if line.strip()]

        if not prompts:
            prompts = ["Wide establishing shot of the scenario"]  # fallback

        def generate_and_upload(idx, prompt):
            png_bytes, _ = self.imagen.generate_image(prompt=prompt, image_size=image_size)
            name = slugify(prompt) or f"scene-{idx}"
            path = gcs_path("storyboards", f"{name}", "png")
            gcs_url = upload_bytes(png_bytes, path, "image/png")
            return {
                "scene_number": idx,
                "scene_slug": name,
                "prompt": prompt,
                "gcs_url": gcs_url
            }

        storyboard = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_prompt = {executor.submit(generate_and_upload, idx, prompt): idx for idx, prompt in enumerate(prompts, start=1)}
            for future in concurrent.futures.as_completed(future_to_prompt):
                try:
                    result = future.result()
                    storyboard.append(result)
                except Exception as exc:
                    scene_idx = future_to_prompt[future]
                    # Log the error, maybe append an error item to the storyboard
                    print(f'Scene {scene_idx} generated an exception: {exc}')


        # Sort storyboard by scene number to maintain order
        storyboard.sort(key=lambda x: x['scene_number'])
        return storyboard

    # FR-04
    def generate_animatic(self, script: str, duration_seconds: int = 45) -> str:
        """
        Starts an async job to generate an animatic.
        Returns a job name.
        """
        prompt, _, _, _ = self.gemini.generate(
            prompt=script, system_instruction=ANIMATIC_SYS
        )
        job_name = self.veo.start_generate_video_job(prompt=prompt, duration_seconds=duration_seconds)
        return job_name

    def check_animatic_job_status(self, job_name: str):
        """
        Checks the status of an animatic generation job.
        """
        return self.veo.check_video_job_status(job_name)

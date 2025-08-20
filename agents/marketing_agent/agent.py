import time
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

SCENE_SYS = """You split a TV script into visual scenes. Return a numbered list. For each scene: a short, vivid image prompt suitable for a photorealistic storyboard frame (no text overlay, cinematic lighting, camera angle)."""

ANIMATIC_SYS = """You are a storyboard-to-animatic producer. Produce a single concise prompt describing the overall commercial visuals, pacing, camera moves, transitions, and mood to generate a ~30-60s video."""
 
class MarketingAgent:
    def __init__(self):
        self.gemini = GeminiClient()
        self.imagen = ImagenClient()
        self.veo = VeoClient()

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
        # Parse numbered list into (scene_number, prompt)
        lines = [l.strip() for l in scenes_text.splitlines() if l.strip()]
        items = []
        for l in lines:
            # Accept formats like "1) prompt", "1. prompt", "1 - prompt"
            if l[0].isdigit():
                # split off the leading number and delimiter
                prompt = l.split(" ", 1)[1] if " " in l else l
                items.append(prompt.strip("-.) ").strip())
        if not items:
            items = ["Wide establishing shot of the scenario"]  # fallback

        storyboard = []
        for idx, prompt in enumerate(items, start=1):
            png_bytes, _ = self.imagen.generate_image(prompt=prompt, image_size=image_size)
            name = slugify(prompt) or f"scene-{idx}"
            path = gcs_path("storyboards", f"{name}", "png")
            gcs_url = upload_bytes(png_bytes, path, "image/png")
            storyboard.append({
                "scene_number": idx,
                "scene_slug": name,
                "prompt": prompt,
                "gcs_url": gcs_url
            })
        return storyboard

    # FR-04
    def generate_animatic(self, script: str, duration_seconds: int = 45):
        prompt, _, _, _ = self.gemini.generate(
            prompt=script, system_instruction=ANIMATIC_SYS
        )
        mp4_bytes, _ = self.veo.generate_video(prompt=prompt, duration_seconds=duration_seconds)
        name = slugify(prompt or "animatic")
        path = gcs_path("animatics", f"{name}", "mp4")
        gcs_url = upload_bytes(mp4_bytes, path, "video/mp4")
        return gcs_url

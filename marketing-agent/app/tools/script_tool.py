import logging
from adk.tools import Tool
from vertexai.generative_models import GenerativeModel, Part

class ScriptTool(Tool):
    """A tool for writing commercial scripts."""

    def __init__(self):
        super().__init__(
            name="generate_script",
            description="Writes a commercial script based on a marketing brief or user prompt.",
        )
        self.model = GenerativeModel("gemini-2.5-pro")
        self.system_prompt = """
You are a professional Screenwriter. Your task is to write a compelling commercial script.
The output MUST follow industry-standard screenplay format:
- SCENE HEADINGS (e.g., INT. COFFEE SHOP - DAY) in all caps.
- ACTION descriptions are in present tense.
- DIALOGUE is centered under the character's name.

Transform the provided brief/prompt into a complete script.
"""

    def _call(self, prompt_or_brief: str) -> str:
        """Invokes Gemini 2.5 Pro to generate the script."""
        try:
            logging.info("Generating script...")
            full_prompt = [
                Part.from_text(self.system_prompt),
                Part.from_text(f"Input Brief/Prompt: {prompt_or_brief}")
            ]
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error in ScriptTool: {e}", exc_info=True)
            return "I'm sorry, I had trouble writing the script. Please provide more details or try again."

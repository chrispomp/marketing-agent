import logging
from adk.tools import Tool
from vertexai.generative_models import GenerativeModel, Part

class BriefTool(Tool):
    """A tool for generating structured marketing briefs."""

    def __init__(self):
        super().__init__(
            name="generate_brief",
            description="Generates a structured marketing brief based on user input about a product or campaign.",
        )
        self.model = GenerativeModel("gemini-2.5-pro")
        self.system_prompt = """
You are an expert Marketing Strategist. Your task is to take a user's prompt and transform it into a professional, structured marketing brief.
The output MUST be in Markdown format.
The brief must contain the following sections:
- ## Objective: The primary goal of the campaign.
- ## Target Audience: A detailed description of the intended audience.
- ## Key Message: The single most important takeaway for the audience.
- ## Tone of Voice: The style and personality of the communication.
- ## Mandatories: Any legal disclaimers, brand guidelines, or required elements.
"""

    def _call(self, prompt: str) -> str:
        """Invokes the Gemini 2.5 Pro model to generate the marketing brief."""
        try:
            logging.info(f"Generating brief for prompt: {prompt}")
            full_prompt = [
                Part.from_text(self.system_prompt),
                Part.from_text(f"User Prompt: {prompt}")
            ]
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error in BriefTool: {e}", exc_info=True)
            return "I'm sorry, I encountered an error while generating the brief. Please try again."

from adk.agent import Agent
from adk.config import STORE_CONVERSATIONS
from vertexai.generative_models import GenerativeModel

from app.agents.brief_writer import BriefWriter
from app.agents.script_writer import ScriptWriter
from app.agents.storyboard_artist import StoryboardArtist
from app.agents.animatic_creator import AnimaticCreator

# Enable conversation history for multi-turn interactions
STORE_CONVERSATIONS = True

class MarketingAgent(Agent):
    """
    An orchestrator agent that acts as a creative co-pilot. It routes tasks 
    for brief writing, script writing, storyboarding, and animatic creation 
    to specialized sub-agents.
    """
    def __init__(self):
        super().__init__(
            name="MarketingAgent",
            description="A creative co-pilot for generating marketing content like briefs, scripts, storyboards, and animatics.",
            model=GenerativeModel("gemini-2.5-pro")
        )
        
        # Add the specialized sub-agents. The orchestrator uses their
        # descriptions to decide which one to route a user's request to.
        self.add_sub_agent(BriefWriter())
        self.add_sub_agent(ScriptWriter())
        self.add_sub_agent(StoryboardArtist())
        self.add_sub_agent(AnimaticCreator())

    def resolve(self, prompt: str) -> str:
        """
        Main entry point for the Marketing Agent. It uses Gemini's reasoning
        to select and delegate to the correct sub-agent.
        """
        # The base Agent class's resolve method handles the routing logic.
        # It matches the user's prompt against the sub-agents' descriptions.
        # For sub-agents with custom resolve methods (like StoryboardArtist),
        # that method will be automatically called.
        return super().resolve(prompt)

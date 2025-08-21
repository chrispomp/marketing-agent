from adk.agent import Agent
from app.tools.brief_tool import BriefTool

class BriefWriter(Agent):
    """A specialized agent that crafts structured marketing briefs from user prompts."""
    def __init__(self):
        super().__init__(
            name="BriefWriter",
            description="Use this agent when the user wants to create, draft, or write a marketing brief.",
        )
        self.add_tool(BriefTool())

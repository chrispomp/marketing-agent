import os
from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

# Pin the model for production stability
GEMINI_MODEL = "gemini-2.5-flash"

async def generate_brief(
prompt: str,
tool_context: ToolContext
) -> str:
    """
    Generates a structured marketing brief from a user prompt.

    Args:
        prompt: The user's request for a marketing brief.
        tool_context: The context of the tool invocation.

    Returns:
        A Markdown-formatted marketing brief.
    """
    brief_agent = LlmAgent(
        model=GEMINI_MODEL,
        instruction="""You are a world-class Marketing Strategist. Your task is to create a structured, professional, and concise marketing brief based on the user's prompt.
The output must be in Markdown format and include the following sections:

### Objective
- What is the primary goal of this campaign?

### Target Audience
- Who are we trying to reach? Describe their demographics and psychographics.

### Key Message
- What is the single most important message we want to convey?

### Tone of Voice
- What is the desired personality of the campaign (e.g., witty, empowering, serious)?

### Mandatories & Constraints
- What are the absolute must-haves or things to avoid (e.g., brand guidelines, legal disclaimers)?
"""
    )

    # The runner is created on-the-fly to execute this specific, one-off task
    runner = tool_context.invocation_context.runner
    final_response = ""
    async for event in runner.run_sub_agent(agent=brief_agent, user_message=prompt, invocation_context=tool_context.invocation_context):
        if event.is_final_response() and event.content:
            final_response = "".join(part.text for part in event.content.parts if part.text)
            break
    return final_response

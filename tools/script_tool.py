import os
from google.adk.agents import LlmAgent, ToolContext
from google.genai.types import Content, Part

# Pin the model for production stability
GEMINI_MODEL = "gemini-2.5-flash"

async def generate_script(
prompt: str,
tool_context: ToolContext
) -> str:
    """
    Generates a formatted commercial script from a prompt, using conversational history for context.

    Args:
        prompt: The user's request for a script.
        tool_context: The context of the tool invocation, used to access conversation history.

    Returns:
        A formatted script following industry standards.
    """
    history = tool_context.invocation_context.session.events
    context_str = ""

    # Look for a previously generated brief in the conversation history
    if history:
        # Iterate backwards to find the most recent relevant content
        for event in reversed(history):
            if event.author != "user" and event.content:
                text_content = "".join(part.text for part in event.content.parts if part.text)
                if "### Objective" in text_content and "### Target Audience" in text_content:
                    context_str = f"Use the following marketing brief as context for the script:\n\n---\n{text_content}\n---\n"
                    break

    script_agent = LlmAgent(
        model=GEMINI_MODEL,
        instruction=f"""
You are a professional screenwriter specializing in short-form commercials.
Your task is to write a script based on the user's prompt.
{context_str}
The output must follow industry-standard screenplay format. Use clear scene headings (e.g., INT. COFFEE SHOP - DAY), concise action lines, and properly formatted dialogue.
The script should be paced appropriately for a 30-second commercial unless specified otherwise.
Ensure the script directly reflects the provided marketing brief.
"""
    )
    runner = tool_context.invocation_context.runner
    final_response = ""
    async for event in runner.run_sub_agent(agent=script_agent, user_message=prompt, invocation_context=tool_context.invocation_context):
        if event.is_final_response() and event.content:
            final_response = "".join(part.text for part in event.content.parts if part.text)
            break
    return final_response

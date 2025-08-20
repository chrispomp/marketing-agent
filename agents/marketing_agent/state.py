from typing import List, Dict
from agents.marketing_agent.schemas import ChatMessage

class ConversationState:
    """
    Minimal in-memory state. For production, back this with Redis/Firestore.
    """
    def __init__(self):
        self.sessions: Dict[str, List[ChatMessage]] = {}

    def get(self, session_id: str) -> List[ChatMessage]:
        return self.sessions.get(session_id, [])

    def append(self, session_id: str, message: ChatMessage):
        self.sessions.setdefault(session_id, []).append(message)

STATE = ConversationState()

from typing import Dict, Any, List
from datetime import datetime

MAX_HISTORY_TURNS = 10

class ContextManager:
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def _ensure_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "history": [], "colleges": [], "programs": [],
                "tests": [], "locations": [], "last_intent": None,
                "created_at": datetime.utcnow().isoformat(),
            }
        return self._sessions[session_id]

    def _merge_entities(self, session, entities):
        for key in ("colleges", "programs", "tests", "locations"):
            for val in entities.get(key, []):
                if val not in session[key]:
                    session[key].append(val)

    def update(self, session_id, user_message, entities=None, assistant_message=None, intent=None):
        session = self._ensure_session(session_id)
        turn = {"role": "user", "message": user_message, "timestamp": datetime.utcnow().isoformat()}
        if intent:
            turn["intent"] = intent
            session["last_intent"] = intent
        session["history"].append(turn)
        if assistant_message:
            session["history"].append({"role": "assistant", "message": assistant_message, "timestamp": datetime.utcnow().isoformat()})
        if entities:
            self._merge_entities(session, entities)
        if len(session["history"]) > MAX_HISTORY_TURNS * 2:
            session["history"] = session["history"][-(MAX_HISTORY_TURNS * 2):]

    def get(self, session_id: str) -> Dict[str, Any]:
        return self._ensure_session(session_id)

    def get_history_text(self, session_id: str, max_turns: int = 5) -> str:
        session = self._ensure_session(session_id)
        recent = session["history"][-(max_turns * 2):]
        return "\n".join(f"{e['role'].capitalize()}: {e['message']}" for e in recent)

    def clear(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())

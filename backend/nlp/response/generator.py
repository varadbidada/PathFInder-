import os, asyncio
from typing import Dict, Any, List

try:
    import anthropic
    _CLIENT = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY",""))
    _USE_ANTHROPIC = True
except ImportError:
    _CLIENT = None
    _USE_ANTHROPIC = False

SYSTEM_PROMPT = """You are an expert college admissions counsellor.
Help students with admission requirements, deadlines, financial aid, programs, and comparisons.
Be concise, warm, and encouraging. Keep responses under 250 words."""

def _format_docs(docs):
    if not docs: return "No documents retrieved."
    return "\n".join(f"[{i+1}] {d.get('text','')}" for i,d in enumerate(docs))

def _format_entities(entities):
    parts = [f"{k}: {', '.join(str(v) for v in vals)}" for k,vals in entities.items() if vals]
    return "; ".join(parts) or "None"

def _build_prompt(payload):
    query = payload.get("query","")
    intent = payload.get("intent","general_inquiry")
    entities = payload.get("entities",{})
    context = payload.get("context",{})
    retrieved = payload.get("retrieved_docs",[])
    history = context.get("history",[])
    hist_text = "\n".join(f"{t.get('role','user').capitalize()}: {t.get('message','')}" for t in history[-6:]) or "First message."
    return f"""## Query\n{query}\n\n## Intent\n{intent}\n\n## Entities\n{_format_entities(entities)}\n\n## History\n{hist_text}\n\n## Knowledge\n{_format_docs(retrieved)}\n\nAnswer helpfully and specifically."""

def _fallback(payload):
    intent = payload.get("intent","general_inquiry")
    entities = payload.get("entities",{})
    colleges = ", ".join(entities.get("colleges",[])) or "your target colleges"
    programs = ", ".join(entities.get("programs",[])) or "your chosen program"
    responses = {
        "greeting": "Hello! I'm your college admissions counsellor. Ask me about requirements, deadlines, financial aid, or anything admissions-related!",
        "admission_requirements": f"Admission to {colleges} typically requires a strong GPA (3.8+), high SAT/ACT scores, compelling essays, and strong recommendations. For {programs}, relevant extracurriculars and projects really help. Check each college's official site for exact cutoffs.",
        "financial_aid": f"Most top universities offer generous need-based aid. {colleges} often meets 100% of demonstrated need. Apply via FAFSA (US) or the college's own portal. Don't let sticker price stop you from applying!",
        "deadlines": f"Early Action/Decision deadlines are typically November 1-15, Regular Decision in January. Always verify on the official {colleges} admissions page and set reminders 2 weeks early.",
        "college_comparison": f"When comparing colleges, weigh: reputation for {programs}, financial aid, campus culture, location, and career outcomes. Happy to do a detailed comparison — just tell me which factors matter most!",
        "goodbye": "Best of luck with your applications! You've got this! Feel free to come back anytime. 🎓",
    }
    return responses.get(intent, f"Great question! Could you give me a bit more detail so I can give you the most accurate advice about {colleges}?")

class ResponseGenerator:
    async def generate(self, payload: Dict[str, Any]) -> str:
        if _USE_ANTHROPIC and os.getenv("ANTHROPIC_API_KEY"):
            return await self._call_claude(payload)
        return _fallback(payload)

    async def _call_claude(self, payload):
        prompt = _build_prompt(payload)
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: _CLIENT.messages.create(
                model="claude-sonnet-4-20250514", max_tokens=512,
                system=SYSTEM_PROMPT,
                messages=[{"role":"user","content":prompt}]
            ))
            return response.content[0].text
        except Exception as e:
            print(f"[ResponseGenerator] API error: {e} — using fallback.")
            return _fallback(payload)

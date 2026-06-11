import json
from datetime import datetime
import time
from google.adk.plugins import base_plugin
from google.genai import types

class AuditLogPlugin(base_plugin.BasePlugin):
    """
    Component: Audit Log
    What it does: Records every interaction (input, output, blocked status, latency).
    Why is it needed: Crucial for post-incident forensics, compliance reporting, and continuous improvement of safety rules.
    """
    def __init__(self):
        super().__init__(name="audit_log")
        self.logs = []
        self._start_times = {}

    def _extract_text(self, content) -> str:
        text = ""
        if hasattr(content, "parts") and content.parts:
            for part in content.parts:
                if hasattr(part, "text") and part.text:
                    text += part.text
        return text

    async def on_user_message_callback(self, *, invocation_context, user_message):
        # Record input + start time. Never block.
        user_id = invocation_context.user_id if invocation_context else "anonymous"
        self._start_times[user_id] = time.time()
        
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "event_type": "user_input",
            "user_id": user_id,
            "message": self._extract_text(user_message)
        })
        return None

    async def after_model_callback(self, *, callback_context, llm_response):
        # Record output + calculate latency. Never modify.
        user_id = "anonymous"
        if callback_context and hasattr(callback_context, "invocation_context") and callback_context.invocation_context:
            user_id = callback_context.invocation_context.user_id

        start_time = self._start_times.get(user_id, time.time())
        latency = time.time() - start_time
        
        response_text = ""
        if hasattr(llm_response, "content"):
            response_text = self._extract_text(llm_response.content)
        else:
            response_text = self._extract_text(llm_response)
            
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "event_type": "model_output",
            "user_id": user_id,
            "latency_seconds": round(latency, 3),
            "response": response_text
        })
        return llm_response

    def export_json(self, filepath="audit_log.json"):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2, default=str, ensure_ascii=False)

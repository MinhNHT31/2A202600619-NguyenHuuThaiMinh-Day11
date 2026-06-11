from collections import defaultdict, deque
import time
from google.adk.plugins import base_plugin
from google.genai import types
from google.adk.agents.invocation_context import InvocationContext

class RateLimitPlugin(base_plugin.BasePlugin):
    """
    Component: Rate Limiter
    What it does: Blocks users who send too many requests within a specific time window.
    Why is it needed: Protects the system against Denial-of-Service (DoS) attacks, brute-forcing
                      passwords or API keys, and prevents cost exhaustion from excessive LLM calls.
    """
    def __init__(self, max_requests=10, window_seconds=60):
        super().__init__(name="rate_limiter")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_windows = defaultdict(deque)

    async def on_user_message_callback(
        self,
        *,
        invocation_context: InvocationContext,
        user_message: types.Content,
    ) -> types.Content | None:
        user_id = invocation_context.user_id if invocation_context else "anonymous"
        now = time.time()
        window = self.user_windows[user_id]

        # Remove expired timestamps
        while window and now - window[0] > self.window_seconds:
            window.popleft()

        # Check if rate limit exceeded
        if len(window) >= self.max_requests:
            wait_time = int(self.window_seconds - (now - window[0]))
            block_message = f"Rate limit exceeded. Please wait {wait_time} seconds before trying again."
            return types.Content(
                role="model",
                parts=[types.Part.from_text(text=block_message)],
            )

        # Allow request and add timestamp
        window.append(now)
        return None

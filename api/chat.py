"""
Serverless endpoint that proxies chat requests to the Claude API.

Runs on Vercel's Python runtime. Streams the model's response back to the
browser using Server-Sent Events (SSE) so messages appear as they're written.

Authentication: every request must carry a Supabase access token in the
Authorization header (the frontend gets this from supabase.auth.getSession()).
We verify the token against SUPABASE_JWT_SECRET. Anything missing or invalid
returns 401 — that's what stops a stranger who finds the URL from spending
your API credits.

Required environment variables:
  ANTHROPIC_API_KEY     — get one at console.anthropic.com
  SUPABASE_JWT_SECRET   — Supabase project Settings → API → JWT Secret
"""

from http.server import BaseHTTPRequestHandler
import json
import os

import anthropic
import jwt

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 4096
THINKING_BUDGET = 4096


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        # ---- Auth gate ----
        user_id = self._verify_auth()
        if not user_id:
            return self._json_error(401, "Authentication required. Please sign in.")

        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length) or b"{}")
        except Exception as e:
            return self._json_error(400, f"Invalid JSON body: {e}")

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return self._json_error(
                500,
                "ANTHROPIC_API_KEY is not set. Add it in Vercel → Settings → "
                "Environment Variables, then redeploy.",
            )

        max_tokens = int(data.get("maxTokens") or DEFAULT_MAX_TOKENS)
        if data.get("thinking"):
            max_tokens = max(max_tokens, THINKING_BUDGET + 4096)

        kwargs = {
            "model": data.get("model") or DEFAULT_MODEL,
            "max_tokens": max_tokens,
            "messages": data.get("messages") or [],
        }
        system = data.get("system")
        if system:
            kwargs["system"] = [{
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }]
        if data.get("useWebSearch"):
            kwargs["tools"] = [{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5,
            }]
        if data.get("thinking"):
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": THINKING_BUDGET}

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self._cors()
        self.end_headers()

        try:
            client = anthropic.Anthropic(api_key=api_key)
            with client.messages.stream(**kwargs) as stream:
                for event in stream:
                    self._handle_event(event)
                final = stream.get_final_message()
                self._sse({
                    "type": "done",
                    "stop_reason": final.stop_reason,
                    "usage": {
                        "input_tokens": final.usage.input_tokens,
                        "output_tokens": final.usage.output_tokens,
                        "cache_creation_input_tokens": getattr(final.usage, "cache_creation_input_tokens", 0) or 0,
                        "cache_read_input_tokens": getattr(final.usage, "cache_read_input_tokens", 0) or 0,
                    },
                })
        except anthropic.APIStatusError as e:
            self._sse({"type": "error", "error": f"{e.status_code}: {e.message}"})
        except Exception as e:
            self._sse({"type": "error", "error": str(e)})

    # ---- Helpers ----

    def _verify_auth(self):
        """Verify the Supabase access token. Returns user_id or None."""
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth[len("Bearer "):].strip()
        if not token:
            return None
        secret = os.environ.get("SUPABASE_JWT_SECRET")
        if not secret:
            # Fail closed — if the secret isn't configured we can't verify
            # anything, so refuse to serve rather than allowing through.
            return None
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
            return payload.get("sub")
        except jwt.PyJWTError:
            return None

    def _handle_event(self, event):
        t = getattr(event, "type", None)
        if t == "content_block_start":
            block = event.content_block
            block_type = getattr(block, "type", None)
            if block_type == "server_tool_use":
                query = ""
                if isinstance(getattr(block, "input", None), dict):
                    query = block.input.get("query", "")
                self._sse({"type": "tool_use", "name": block.name, "query": query})
        elif t == "content_block_delta":
            delta = event.delta
            delta_type = getattr(delta, "type", None)
            if delta_type == "text_delta":
                self._sse({"type": "text", "text": delta.text})
            elif delta_type == "thinking_delta":
                self._sse({"type": "thinking", "text": delta.thinking})

    def _sse(self, payload):
        try:
            self.wfile.write(f"data: {json.dumps(payload)}\n\n".encode())
            self.wfile.flush()
        except Exception:
            pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _json_error(self, code, message):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())

"""One request in a killable subprocess; credential only enters via stdin."""
from __future__ import annotations

import json
import sys
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener


ENDPOINTS = {
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "deepseek": "https://api.deepseek.com/chat/completions",
}
QWEN_ENDPOINTS = {
    "beijing": ENDPOINTS["qwen"],
    "singapore": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
}


def endpoint_for(provider: str, region: str) -> str:
    return QWEN_ENDPOINTS[region] if provider == "qwen" else ENDPOINTS[provider]


def read_request(stream) -> dict:
    # Parent writes UTF-8 regardless of the Windows console's legacy encoding.
    return json.loads(stream.read(100000).decode("utf-8"))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main() -> None:
    try:
        incoming = read_request(sys.stdin.buffer)
        endpoint = endpoint_for(incoming["provider"], incoming.get("region", ""))
        request = Request(endpoint, data=json.dumps(incoming["payload"], ensure_ascii=False).encode("utf-8"), headers={"Authorization": "Bearer " + incoming["credential"], "Content-Type": "application/json"}, method="POST")
        with build_opener(NoRedirect()).open(request, timeout=4) as response:
            body = response.read(131073)
        if len(body) > 131072:
            raise ValueError("oversized response")
        parsed = json.loads(body)
        # Do not return HTTP metadata, raw errors or hidden reasoning to caller.
        choices = parsed.get("choices", [])
        choice = choices[0] if choices else {}
        print(json.dumps({"usage": parsed.get("usage"), "finish_reason": choice.get("finish_reason"), "content": choice.get("message", {}).get("content")}))
    except HTTPError as error:
        # Status only; do not expose the response body, URL, headers or key.
        print(json.dumps({"error": "http_error", "http_status": error.code}))
    except Exception:
        # Provider errors can contain sensitive request details; never log them.
        print('{"error":"transport_failed"}')


if __name__ == "__main__":
    main()

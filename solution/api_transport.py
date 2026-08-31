"""One request in a killable subprocess; credential only enters via stdin."""
from __future__ import annotations

import json
import sys
from urllib.request import HTTPRedirectHandler, Request, build_opener


ENDPOINTS = {
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "deepseek": "https://api.deepseek.com/chat/completions",
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main() -> None:
    try:
        incoming = json.loads(sys.stdin.read(100000))
        endpoint = ENDPOINTS[incoming["provider"]]
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
    except Exception:
        # Provider errors can contain sensitive request details; never log them.
        print('{"error":"transport_failed"}')


if __name__ == "__main__":
    main()

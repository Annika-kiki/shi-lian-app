import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from recipe_engine import generate_recipe
from nutrition import FOODS
from training_engine import EXERCISES, list_exercises, generate_plan

ROOT = Path(__file__).parent


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, payload, content_type="application/json; charset=utf-8"):
        body = payload if isinstance(payload, bytes) else json.dumps(
            payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._send(200, (ROOT / "static" / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path.startswith("/assets/"):
            relative = self.path.removeprefix("/assets/")
            asset_root = (ROOT / "static" / "assets").resolve()
            asset = (asset_root / relative).resolve()
            if asset_root not in asset.parents or not asset.is_file():
                return self._send(404, {"error": "not_found"})
            self._send(200, asset.read_bytes(), mimetypes.guess_type(asset.name)[0] or "application/octet-stream")
        elif self.path == "/api/health":
            self._send(200, {"ok": True, "foods": len(FOODS), "mode": "offline-demo"})
        elif self.path == "/api/foods":
            self._send(200, {"foods": sorted(FOODS)})
        elif self.path.startswith("/api/exercises"):
            self._send(200, {"exercises": list_exercises()})
        else:
            self._send(404, {"error": "not_found"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 100_000:
                raise ValueError("请求内容为空或过大")
            data = json.loads(self.rfile.read(length))
            if self.path == "/api/recipes/generate":
                result = generate_recipe(
                    data.get("ingredients"), data.get("target_kcal", 500), data.get("preferences", []))
            elif self.path == "/api/training/plan":
                result = generate_plan(data.get("goal", "减脂"), data.get("level", "新手"),
                                       data.get("days", 3), data.get("equipment"))
            else:
                return self._send(404, {"error": "not_found"})
            self._send(200, result)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._send(400, {"error": "invalid_request", "message": str(exc)})

    def log_message(self, fmt, *args):
        print(f"[server] {self.address_string()} - {fmt % args}")


if __name__ == "__main__":
    address = ("127.0.0.1", 8000)
    print(f"食练周期演示已启动：http://{address[0]}:{address[1]}")
    ThreadingHTTPServer(address, Handler).serve_forever()

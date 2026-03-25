import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from ratechecker import get_mastercard_rate, get_market_rate, TARGET_PAIRS
import requests

HOST = "0.0.0.0"
PORT = 8000

SUPPORTED_CURRENCIES = sorted({b for b, _ in TARGET_PAIRS} | {t for _, t in TARGET_PAIRS})
SUPPORTED_PAIRS = {f"{b}/{t}" for b, t in TARGET_PAIRS}


class SimpleAPIHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/compare-custom":
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found."}).encode("utf-8"))
            return

        content_length = int(self.headers.get("Content-Length", 0))
        try:
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)
        except Exception:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON."}).encode("utf-8"))
            return

        base = data.get("base")
        quote = data.get("quote")

        if not base or not quote:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Missing base or quote currency."}).encode("utf-8"))
            return

        base = str(base).upper().strip()
        quote = str(quote).upper().strip()

        if base == quote:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Please select two different currencies."}).encode("utf-8"))
            return

        if base not in SUPPORTED_CURRENCIES or quote not in SUPPORTED_CURRENCIES:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "This currency pair is not supported."}).encode("utf-8"))
            return

        pair_str = f"{base}/{quote}"
        if pair_str not in SUPPORTED_PAIRS:
            # Mastercard API may not accept all combinations but we confirm against known
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "This currency pair is not supported."}).encode("utf-8"))
            return

        try:
            session = requests.Session()
            mc_rate = get_mastercard_rate(session, base, quote)
            market_rate = get_market_rate(base, quote)
        except Exception as e:
            self._set_headers(502)
            self.wfile.write(json.dumps({"error": "Rate unavailable for this pair."}).encode("utf-8"))
            return

        diff = mc_rate - market_rate
        better_rate = diff < 0
        message = "Mastercard rate is lower than the market rate." if better_rate else "Mastercard rate is higher than the market rate."

        response = {
            "pair": pair_str,
            "mastercard_rate": round(mc_rate, 6),
            "market_rate": round(market_rate, 6),
            "diff": round(diff, 6),
            "better_rate": better_rate,
            "message": message,
        }

        self._set_headers(200)
        self.wfile.write(json.dumps(response).encode("utf-8"))


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), SimpleAPIHandler)
    print(f"API server running at http://{HOST}:{PORT}")
    print("POST /api/compare-custom with JSON {\"base\": ... , \"quote\": ...}")
    server.serve_forever()
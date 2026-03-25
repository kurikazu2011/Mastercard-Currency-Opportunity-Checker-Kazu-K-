import json
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from ratechecker import get_mastercard_rate, get_market_rate, TARGET_PAIRS
import requests

HOST = "0.0.0.0"
PORT = 9000

SUPPORTED_CURRENCIES = [
    {"code": "AFN", "name": "Afghanistan Afghani"},
    {"code": "ALL", "name": "Albanian Lek"},
    {"code": "DZD", "name": "Algerian Dinar"},
    {"code": "AOA", "name": "Angolan Kwanza"},
    {"code": "ARS", "name": "Argentine Peso"},
    {"code": "AMD", "name": "Armenian Dram"},
    {"code": "AWG", "name": "Aruban Guilder"},
    {"code": "AUD", "name": "Australian Dollar"},
    {"code": "AZN", "name": "Azerbaijan Manat"},
    {"code": "BSD", "name": "Bahamian Dollar"},
    {"code": "BHD", "name": "Bahrain Dinar"},
    {"code": "BDT", "name": "Bangladesh Taka"},
    {"code": "BBD", "name": "Barbados Dollar"},
    {"code": "BYN", "name": "Belarussian Ruble"},
    {"code": "BZD", "name": "Belize Dollar"},
    {"code": "BMD", "name": "Bermudan Dollar"},
    {"code": "BTN", "name": "Bhutanese Ngultrum"},
    {"code": "BOB", "name": "Bolivian Boliviano"},
    {"code": "BAM", "name": "Bosnian Convertible Mark"},
    {"code": "BWP", "name": "Botswana Pula"},
    {"code": "BRL", "name": "Brazilian Real"},
    {"code": "BND", "name": "Brunei Dollar"},
    {"code": "BGN", "name": "Bulgarian Lev"},
    {"code": "BIF", "name": "Burundi Franc"},
    {"code": "KHR", "name": "Cambodian Riel"},
    {"code": "CAD", "name": "Canadian Dollar"},
    {"code": "CVE", "name": "Cape Verde Escudo"},
    {"code": "XCG", "name": "Caribbean Guilder"},
    {"code": "KYD", "name": "Cayman Island Dollar"},
    {"code": "XOF", "name": "CFA Franc BCEAO"},
    {"code": "XAF", "name": "CFA Franc BEAC"},
    {"code": "XPF", "name": "CFP Franc"},
    {"code": "CLP", "name": "Chilean Peso"},
    {"code": "CNY", "name": "China Yuan Renminbi"},
    {"code": "COP", "name": "Colombian Peso"},
    {"code": "KMF", "name": "Comoros Franc"},
    {"code": "CDF", "name": "Congolese Franc"},
    {"code": "CRC", "name": "Costa Rica Colon"},
    {"code": "CUP", "name": "Cuban Peso"},
    {"code": "CZK", "name": "Czech Koruna"},
    {"code": "DKK", "name": "Danish Krone"},
    {"code": "DJF", "name": "Djibouti Franc"},
    {"code": "DOP", "name": "Dominican Peso"},
    {"code": "XCD", "name": "East Caribbean Dollar"},
    {"code": "EGP", "name": "Egyptian Pound"},
    {"code": "SVC", "name": "El Salvador Colon"},
    {"code": "ETB", "name": "Ethiopia Birr"},
    {"code": "EUR", "name": "Euro"},
    {"code": "FKP", "name": "Falkland Island Pound"},
    {"code": "FJD", "name": "Fiji Dollar"},
    {"code": "GMD", "name": "Gambia Dalasi"},
    {"code": "GEL", "name": "Georgian Lari"},
    {"code": "GHS", "name": "Ghanaian Cedi"},
    {"code": "GIP", "name": "Gibraltar Pound"},
    {"code": "GBP", "name": "Great British Pound"},
    {"code": "GTQ", "name": "Guatemala Quetzal"},
    {"code": "GNF", "name": "Guinea Franc"},
    {"code": "GYD", "name": "Guyana Dollar"},
    {"code": "HTG", "name": "Haiti Gourde"},
    {"code": "HNL", "name": "Honduras Lempira"},
    {"code": "HKD", "name": "Hong Kong Dollar"},
    {"code": "HUF", "name": "Hungarian Forint"},
    {"code": "ISK", "name": "Icelandic Krona"},
    {"code": "INR", "name": "Indian Rupee"},
    {"code": "IDR", "name": "Indonesian Rupiah"},
    {"code": "IQD", "name": "Iraq Dinar"},
    {"code": "ILS", "name": "Israeli Sheqel"},
    {"code": "JMD", "name": "Jamaican Dollar"},
    {"code": "JPY", "name": "Japanese Yen"},
    {"code": "JOD", "name": "Jordan Dinar"},
    {"code": "KZT", "name": "Kazakhstan Tenge"},
    {"code": "KES", "name": "Kenyan Shilling"},
    {"code": "KWD", "name": "Kuwaiti Dinar"},
    {"code": "KGS", "name": "Kyrgyzstan Som"},
    {"code": "LAK", "name": "Laotian Kip"},
    {"code": "LBP", "name": "Lebanese Pound"},
    {"code": "LSL", "name": "Lesotho Loti"},
    {"code": "LRD", "name": "Liberian Dollar"},
    {"code": "LYD", "name": "Libya Dinar"},
    {"code": "MOP", "name": "Macau Pataca"},
    {"code": "MKD", "name": "Macedonia Denar"},
    {"code": "MGA", "name": "Malagasy Ariary"},
    {"code": "MWK", "name": "Malawi Kwacha"},
    {"code": "MYR", "name": "Malaysian Ringgit"},
    {"code": "MVR", "name": "Maldive Rufiyaa"},
    {"code": "MRU", "name": "Mauritania Ouguiya New"},
    {"code": "MUR", "name": "Mauritian Rupee"},
    {"code": "MXN", "name": "Mexican Peso"},
    {"code": "MDL", "name": "Moldova Leu"},
    {"code": "MNT", "name": "Mongolia Tugrik"},
    {"code": "MAD", "name": "Moroccan Dirham"},
    {"code": "MZN", "name": "Mozambique Metical"},
    {"code": "MMK", "name": "Myanmar Kyat"},
    {"code": "NAD", "name": "Namibia Dollar"},
    {"code": "NPR", "name": "Nepalese Rupee"},
    {"code": "NZD", "name": "New Zealand Dollar"},
    {"code": "NIO", "name": "Nicaragua Cordoba Oro"},
    {"code": "NGN", "name": "Nigerian Naira"},
    {"code": "NOK", "name": "Norwegian Krone"},
    {"code": "OMR", "name": "Oman Rial"},
    {"code": "PKR", "name": "Pakistani Rupee"},
    {"code": "PAB", "name": "Panama Balboa"},
    {"code": "PGK", "name": "Papua New Guinea Kina"},
    {"code": "PYG", "name": "Paraguay Guarani"},
    {"code": "PEN", "name": "Peru Nuevo Sol"},
    {"code": "PHP", "name": "Philippine Peso"},
    {"code": "PLN", "name": "Polish Zloty"},
    {"code": "QAR", "name": "Qatar Rial"},
    {"code": "RON", "name": "Romanian Leu"},
    {"code": "RUB", "name": "Russian Ruble"},
    {"code": "RWF", "name": "Rwanda Franc"},
    {"code": "SHP", "name": "Saint Helena Pound"},
    {"code": "WST", "name": "Samoa Tala"},
    {"code": "STN", "name": "Sao Tome and Principe Dobra New"},
    {"code": "SAR", "name": "Saudi Arabia Riyal"},
    {"code": "RSD", "name": "Serbian Dinar"},
    {"code": "SCR", "name": "Seychelles Rupee"},
    {"code": "SLE", "name": "Sierra Leone SLE"},
    {"code": "SGD", "name": "Singapore Dollar"},
    {"code": "SBD", "name": "Solomon Island Dollar"},
    {"code": "SOS", "name": "Somali Shilling"},
    {"code": "ZAR", "name": "South African Rand"},
    {"code": "KRW", "name": "South Korean Won"},
    {"code": "SSP", "name": "South Sudan Pound"},
    {"code": "LKR", "name": "Sri Lankan Rupee"},
    {"code": "SDG", "name": "Sudanese Pound"},
    {"code": "SRD", "name": "Suriname Dollar"},
    {"code": "SZL", "name": "Swaziland Lilangeni"},
    {"code": "SEK", "name": "Swedish Krona"},
    {"code": "CHF", "name": "Swiss Franc"},
    {"code": "TWD", "name": "Taiwan Dollar"},
    {"code": "TJS", "name": "Tajikistan Somoni"},
    {"code": "TZS", "name": "Tanzanian Shilling"},
    {"code": "THB", "name": "Thai Baht"},
    {"code": "TOP", "name": "Tonga Paanga"},
    {"code": "TTD", "name": "Trinidad and Tobago Dollar"},
    {"code": "TND", "name": "Tunisian Dinar"},
    {"code": "TRY", "name": "Turkish Lira"},
    {"code": "TMT", "name": "Turkmenistan Manat"},
    {"code": "UGX", "name": "Uganda Shilling"},
    {"code": "UAH", "name": "Ukrainian Hryvnia"},
    {"code": "AED", "name": "United Arab Emirates Dirham"},
    {"code": "USD", "name": "United States Dollar"},
    {"code": "UYU", "name": "Uruguay Peso"},
    {"code": "UZS", "name": "Uzbekistan Sum"},
    {"code": "VUV", "name": "Vanuatu Vatu"},
    {"code": "VES", "name": "Venezuelan Bolivar Soberano"},
    {"code": "VND", "name": "Vietnam Dong"},
    {"code": "YER", "name": "Yemen Rial"},
    {"code": "ZMW", "name": "Zambia Kwacha"},
    {"code": "ZWG", "name": "Zimbabwe Gold"}
]
SUPPORTED_CURRENCY_CODES = {item['code'] for item in SUPPORTED_CURRENCIES}
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

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/supported-currencies":
            self._set_headers(200)
            self.wfile.write(json.dumps({"currencies": SUPPORTED_CURRENCIES}).encode("utf-8"))
            return
        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Endpoint not found."}).encode("utf-8"))

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

        print(f"[compare-custom] Received: base={base}, quote={quote}")

        if base == quote:
            print(f"[compare-custom] ERROR: Same currency selected")
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Please select two different currencies."}).encode("utf-8"))
            return

        if base not in SUPPORTED_CURRENCY_CODES or quote not in SUPPORTED_CURRENCY_CODES:
            print(f"[compare-custom] ERROR: Unsupported currency - base_valid={base in SUPPORTED_CURRENCY_CODES}, quote_valid={quote in SUPPORTED_CURRENCY_CODES}")
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "This currency is not supported."}).encode("utf-8"))
            return

        pair_str = f"{base}/{quote}"
        if pair_str not in SUPPORTED_PAIRS:
            print(f"[compare-custom] WARNING: Pair not in precomputed list, will attempt anyway. pair={pair_str}")

        mc_rate = None
        market_rate = None
        mc_error = None
        yahoo_error = None

        try:
            print(f"[compare-custom] Fetching Mastercard rate...")
            session = requests.Session()
            mc_rate = get_mastercard_rate(session, base, quote)
            print(f"[compare-custom] Mastercard rate retrieved: {mc_rate}")
        except Exception as e:
            mc_error = str(e)
            print(f"[compare-custom] ERROR fetching Mastercard: {mc_error}")
            traceback.print_exc()

        try:
            print(f"[compare-custom] Fetching Yahoo market rate...")
            market_rate = get_market_rate(base, quote)
            print(f"[compare-custom] Market rate retrieved: {market_rate}")
        except Exception as e:
            yahoo_error = str(e)
            print(f"[compare-custom] ERROR fetching Yahoo: {yahoo_error}")
            traceback.print_exc()

        if mc_error and yahoo_error:
            print(f"[compare-custom] FAILED: Both Mastercard and Yahoo")
            self._set_headers(502)
            self.wfile.write(json.dumps({"error": "Failed to fetch both Mastercard and market rates."}).encode("utf-8"))
            return
        elif mc_error:
            print(f"[compare-custom] FAILED: Mastercard only")
            self._set_headers(502)
            self.wfile.write(json.dumps({"error": "Failed to fetch Mastercard rate."}).encode("utf-8"))
            return
        elif yahoo_error:
            print(f"[compare-custom] FAILED: Yahoo only")
            self._set_headers(502)
            self.wfile.write(json.dumps({"error": "Failed to fetch market rate."}).encode("utf-8"))
            return

        diff = mc_rate - market_rate
        better_rate = diff < 0
        message = "Mastercard rate is lower than the market rate." if better_rate else "Mastercard rate is higher than the market rate."

        print(f"[compare-custom] SUCCESS: pair={pair_str}, diff={diff:.6f}, better_rate={better_rate}")

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
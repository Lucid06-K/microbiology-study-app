#!/usr/bin/env python3
"""
Microbiology Study App - Local TTS Server
Run this script, then open http://localhost:8742 in your browser.
Uses your Mac's built-in voices for natural text-to-speech.
"""

import http.server
import subprocess
import json
import os
import tempfile
import urllib.parse
import webbrowser
import threading
import re

PORT = 8742
HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MicrobiologyStudy.html")

def get_mac_voices():
    """Get list of available English Mac voices."""
    result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
    voices = []
    for line in result.stdout.strip().split("\n"):
        match = re.match(r"^(.+?)\s+(en_\w+)\s+#", line)
        if match:
            name = match.group(1).strip()
            lang = match.group(2).strip()
            # Skip novelty voices
            skip = {"Albert", "Bad News", "Bahh", "Bells", "Boing", "Bubbles",
                    "Cellos", "Good News", "Jester", "Junior", "Organ",
                    "Superstar", "Trinoids", "Whisper", "Zarvox", "Wobble"}
            if name in skip:
                continue
            quality = "premium" if "Premium" in name else "enhanced" if "Enhanced" in name else "standard"
            voices.append({"name": name, "lang": lang, "quality": quality})
    # Sort: premium first, then enhanced, then standard
    order = {"premium": 0, "enhanced": 1, "standard": 2}
    voices.sort(key=lambda v: (order.get(v["quality"], 3), v["name"]))
    return voices


ALLOWED_ORIGINS = {"http://localhost:8742", "http://127.0.0.1:8742"}

# Cache known voice names at startup
_known_voices = None
def get_known_voice_names():
    global _known_voices
    if _known_voices is None:
        _known_voices = {v["name"] for v in get_mac_voices()}
    return _known_voices


class TTSHandler(http.server.SimpleHTTPRequestHandler):
    def _cors_header(self):
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
        else:
            self.send_header("Access-Control-Allow-Origin", "http://localhost:8742")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/index.html":
            # Serve the HTML file
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._cors_header()
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            with open(HTML_FILE, "rb") as f:
                self.wfile.write(f.read())

        elif parsed.path == "/api/voices":
            # Return available voices
            voices = get_mac_voices()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors_header()
            self.end_headers()
            self.wfile.write(json.dumps(voices).encode())

        elif parsed.path == "/api/speak":
            # Generate speech audio
            params = urllib.parse.parse_qs(parsed.query)
            text = params.get("text", [""])[0]
            voice = params.get("voice", ["Samantha"])[0]
            rate = params.get("rate", ["175"])[0]  # words per minute

            if not text:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing text parameter")
                return

            # Validate voice against known voices
            known = get_known_voice_names()
            if known and voice not in known:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid voice parameter")
                return

            # Validate rate is a number between 50 and 400
            try:
                rate_int = int(rate)
                if rate_int < 50 or rate_int > 400:
                    raise ValueError
                rate = str(rate_int)
            except (ValueError, TypeError):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid rate parameter (must be 50-400)")
                return

            # Limit text length for safety
            text = text[:5000]

            # Sanitize text: remove shell-special characters (extra safety layer)
            text = re.sub(r'[`$\\]', '', text)

            try:
                with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp:
                    tmp_path = tmp.name

                # Use macOS say command to generate audio
                cmd = ["say", "-v", voice, "-r", str(rate), "-o", tmp_path, "--", text]
                subprocess.run(cmd, check=True, timeout=30)

                # Convert to WAV using afconvert (built into macOS)
                wav_path = tmp_path.replace(".aiff", ".wav")
                subprocess.run(
                    ["afconvert", "-f", "WAVE", "-d", "LEI16@22050", tmp_path, wav_path],
                    check=True, timeout=10
                )

                # Send the WAV file
                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self._cors_header()
                self.send_header("Cache-Control", "no-cache")
                with open(wav_path, "rb") as f:
                    data = f.read()
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

                # Cleanup
                os.unlink(tmp_path)
                os.unlink(wav_path)

            except subprocess.TimeoutExpired:
                self.send_response(504)
                self.end_headers()
                self.wfile.write(b"TTS generation timed out")
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Quieter logging
        if "/api/speak" in str(args):
            print(f"  Speaking: {args[0][:80]}...")
        elif "/api/voices" not in str(args) and "favicon" not in str(args):
            print(f"  {args[0]}")


def main():
    if not os.path.exists(HTML_FILE):
        print(f"ERROR: Cannot find {HTML_FILE}")
        print(f"Make sure MicrobiologyStudy.html is in the same folder as this script.")
        return

    server = http.server.HTTPServer(("127.0.0.1", PORT), TTSHandler)
    print(f"\n  Microbiology Study App")
    print(f"  ─────────────────────────────────")
    print(f"  Server running at: http://localhost:{PORT}")
    print(f"  Using Mac voices for text-to-speech")
    print(f"  Press Ctrl+C to stop\n")

    # Open browser after a short delay
    threading.Timer(0.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.server_close()


if __name__ == "__main__":
    main()

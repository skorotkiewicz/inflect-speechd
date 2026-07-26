"""Usage:

curl -X POST http://127.0.0.1:8000/speak \
  -H 'Content-Type: application/json' \
  -d '{"text":"Hello from the voice server"}'

"""

import io
import json
import subprocess
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer

import soundfile as sf

MAX_TEXT_LENGTH = 1000
tts = None


class SpeakHandler(BaseHTTPRequestHandler):
    def respond(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def respond_audio(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path not in ("/speak", "/synthesize"):
            self.respond(404, {"error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError
            payload = json.loads(self.rfile.read(length))
            text = payload.get("text", "")
            speed = payload.get("speed", 1.0)
            variation = payload.get("variation", 0.667)
            seed = payload.get("seed", 0)
            if not isinstance(text, str) or not text.strip():
                raise ValueError
            if len(text) > MAX_TEXT_LENGTH:
                self.respond(413, {"error": "Text exceeds 1000 characters"})
                return
        except (ValueError, json.JSONDecodeError, AttributeError):
            self.respond(400, {"error": "Send JSON containing non-empty text"})
            return

        if isinstance(speed, bool) or not isinstance(speed, (int, float)) or not 0.5 <= speed <= 2.0:
            self.respond(400, {"error": "speed must be between 0.5 and 2.0"})
            return
        if isinstance(variation, bool) or not isinstance(variation, (int, float)) or not 0.0 <= variation <= 1.0:
            self.respond(400, {"error": "variation must be between 0.0 and 1.0"})
            return
        if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 2**63 - 1:
            self.respond(400, {"error": "seed must be a non-negative integer"})
            return

        # Speech Dispatcher shell-escapes apostrophes before substitution.
        text = text.replace("'\\''", "'").rstrip()
        if text[-1] not in ".!?;:":
            text += "."

        try:
            sample_rate, waveform = tts.synthesize(
                text, speed=speed, variation=variation, seed=seed
            )
            if self.path == "/synthesize":
                with io.BytesIO() as audio:
                    sf.write(audio, waveform, sample_rate, format="WAV")
                    self.respond_audio(audio.getvalue())
                return
            with tempfile.NamedTemporaryFile(suffix=".wav") as audio:
                sf.write(audio.name, waveform, sample_rate)
                subprocess.run(["aplay", "-q", audio.name], check=True)
        except Exception as error:
            print(f"Speech failed: {error}", file=sys.stderr)
            self.respond(500, {"error": "Speech synthesis failed"})
            return

        self.respond(200, {"status": "played"})


def main():
    global tts

    from huggingface_hub import snapshot_download

    model_dir = snapshot_download("owensong/Inflect-Nano-v2")
    sys.path[:0] = [f"{model_dir}/runtime", model_dir]
    from inference import InflectTTS

    tts = InflectTTS(model_dir, device="cpu")
    server = HTTPServer(("127.0.0.1", 8000), SpeakHandler)
    print("Listening on http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

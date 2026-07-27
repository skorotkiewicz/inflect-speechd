# Inflect TTS

A local text-to-speech server built around [Inflect Nano v2](https://huggingface.co/owensong/Inflect-Nano-v2). The model stays loaded between requests, while Speech Dispatcher connects it to Firefox and other desktop applications.

- Local CPU inference
- HTTP API for playback or WAV output
- Adjustable speed, variation, and seed
- Speech Dispatcher rate and volume control

## Run

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python server.py
```

The first run downloads the model from Hugging Face. The server listens on `127.0.0.1:8000`.

## API

Play through the server:

```bash
curl -X POST http://127.0.0.1:8000/speak \
  -H 'Content-Type: application/json' \
  -d '{"text":"Hello from Inflect."}'
```

Return a WAV file:

```bash
curl -fsS -X POST http://127.0.0.1:8000/synthesize \
  -H 'Content-Type: application/json' \
  -d '{"text":"Hello from Inflect.","speed":1.2,"variation":0.667,"seed":0}' \
  -o speech.wav
```

| Option | Default | Range |
|---|---:|---:|
| `speed` | `1.0` | `0.5..2.0` |
| `variation` | `0.667` | `0.0..1.0` |
| `seed` | `0` | non-negative integer |

## Run as a user service

The included unit keeps the model loaded in the background. Update its paths if the project is moved.

```bash
cp inflect-tts.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now inflect-tts.service
```

```bash
systemctl --user status inflect-tts.service
journalctl --user -u inflect-tts.service -f
```

## Speech Dispatcher

See [speech-dispatcher.md](speech-dispatcher.md) for the module and wrapper configuration.

```bash
spd-say -w -o inflect -r 40 -i 75 "Hello from Speech Dispatcher."
```

`-r` controls Inflect speed and `-i` controls mpv playback volume. Both use Speech Dispatcher's `-100..100` scale.

## Development

Managed with [uv](https://docs.astral.sh/uv/); linting/formatting with [ruff](https://docs.astral.sh/ruff/); type checking with [ty](https://github.com/astral-sh/ty). 

```bash
uv run ruff check .   # lint
uv run ruff format .  # format
uv run ty check       # type check
uv run pytest -q      # tests
```

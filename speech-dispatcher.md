# Inflect with Speech Dispatcher

Inflect runs as a persistent local service. The model loads once when the service starts and remains in memory between requests.

## Request flow

```text
spd-say
  -> Speech Dispatcher sd_generic module
  -> inflect-tts-wrapper.sh
  -> POST http://127.0.0.1:8000/synthesize
  -> WAV response
  -> aplay
```

Speech Dispatcher controls the `aplay` process. The server handles synthesis and does not reload the model for each utterance.

## Inflect systemd service

The user service is stored at:

```text
~/.config/systemd/user/inflect-tts.service
```

```ini
[Unit]
Description=Inflect TTS server
After=pipewire.service

[Service]
Type=simple
WorkingDirectory=/home/mod/Dev/Python/Voice
ExecStart=/home/mod/Dev/Python/Voice/.venv/bin/python server.py
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
```

Manage the service with:

```bash
systemctl --user daemon-reload
systemctl --user enable --now inflect-tts.service
systemctl --user restart inflect-tts.service
systemctl --user status inflect-tts.service
journalctl --user -u inflect-tts.service -f
```

## Server endpoint

`server.py` accepts two local endpoints:

- `POST /speak` synthesizes and plays audio on the server.
- `POST /synthesize` returns a WAV response without playing it.

Both accept JSON. `speed`, `variation`, and `seed` are optional:

```json
{
  "text": "Hello from Inflect.",
  "speed": 1.15,
  "variation": 0.5,
  "seed": 42
}
```

The defaults are `1.0` for speed, `0.667` for variation, and `0` for seed. Speed must be between `0.5` and `2.0`; variation must be between `0.0` and `1.0`; seed must be a non-negative integer.

The server appends a period when text has no terminal punctuation. Inflect needs terminal punctuation to finish the last word cleanly.

Example WAV request:

```bash
curl -fsS -X POST http://127.0.0.1:8000/synthesize \
  -H 'Content-Type: application/json' \
  -d '{"text":"Hello from Inflect."}' \
  -o /tmp/inflect.wav

aplay -q /tmp/inflect.wav
```

## Speech Dispatcher wrapper

The wrapper is stored at:

```text
~/.config/speech-dispatcher/modules/inflect-tts-wrapper.sh
```

```bash
#!/usr/bin/env bash
set -o pipefail

RATE="${1:-0}"
VARIATION="${2:-0.667}"
SEED="${3:-0}"
VOLUME="${4:-100}"

python3 -c '
import json
import sys

rate = max(-100.0, min(100.0, float(sys.argv[1])))
speed = 1.0 + (rate / 100.0 if rate >= 0 else rate / 200.0)
json.dump(
    {
        "text": sys.stdin.read(),
        "speed": speed,
        "variation": float(sys.argv[2]),
        "seed": int(sys.argv[3]),
    },
    sys.stdout,
)
' "$RATE" "$VARIATION" "$SEED" \
    | curl -fsS \
        -H 'Content-Type: application/json' \
        --data-binary @- \
        http://127.0.0.1:8000/synthesize \
    | aplay -q
    # | mpv --no-terminal --really-quiet --no-video --volume="$VOLUME" -
```

The wrapper converts stdin to JSON, maps Speech Dispatcher rate `-100..100` to Inflect speed `0.5..2.0`, forwards variation and seed, requests WAV data from the persistent server, and sends the response to `aplay`. Its positional defaults are `0`, `0.667`, and `0`.

## Generic output module

The module configuration is stored at:

```text
~/.config/speech-dispatcher/modules/inflect-tts-generic.conf
```

```conf
GenericExecuteSynth "echo \"$DATA\" | /home/mod/.config/speech-dispatcher/modules/inflect-tts-wrapper.sh $RATE 0.667 0 $VOLUME"
GenericCmdDependency "curl"

GenericLanguage "en" "en" "UTF-8"
AddVoice "en" "male1" "inflect"
DefaultVoice "inflect"
GenericCharset "UTF-8"
```

The wrapper must be executable:

```bash
chmod 755 ~/.config/speech-dispatcher/modules/inflect-tts-wrapper.sh
```

## Speech Dispatcher registration

This line was added to `~/.config/speech-dispatcher/speechd.conf`:

```conf
AddModule "inflect" "sd_generic" "inflect-tts-generic.conf"
```

Piper remains the default:

```conf
DefaultModule piper-tts-generic
```

Restart Speech Dispatcher after configuration changes:

```bash
systemctl --user restart speech-dispatcher.service
```

## Usage

Select Inflect explicitly:

```bash
spd-say -w -o inflect "Hello from Inflect."
```

Use Speech Dispatcher's maximum rate, which maps to Inflect speed `2.0`:

```bash
spd-say -w -o inflect -r 100 "Inflect at maximum speed."
```

To make Inflect the default, change the existing `DefaultModule` line in `speechd.conf`:

```conf
DefaultModule inflect
```

Then restart Speech Dispatcher.

## Checks

Confirm both services are running:

```bash
systemctl --user is-active inflect-tts.service
systemctl --user is-active speech-dispatcher.service
```

Confirm Speech Dispatcher loaded the module:

```bash
ps -ef | grep '[s]d_generic.*inflect-tts-generic.conf'
```

Test the complete path:

```bash
spd-say -w -o inflect "Speech Dispatcher is using Inflect."
```

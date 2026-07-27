import sys

import soundfile as sf
from huggingface_hub import snapshot_download

model_dir = snapshot_download("owensong/Inflect-Micro-v2")
sys.path[:0] = [f"{model_dir}/runtime", model_dir]

from inference import InflectTTS  # noqa: E402  # ty: ignore[unresolved-import]

tts = InflectTTS(model_dir, device="cpu")
sample_rate, waveform = tts.synthesize("The complete model runs locally.")

sf.write("speech-micro.wav", waveform, sample_rate)

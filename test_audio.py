from TTS.api import TTS
import soundfile as sf
import numpy as np

# -------------------------
# Load multi-speaker VCTK model
# -------------------------
tts = TTS(model_name="tts_models/en/vctk/vits", progress_bar=True, gpu=False)

# -------------------------
# Predefined male speakers
# -------------------------
male_speakers = [
    "p225", "p226", "p227", "p228", "p229",
    "p230", "p231", "p232", "p233", "p234"
]
speaker = male_speakers[9]  # pick the first male

# -------------------------
# Sample text
# -------------------------
text = "Hello! This is a test of the multi-speaker Coqui TTS model. You should hear a male voice."

# -------------------------
# Generate audio
# -------------------------
wav = tts.tts(text=text, speaker=speaker)

# Optional: add 0.5s silence at the end
sr = tts.synthesizer.output_sample_rate
wav = np.concatenate([wav, np.zeros(int(sr*0.5))])

# -------------------------
# Save to WAV
# -------------------------
sf.write("test_male.wav", wav, sr)
print("✅ Saved test_male.wav with speaker:", speaker)

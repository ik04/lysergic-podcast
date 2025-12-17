import requests
from dotenv import load_dotenv
from TTS.api import TTS
import soundfile as sf
import numpy as np
import re
import logging
import string
import sys
from urllib.parse import unquote
import librosa

# -------------------------
# Logging setup
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()

# -------------------------
# Helpers
# -------------------------
def slow_audio(wav, rate=0.9):
    wav = np.asarray(wav, dtype=np.float32)
    return librosa.effects.time_stretch(wav, rate=rate)

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def silence(seconds: float, sr: int):
    return np.zeros(int(seconds * sr), dtype=np.float32)

def sanitize_filename(name: str) -> str:
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return "".join(c for c in name if c in valid_chars).replace(" ", "_")

# -------------------------
# Split text keeping punctuation
# -------------------------
def split_with_punctuation(text: str):
    """
    Returns list of (text, pause_seconds)
    """
    parts = re.findall(r'[^.,!?;:]+[.,!?;:]?', text)
    result = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        last_char = part[-1]
        if last_char in ".!?":
            pause = 1.0
        elif last_char in ",;:":
            pause = 0.3
        else:
            pause = 0.3

        result.append((part, pause))

    return result

# -------------------------
# Check for URL argument
# -------------------------
experience_url = None
if len(sys.argv) > 1:
    experience_url = unquote(sys.argv[1])
    logger.info("Using provided experience URL: %s", experience_url)

# -------------------------
# Fetch random experience if no URL
# -------------------------
if not experience_url:
    logger.info("Fetching random Erowid experience")
    url = "https://lysergic.kaizenklass.xyz/api/v1/erowid/random/experience?size_per_substance=1"
    substances = {
        "urls": [
            "https://www.erowid.org/chemicals/dmt/dmt.shtml",
            "https://www.erowid.org/chemicals/lsd/lsd.shtml",
            "https://www.erowid.org/plants/salvia/salvia.shtml",
            "https://www.erowid.org/plants/cannabis/cannabis.shtml",
        ]
    }
    experience = requests.post(url, json=substances).json()
    experience_url = experience["experience"]["url"]

# -------------------------
# Fetch experience details
# -------------------------
logger.info("Fetching full experience details")
url = "https://lysergic.kaizenklass.xyz/api/v1/erowid/experience"
payload = {"url": experience_url}
data = requests.post(url, json=payload).json()["data"]

clean_experience = {
    "title": data["title"],
    "username": data["author"],
    "gender": data["metadata"].get("gender", "Unknown"),
    "age": data["metadata"].get("age", "Unknown"),
    "content": data["content"],
    "doses": data["doses"],
}

logger.info("Loaded experience: '%s' by %s",
            clean_experience["title"], clean_experience["username"])

substances_used = sorted({d["substance"] for d in clean_experience["doses"]})
substances_text = ", ".join(substances_used)

# -------------------------
# Build narration script
# -------------------------
tts_script = f"""
Welcome.

This is a narrated experience report sourced from Erowid dot org,
a public archive of psychoactive experience reports shared for
educational and harm reduction purposes.

This video is not an endorsement, not medical advice,
and does not encourage illegal activity.

Listener discretion is advised.

{clean_experience['title']}.

This experience was submitted under the username
{clean_experience['username']}.

Reported age: {clean_experience['age']}.
Reported gender: {clean_experience['gender']}.

The substances involved in this experience include:
{substances_text}.

What follows is the original experience,
with minimal edits for clarity.

{clean_experience['content']}

Experiences like this can be deeply personal and unpredictable,
and are influenced by mindset, environment,
and many other factors.

If you choose to explore altered states of consciousness,
education, preparation, and harm reduction are essential.

Thank you for listening.
"""

clean_text = normalize_text(tts_script)
segments = split_with_punctuation(clean_text)

# -------------------------
# Load TTS
# -------------------------
logger.info("Loading Coqui TTS model")
tts = TTS(
    model_name="tts_models/en/vctk/vits",
    progress_bar=False,
    gpu=False
)

speaker = "p232"
sr = tts.synthesizer.output_sample_rate

# -------------------------
# Generate audio with pauses
# -------------------------
audio_parts = []

for text, pause in segments:
    logger.info("Speaking: %s", text[:60])
    wav = tts.tts(text=text, speaker=speaker)
    audio_parts.append(wav)
    audio_parts.append(silence(pause, sr))

# Extra dramatic pause after title
audio_parts.insert(
    segments.index((f"{clean_experience['title']}.", 1.0)) + 1,
    silence(2.0, sr)
)

final_audio = np.concatenate(audio_parts)

# -------------------------
# Save
# -------------------------
audio_filename = sanitize_filename(clean_experience["title"]) + ".wav"
sf.write(audio_filename, final_audio, sr)
logger.info("Saved audio as %s", audio_filename)

print(audio_filename)

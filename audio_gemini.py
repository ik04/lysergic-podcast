import os
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

from google import genai

# -------------------------
# Logging setup
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# -------------------------
# Load environment
# -------------------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY environment variable not set")

# -------------------------
# Create Gemini client
# -------------------------
client = genai.Client(api_key=GOOGLE_API_KEY)

# -------------------------
# Helpers
# -------------------------
def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def silence(seconds: float, sr: int):
    return np.zeros(int(seconds * sr), dtype=np.float32)

def sanitize_filename(name: str) -> str:
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return "".join(c for c in name if c in valid_chars).replace(" ", "_")

def split_with_punctuation(text: str):
    parts = re.findall(r'[^.!?]+[.!?]?', text)
    result = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        last_char = part[-1]
        pause = 1.0 if last_char in ".!?" else 0.3
        result.append((part, pause))
    return result

# -------------------------
# Gemini cleanup + extract primary substance
# -------------------------
def clean_and_extract(content: str):
    prompt = (
        "Clean up the following experience content by fixing punctuation "
        "and removing repeated sentences, then return a JSON object with:\n"
        "  {\"cleaned_content\": ..., \"primary_substance\": ...}\n"
        "Do not add extra keys.\n"
        f"Content:\n{content}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    text_out = response.text.strip()
    # Try to parse JSON
    import json
    try:
        parsed = json.loads(text_out)
        return parsed.get("cleaned_content", content), parsed.get("primary_substance", "Unknown")
    except json.JSONDecodeError:
        logger.warning("Gemini output not JSON; using fallback")
        fallback_clean = content
        fallback_primary = "Unknown"
        match = re.search(r'\b(LSD|DMT|Salvia|MDMA|Cannabis)\b', content, re.IGNORECASE)
        if match:
            fallback_primary = match.group(0)
        return fallback_clean, fallback_primary

# -------------------------
# Parse experience URL
# -------------------------
experience_url = None
if len(sys.argv) > 1:
    experience_url = unquote(sys.argv[1])
    logger.info("Using provided experience URL: %s", experience_url)

# -------------------------
# Fetch random if none
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
            "https://www.erowid.org/chemicals/mdma/mdma.shtml"
        ]
    }
    experience = requests.post(url, json=substances).json()
    experience_url = experience["experience"]["url"]

# -------------------------
# Fetch experience details
# -------------------------
logger.info("Fetching full experience details")
resp = requests.post("https://lysergic.kaizenklass.xyz/api/v1/erowid/experience", json={"url": experience_url})
data = resp.json().get("data", {})

raw_content = data.get("content", "")
cleaned_content, primary_substance = clean_and_extract(raw_content)
logger.info("Primary substance: %s", primary_substance)

# -------------------------
# Build TTS text
# -------------------------
clean_experience = {
    "title": data.get("title", "Unknown Title"),
    "username": data.get("author", "Unknown"),
    "gender": data.get("metadata", {}).get("gender", "Unknown"),
    "age": data.get("metadata", {}).get("age", "Unknown"),
}

tts_script = f"""
Welcome.

This is a narrated experience report from Erowid.org.

{clean_experience['title']}.

Submitted by {clean_experience['username']}.
Age: {clean_experience['age']}.
Gender: {clean_experience['gender']}.

Primary substance: {primary_substance}.

{cleaned_content}

Thank you for listening.
"""

# -------------------------
# Generate audio
# -------------------------
logger.info("Loading TTS model")
tts = TTS(model_name="tts_models/en/vctk/vits", progress_bar=False, gpu=False)
sr = tts.synthesizer.output_sample_rate

segments = split_with_punctuation(normalize_text(tts_script))
audio_parts = []

for text, pause in segments:
    logger.info("Synthesizing: %s...", text[:40])
    wav = tts.tts(text=text, speaker="p232")
    audio_parts.append(wav)
    audio_parts.append(silence(pause, sr))

final_audio = np.concatenate(audio_parts)

audio_filename = sanitize_filename(clean_experience["title"]) + ".wav"
sf.write(audio_filename, final_audio, sr)
logger.info("Saved audio as %s", audio_filename)

print(f"{audio_filename}|{primary_substance}")

import subprocess
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

AUDIO_SCRIPT = "audio.py"
VIDEO_SCRIPT = "video.py"
YT_SCRIPT = "yt.py"
# Optional experience URL argument
experience_url = sys.argv[1] if len(sys.argv) > 1 else None

# -------------------------
# Run audio.py
# -------------------------
logger.info("Running audio.py...")
cmd = ["python", AUDIO_SCRIPT]
if experience_url:
    cmd.append(experience_url)

result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    logger.error("audio.py failed!\n%s", result.stderr)
    exit(1)

# Only take the last line of stdout as the audio file
audio_file = result.stdout.strip().splitlines()[-1]
logger.info("Generated audio: %s", audio_file)

# -------------------------
# Run video.py with audio
# -------------------------
logger.info("Running video.py...")
video_result = subprocess.run(["python", VIDEO_SCRIPT, audio_file])
if video_result.returncode != 0:
    logger.error("video.py failed!")
    exit(1)


video_file = video_result.stdout.strip().splitlines()[-1]
# -------------------------
# Upload to YouTube
# -------------------------
logger.info("Uploading to YouTube...")

# Extract title from filename
title = audio_file.replace(".wav", "").replace("_", " ")

PLAYLIST_ID = "PL6-XViE7MT_Br2si0sy6AHk_omwmj9q4G"

yt_result = subprocess.run([
    "python",
    YT_SCRIPT,
    video_file,   # or whatever video.py outputs
    title,
    PLAYLIST_ID
])

if yt_result.returncode != 0:
    logger.error("yt.py failed!")
    exit(1)

logger.info("YouTube upload completed!")


logger.info("Pipeline completed successfully!")

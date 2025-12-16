import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

AUDIO_SCRIPT = "audio.py"
VIDEO_SCRIPT = "video.py"

# Run audio.py
logger.info("Running audio.py...")
result = subprocess.run(
    ["python", AUDIO_SCRIPT],
    capture_output=True,
    text=True,
)
if result.returncode != 0:
    logger.error("audio.py failed!\n%s", result.stderr)
    exit(1)

# Only take the last line of stdout as the audio file
audio_file = result.stdout.strip().splitlines()[-1]
logger.info("Generated audio: %s", audio_file)

# Run video.py with audio filename
logger.info("Running video.py...")
video_result = subprocess.run(["python", VIDEO_SCRIPT, audio_file])
if video_result.returncode != 0:
    logger.error("video.py failed!")
    exit(1)

logger.info("Pipeline completed successfully!")

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

# -------------------------
# Parse arguments
# -------------------------
experience_url = None
auto_upload = False

for arg in sys.argv[1:]:
    if arg == "-y":
        auto_upload = True
    else:
        experience_url = arg

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

audio_file = result.stdout.strip().splitlines()[-1]
logger.info("Generated audio: %s", audio_file)

# -------------------------
# Run video.py with audio
# -------------------------
logger.info("Running video.py...")
video_result = subprocess.run(
    ["python", VIDEO_SCRIPT, audio_file],
    capture_output=True,
    text=True
)
if video_result.returncode != 0:
    logger.error("video.py failed!\n%s", video_result.stderr)
    exit(1)

video_file = video_result.stdout.strip().splitlines()[-1]
logger.info("Generated video: %s", video_file)

# -------------------------
# YouTube upload
# -------------------------
PLAYLIST_ID = "PL6-XViE7MT_Br2si0sy6AHk_omwmj9q4G"

if not auto_upload:
    answer = input("Upload video to YouTube? [y/n]: ").strip().lower()
    if answer != "y":
        logger.info("Upload cancelled.")
        exit(0)

logger.info("Uploading to YouTube...")
yt_result = subprocess.run([
    "python",
    YT_SCRIPT,
    video_file,
    PLAYLIST_ID
], capture_output=True, text=True)

if yt_result.returncode != 0:
    logger.error("yt.py failed!\n%s", yt_result.stderr)
    exit(1)

logger.info("YouTube upload completed!")
logger.info("Pipeline completed successfully!")

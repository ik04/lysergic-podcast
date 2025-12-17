import sys
import os
import logging
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from moviepy.audio.fx.all import volumex, audio_loop
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------
# Parameters
# -------------------------
if len(sys.argv) < 2:
    logger.error("Usage: python video.py <tts_audio_file>")
    sys.exit(1)

random_music_index = random.randint(1, 6)
random_clip_index = random.randint(1, 5)

tts_audio_file = sys.argv[1]  # TTS audio
music_file = f"music/{random_music_index}.mp3"    # Background music
clip_file = f"clips/{random_clip_index}.mp4"     # Video clip

output_folder = "output"
os.makedirs(output_folder, exist_ok=True)
base_name = os.path.splitext(os.path.basename(tts_audio_file))[0]
output_file = os.path.join(output_folder, f"{base_name}.mp4")

# -------------------------
# Load clips
# -------------------------
logger.info("Loading TTS audio: %s", tts_audio_file)
tts_clip = AudioFileClip(tts_audio_file)

logger.info("Loading background music: %s", music_file)
music_clip = AudioFileClip(music_file)

logger.info("Loading video clip: %s", clip_file)
video_clip = VideoFileClip(clip_file)

# -------------------------
# Loop video clip to match TTS duration
# -------------------------
loops = int(tts_clip.duration // video_clip.duration) + 1
video_clip = video_clip.loop(n=loops).subclip(0, tts_clip.duration)

# -------------------------
# Loop music to match TTS duration
# -------------------------
music_clip = audio_loop(music_clip, duration=tts_clip.duration)
music_clip = volumex(music_clip, 0.1)  # Lower music volume

# -------------------------
# Overlay audio
# -------------------------
combined_audio = CompositeAudioClip([music_clip, tts_clip])
video_clip = video_clip.set_audio(combined_audio)

# -------------------------
# Export
# -------------------------
logger.info("Exporting final video to %s", output_file)
video_clip.write_videofile(
    output_file,
    codec="libx264",
    audio_codec="aac",
    preset="medium",
    threads=4
)

logger.info("Video exported successfully!")

# -------------------------
# Cleanup
# -------------------------
if os.path.exists(tts_audio_file):
    os.remove(tts_audio_file)
    logger.info(f"Removed temporary audio file: {tts_audio_file}")

# -------------------------
# Output for runner
# -------------------------
print(output_file)

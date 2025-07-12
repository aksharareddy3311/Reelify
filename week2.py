import os
import subprocess
import whisper
import re
import math

# ------------ CONFIG ------------
YOUTUBE_URL = "https://youtu.be/R4AbzwYOmNE?si=EjVFXQt_beB9Gg4f"
VIDEO_FILE = "input_video.mp4"
AUDIO_FILE = "audio000.wav"
TRANSCRIPT_FILE = "transcript000.txt"
INTERVAL_SECONDS = 30  # Clip length
# --------------------------------

def download_youtube_video():
    print("Downloading video...")
    subprocess.run(["yt-dlp", "-f", "best", "-o", VIDEO_FILE, YOUTUBE_URL], check=True)

def extract_audio():
    print("Extracting audio...")
    subprocess.run([
        "ffmpeg", "-y", "-i", VIDEO_FILE,
        "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", AUDIO_FILE
    ], check=True)
    print("Audio saved as:", AUDIO_FILE)

def transcribe_audio():
    print("Transcribing audio with Whisper...")
    model = whisper.load_model("base")
    result = model.transcribe(AUDIO_FILE)
    with open(TRANSCRIPT_FILE, "w", encoding="utf-8") as f:
        f.write(result["text"])
    print("Transcript saved as:", TRANSCRIPT_FILE)

def get_video_duration():
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", VIDEO_FILE],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)

def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02}:{m:02}:{s:02}"

def generate_fixed_timestamps(duration):
    print("Generating fixed timestamps...")
    timestamps = []
    for start in range(0, int(duration), INTERVAL_SECONDS):
        end = min(start + INTERVAL_SECONDS, int(duration))
        timestamps.append((format_time(start), format_time(end)))
    return timestamps

def create_clips(timestamps):
    print("Creating video clips...")
    for idx, (start, end) in enumerate(timestamps):
        output_clip = f"clip_{idx+1}.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-i", VIDEO_FILE,
            "-ss", start, "-to", end,
            "-vf", "scale=1080:-2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k", output_clip
        ], check=True)
        print(f"Created: {output_clip}")

def main():
    download_youtube_video()
    extract_audio()
    transcribe_audio()
    duration = get_video_duration()
    timestamps = generate_fixed_timestamps(duration)
    create_clips(timestamps)

if __name__ == "__main__":
    main()

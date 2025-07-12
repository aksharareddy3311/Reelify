import os
import subprocess
import whisper
import numpy as np

# -------- CONFIG --------
FFMPEG_PATH = "C:\\Users\\91888\\Documents\\ffmpeg.exe"  # Update this path if needed
YOUTUBE_URL = "https://youtu.be/R4AbzwYOmNE?si=EjVFXQt_beB9Gg4f"
INPUT_VIDEO = "input_video.mp4"
AUDIO_FILE = "audio.wav"
REEL_CLIP = "reel_clip.mp4"
WHISPER_MODEL = "base"
# ------------------------

def download_youtube_video():
    print("Downloading video from YouTube...")
    try:
        subprocess.run(["yt-dlp", "-f", "best", "-o", INPUT_VIDEO, YOUTUBE_URL], check=True)
        print("Downloaded:", INPUT_VIDEO)
        return True
    except subprocess.CalledProcessError as e:
        print("yt-dlp failed:", e)
        return False

def extract_audio():
    print("Extracting audio from video...")
    if not os.path.exists(INPUT_VIDEO):
        print(f"'{INPUT_VIDEO}' not found.")
        return False

    if not os.path.exists(FFMPEG_PATH):
        print(f"ffmpeg not found at '{FFMPEG_PATH}'")
        return False

    try:
        subprocess.run([
            FFMPEG_PATH, "-y", "-i", INPUT_VIDEO,
            "-q:a", "0", "-map", "a", AUDIO_FILE
        ], check=True)
        print("Audio saved as:", AUDIO_FILE)
        return True
    except subprocess.CalledProcessError as e:
        print("FFmpeg audio extraction failed:", e)
        return False

def transcribe_and_find_best_segment():
    print("Transcribing audio using Whisper...")

    import whisper.audio
    from whisper.audio import SAMPLE_RATE

    def custom_load_audio(file: str):
        cmd = [
            FFMPEG_PATH,
            "-nostdin",
            "-threads", "0",
            "-i", file,
            "-f", "f32le",
            "-ac", "1",
            "-acodec", "pcm_f32le",
            "-ar", str(SAMPLE_RATE),
            "-"
        ]
        out = subprocess.run(cmd, capture_output=True, check=True).stdout
        return np.frombuffer(out, np.float32).flatten()

    whisper.audio.load_audio = custom_load_audio

    model = whisper.load_model(WHISPER_MODEL)
    result = model.transcribe(AUDIO_FILE)

    best_start = 0
    best_duration = 0
    best_text = ""

    for segment in result["segments"]:
        duration = segment["end"] - segment["start"]
        if 25 <= duration <= 30 and duration > best_duration:
            best_start = segment["start"]
            best_duration = duration
            best_text = segment["text"]

    if best_duration == 0:
        print("No ideal 25–30s segment found. Using fallback (0–30s).")
        best_start = 0
        best_duration = 30

    print(f"Selected Segment: {best_start:.2f}s to {best_start + best_duration:.2f}s")
    print("Transcript:", best_text)
    return best_start, best_duration

def create_reel_clip(start_time, duration):
    print("Creating vertical reel...")
    try:
        subprocess.run([
            FFMPEG_PATH, "-y", "-ss", str(start_time), "-i", INPUT_VIDEO,
            "-t", str(duration),
            "-vf", "scale=1080:-2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
            REEL_CLIP
        ], check=True)
        print("Reel created at:", os.path.abspath(REEL_CLIP))
    except subprocess.CalledProcessError as e:
        print("Error during reel creation:", e)

def main():
    print("Working directory:", os.getcwd())
    if download_youtube_video():
        if extract_audio():
            start_time, duration = transcribe_and_find_best_segment()
            create_reel_clip(start_time, duration)

if __name__ == "__main__":
    main()

import os
import subprocess
import whisper
import numpy as np

# -------- CONFIG --------
FFMPEG_PATH = "C:\\Users\\91888\\Documents\\ffmpeg.exe"  # 👈 Your exact path to ffmpeg.exe
INPUT_VIDEO = "input.mp4"
AUDIO_FILE = "audio.wav"
REEL_CLIP = "reel_clip.mp4"
WHISPER_MODEL = "base"
# ------------------------

def extract_audio():
    print("Extracting audio from video...")
    if not os.path.exists(INPUT_VIDEO):
        print(f"Error: '{INPUT_VIDEO}' not found.")
        return False

    if not os.path.exists(FFMPEG_PATH):
        print(f"Error: ffmpeg not found at '{FFMPEG_PATH}'")
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

    # Force Whisper to use our ffmpeg.exe path
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
        audio = np.frombuffer(out, np.float32).flatten()
        return audio  # ✅ Whisper expects numpy array, not tensor

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
        print("No 30s segment found. Using fallback.")
        best_start = 0
        best_duration = 30

    print(f"\nSelected Segment: {best_start:.2f}s to {best_start + best_duration:.2f}s")
    print("Transcript:", best_text)
    return best_start, best_duration

def create_reel_clip(start_time, duration):
    print("Creating vertical reel (1080x1920)...")
    try:
        subprocess.run([
            FFMPEG_PATH, "-y", "-ss", str(start_time), "-i", INPUT_VIDEO,
            "-t", str(duration),
            "-vf", "scale=1080:-2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
            REEL_CLIP
        ], check=True)
        abs_path = os.path.abspath(REEL_CLIP)
        print("✅ Reel created successfully at:", abs_path)
    except subprocess.CalledProcessError as e:
        print("Error during reel creation:", e)

def main():
    print("Working directory:", os.getcwd())
    if extract_audio():
        start_time, duration = transcribe_and_find_best_segment()
        create_reel_clip(start_time, duration)

if __name__ == "__main__":
    main()

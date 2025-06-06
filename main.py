import os
import re
import subprocess
import tempfile
import streamlit as st
from pydub import AudioSegment
from gtts import gTTS

# Force pydub to use ffmpeg from system
AudioSegment.converter = "/usr/bin/ffmpeg"

def parse_script(script_text):
    entries = re.findall(r"\[(.*?)\]\n\"(.*?)\"", script_text.strip())
    result = []
    for time_range, text in entries:
        start, end = time_range.split(" - ")
        result.append((start.strip(), end.strip(), text.strip()))
    return result

def time_to_milliseconds(t):
    minutes, seconds = map(float, t.split(":"))
    return int((minutes * 60 + seconds) * 1000)

def generate_voice(text):
    filename = f"/tmp/voice_{hash(text)}.mp3"
    gTTS(text).save(filename)
    return AudioSegment.from_file(filename)

def build_audio(script):
    combined = AudioSegment.silent(duration=0)
    for start, end, line in script:
        start_ms, end_ms = time_to_milliseconds(start), time_to_milliseconds(end)
        duration = end_ms - start_ms
        voice = generate_voice(line)
        voice = voice[:duration] + AudioSegment.silent(duration=max(0, duration - len(voice)))
        if len(combined) < start_ms:
            combined += AudioSegment.silent(duration=start_ms - len(combined))
        combined += voice
    return combined

def merge_audio_video(video_path, audio_path, output_path):
    cmd = [
        "ffmpeg", "-y", "-i", video_path, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest", output_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# UI
st.title("🎙️ Voiceover Video Generator")
video = st.file_uploader("Upload your MP4 video", type=["mp4"])
script = st.text_area("Paste your timestamped script", height=300)

if st.button("Generate Voiceover") and video and script:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video.read())
        video_path = tmp.name

    parsed = parse_script(script)
    audio = build_audio(parsed)

    audio_path = tempfile.mktemp(suffix=".mp3")
    audio.export(audio_path, format="mp3")

    output_path = tempfile.mktemp(suffix=".mp4")
    merge_audio_video(video_path, audio_path, output_path)

    st.success("✅ Done! Download your video:")
    with open(output_path, "rb") as f:
        st.download_button("📥 Download Final Video", f, file_name="voiceover_video.mp4")

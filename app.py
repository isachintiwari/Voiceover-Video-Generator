# Voiceover Video Tool - Streamlit + gTTS + ffmpeg Only (No pydub)

import os
import re
import subprocess
import tempfile
import streamlit as st
from gtts import gTTS

def parse_script(script_text):
    entries = re.findall(r"\[(.*?)\]\n\"(.*?)\"", script_text.strip())
    return [(s.strip(), e.strip(), txt.strip()) for time, txt in entries for s, e in [time.split(" - ")]]

def time_to_milliseconds(t):
    m, s = map(float, t.split(":"))
    return int((m * 60 + s) * 1000)

def generate_gtts_clip(text, filename):
    tts = gTTS(text)
    tts.save(filename)

def build_audio_with_ffmpeg(script_entries, output_path):
    clips = []
    concat_txt = os.path.join(tempfile.gettempdir(), "concat.txt")
    with open(concat_txt, "w") as f:
        for i, (start, end, text) in enumerate(script_entries):
            clip_path = os.path.join(tempfile.gettempdir(), f"part_{i}.mp3")
            generate_gtts_clip(text, clip_path)
            f.write(f"file '{clip_path}'\n")
            clips.append(clip_path)

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_txt, "-c", "copy", output_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def merge_audio_video(video_path, audio_path, output_path):
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        output_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Streamlit UI
st.title("🎙️ Voiceover Video Generator")

uploaded_video = st.file_uploader("Upload your MP4 video", type=["mp4"])
uploaded_script = st.text_area("Paste your timestamped script", height=300)

if st.button("Generate Voiceover") and uploaded_video and uploaded_script:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
        tmp_video.write(uploaded_video.read())
        video_path = tmp_video.name

    parsed = parse_script(uploaded_script)
    voice_path = tempfile.mktemp(suffix=".mp3")
    build_audio_with_ffmpeg(parsed, voice_path)

    final_output = tempfile.mktemp(suffix=".mp4")
    merge_audio_video(video_path, voice_path, final_output)

    st.success("✅ Your video is ready! Download below:")
    with open(final_output, "rb") as f:
        st.download_button("📥 Download Final Video", f, file_name="voiceover_output.mp4")

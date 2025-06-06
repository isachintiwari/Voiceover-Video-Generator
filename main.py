# Voiceover Video Tool - Streamlit + ffmpeg-python Version (Safe for Cloud)

import os
import re
import tempfile
import subprocess
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment

# Force pydub to use ffmpeg (avoid PyAudio dependencies)
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


def generate_voice_clip(text):
    temp_path = f"/tmp/voice_{abs(hash(text))}.mp3"
    gTTS(text).save(temp_path)
    return AudioSegment.from_file(temp_path)


def build_audio(script_entries):
    full_audio = AudioSegment.silent(duration=0)
    for start, end, line in script_entries:
        start_ms = time_to_milliseconds(start)
        end_ms = time_to_milliseconds(end)
        target_duration = end_ms - start_ms

        voice = generate_voice_clip(line)
        voice = voice[:target_duration] + AudioSegment.silent(duration=max(0, target_duration - len(voice)))

        if len(full_audio) < start_ms:
            full_audio += AudioSegment.silent(duration=start_ms - len(full_audio))

        full_audio += voice

    return full_audio


def merge_video_audio(video_path, audio_path, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# Streamlit app interface
st.title("🎙️ Voiceover Video Generator")

uploaded_video = st.file_uploader("Upload your MP4 video", type=["mp4"])
uploaded_script = st.text_area("Paste your timestamped script", height=300)

if st.button("Generate Voiceover") and uploaded_video and uploaded_script:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(uploaded_video.read())
        video_path = tmp.name

    parsed_script = parse_script(uploaded_script)
    audio = build_audio(parsed_script)

    audio_path = tempfile.mktemp(suffix=".mp3")
    audio.export(audio_path, format="mp3")

    final_output = tempfile.mktemp(suffix=".mp4")
    merge_video_audio(video_path, audio_path, final_output)

    st.success("✅ Your video is ready. Download below:")
    with open(final_output, "rb") as f:
        st.download_button("📥 Download Final Video", f, file_name="voiceover_output.mp4")

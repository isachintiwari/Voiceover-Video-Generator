# Voiceover Video Tool - Timestamp-Aligned Version with gTTS + ffmpeg

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


def generate_gtts_clip(text, path):
    gTTS(text).save(path)


def build_timed_audio(script_entries, output_path):
    concat_list = []
    last_end = 0
    concat_txt_path = os.path.join(tempfile.gettempdir(), "concat.txt")

    with open(concat_txt_path, "w") as concat_file:
        for i, (start, end, text) in enumerate(script_entries):
            start_ms = time_to_milliseconds(start)
            end_ms = time_to_milliseconds(end)
            duration = end_ms - start_ms

            silence_duration = max(0, start_ms - last_end)
            silence_path = os.path.join(tempfile.gettempdir(), f"silence_{i}.mp3")
            voice_path = os.path.join(tempfile.gettempdir(), f"voice_{i}.mp3")

            if silence_duration > 0:
                subprocess.run([
                    "ffmpeg", "-f", "lavfi", "-i",
                    f"anullsrc=channel_layout=mono:sample_rate=44100",
                    "-t", str(silence_duration / 1000), silence_path, "-y"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                concat_file.write(f"file '{silence_path}'\n")

            generate_gtts_clip(text, voice_path)
            subprocess.run([
                "ffmpeg", "-y", "-i", voice_path, "-t", str(duration / 1000),
                os.path.join(tempfile.gettempdir(), f"voice_trimmed_{i}.mp3")
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            concat_file.write(f"file '{os.path.join(tempfile.gettempdir(), f'voice_trimmed_{i}.mp3')}'\n")
            last_end = end_ms

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_txt_path, "-c", "copy", output_path
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
    build_timed_audio(parsed, voice_path)

    final_output = tempfile.mktemp(suffix=".mp4")
    merge_audio_video(video_path, voice_path, final_output)

    st.success("✅ Your video is ready! Download below:")
    with open(final_output, "rb") as f:
        st.download_button("📥 Download Final Video", f, file_name="voiceover_output.mp4")

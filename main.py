# Voiceover Video Tool - SRT-based Version with gTTS + ffmpeg (WAV Fix for Sync Errors)

import os
import re
import subprocess
import tempfile
import streamlit as st
from gtts import gTTS


def parse_srt_file(srt_text):
    pattern = r"(\d+)\s+([\d:,]+) --> ([\d:,]+)\s+(.+?)(?=\n\d+\n|\Z)"
    matches = re.findall(pattern, srt_text.strip(), re.DOTALL)
    entries = []
    for _, start, end, text in matches:
        start = start.replace(",", ".")
        end = end.replace(",", ".")
        text = " ".join(text.strip().splitlines()).strip()
        entries.append((start, end, text))
    return entries


def srt_time_to_seconds(t):
    h, m, s = t.split(":")
    s, ms = s.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def generate_gtts_clip(text, wav_path):
    tts_mp3 = wav_path.replace(".wav", ".mp3")
    gTTS(text).save(tts_mp3)
    subprocess.run([
        "ffmpeg", "-y", "-i", tts_mp3, "-ar", "44100", "-ac", "1", wav_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Generated WAV:", wav_path, "Exists:", os.path.exists(wav_path))


def build_timed_audio_srt(srt_entries, output_path):
    concat_txt = os.path.join(tempfile.gettempdir(), "concat_srt.txt")
    last_end = 0

    with open(concat_txt, "w") as concat_file:
        for i, (start, end, text) in enumerate(srt_entries):
            start_sec = srt_time_to_seconds(start)
            end_sec = srt_time_to_seconds(end)
            duration = end_sec - start_sec

            silence_duration = max(0, start_sec - last_end)
            silence_path = os.path.join(tempfile.gettempdir(), f"silence_{i}.wav")
            voice_path = os.path.join(tempfile.gettempdir(), f"voice_{i}.wav")
            trimmed_path = os.path.join(tempfile.gettempdir(), f"voice_trimmed_{i}.wav")

            if silence_duration > 0:
                subprocess.run([
                    "ffmpeg", "-f", "lavfi", "-i",
                    "anullsrc=channel_layout=mono:sample_rate=44100",
                    "-t", str(silence_duration), silence_path, "-y"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                concat_file.write(f"file '{silence_path}'\n")

            generate_gtts_clip(text, voice_path)
            subprocess.run([
                "ffmpeg", "-y", "-i", voice_path, "-t", str(duration), trimmed_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            concat_file.write(f"file '{trimmed_path}'\n")
            last_end = end_sec

    result = subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_txt, "-c:a", "aac", output_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if not os.path.exists(output_path):
        st.error("❌ Failed to generate audio from subtitles.")
        st.text("FFmpeg audio error:")
        st.code(result.stderr.decode())


def merge_audio_video(video_path, audio_path, output_path):
    result = subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        output_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if not os.path.exists(output_path):
        st.error("❌ Failed to generate final video.")
        st.text("FFmpeg merge error:")
        st.code(result.stderr.decode())


# Streamlit UI
st.title("🎙️ Voiceover Video Generator from SRT")

uploaded_video = st.file_uploader("Upload your MP4 video", type=["mp4"])
uploaded_srt = st.file_uploader("Upload your SRT file", type=["srt"])

if st.button("Generate Voiceover") and uploaded_video and uploaded_srt:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
        tmp_video.write(uploaded_video.read())
        video_path = tmp_video.name

    srt_text = uploaded_srt.read().decode("utf-8")
    parsed_entries = parse_srt_file(srt_text)

    voice_path = tempfile.mktemp(suffix=".aac")
    build_timed_audio_srt(parsed_entries, voice_path)

    st.audio(voice_path, format="audio/aac")

    final_output = tempfile.mktemp(suffix=".mp4")
    merge_audio_video(video_path, voice_path, final_output)

    if os.path.exists(final_output):
        st.success("✅ Your video is ready! Download below:")
        with open(final_output, "rb") as f:
            st.download_button("📥 Download Final Video", f, file_name="voiceover_output.mp4")

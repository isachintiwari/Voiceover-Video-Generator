import os
import re
import subprocess
import tempfile
import streamlit as st
from gtts import gTTS
import requests

st.set_page_config(
    page_title="Voiceover Video Tool",
    page_icon="🎤",
    layout="wide",
    menu_items={
        "About": "This tool lets you auto-generate voiceovers from subtitles and add background music to videos."
    }
)

DEFAULT_MUSIC = {
    "Soft Piano": "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Komiku/It_Grows/Komiku_-_01_-_Friends_Call_Me_Jimmy.mp3",
    "Ambient Loop": "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Lobo_Loco/Sounds_of_the_Street/Lobo_Loco_-_01_-_Ladies_Night_ID_1179.mp3",
    "Calm Background": "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Monplaisir/Loyalty_Freak_Music/Monplaisir_-_03_-_Electric_Dawn.mp3",
    "Eona Ambient Pop": "https://raw.githubusercontent.com/isachintiwari/tools/dev/eona-emotional-ambient-pop-351436.mp3"
}

with st.sidebar:
    st.header("🎛️ Configuration")
    uploaded_video = st.file_uploader("Upload MP4 video", type=["mp4"])
    uploaded_srt = st.file_uploader("Upload SRT subtitles", type=["srt"])
    uploaded_music = st.file_uploader("(Optional) Upload your own background music (MP3)", type=["mp3"])
    default_music_choice = st.selectbox("Or choose a default music", ["None"] + list(DEFAULT_MUSIC.keys()))
    generate = st.button("Generate Voiceover")

st.title("🎙️ Voiceover Video Generator")
st.markdown("""
This tool helps you generate voiceovers from subtitle files and combine them with video and optional background music.
Upload your video and SRT file on the left to begin.
""")

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
    subprocess.run(["ffmpeg", "-y", "-i", tts_mp3, "-ar", "44100", "-ac", "1", wav_path], stdout=subprocess.PIPE)

def stretch_audio_to_duration(input_path, output_path, target_duration):
    subprocess.run([
        "ffmpeg", "-y", "-i", input_path,
        "-filter:a", f"apad=pad_dur={target_duration}",
        "-t", str(target_duration), output_path
    ], stdout=subprocess.PIPE)

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
            stretched_path = os.path.join(tempfile.gettempdir(), f"voice_stretch_{i}.wav")
            if silence_duration > 0:
                subprocess.run([
                    "ffmpeg", "-f", "lavfi", "-i",
                    "anullsrc=channel_layout=mono:sample_rate=44100",
                    "-t", str(silence_duration), silence_path, "-y"
                ], stdout=subprocess.PIPE)
                concat_file.write(f"file '{silence_path}'\n")
            generate_gtts_clip(text, voice_path)
            stretch_audio_to_duration(voice_path, stretched_path, duration)
            concat_file.write(f"file '{stretched_path}'\n")
            last_end = end_sec
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_txt, "-c:a", "aac", output_path
    ], stdout=subprocess.PIPE)

def add_background_music(voice_path, music_path, final_audio_path):
    subprocess.run([
        "ffmpeg", "-y", "-i", voice_path, "-i", music_path,
        "-filter_complex",
        "[1:a]volume=0.1[a1];[0:a][a1]amix=inputs=2:duration=first:dropout_transition=2",
        "-c:a", "aac", final_audio_path
    ], stdout=subprocess.PIPE)

def merge_audio_video(video_path, audio_path, output_path):
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-i", audio_path,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-shortest", output_path
    ], stdout=subprocess.PIPE)

if generate and uploaded_video and uploaded_srt:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
        tmp_video.write(uploaded_video.read())
        video_path = tmp_video.name

    srt_text = uploaded_srt.read().decode("utf-8")
    parsed_entries = parse_srt_file(srt_text)
    voice_path = tempfile.mktemp(suffix=".aac")
    build_timed_audio_srt(parsed_entries, voice_path)

    music_path = None
    final_audio = voice_path

    if uploaded_music:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_music:
            tmp_music.write(uploaded_music.read())
            music_path = tmp_music.name
    elif default_music_choice != "None":
        music_url = DEFAULT_MUSIC[default_music_choice]
        music_path = tempfile.mktemp(suffix=".mp3")
        try:
            r = requests.get(music_url)
            r.raise_for_status()
            with open(music_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            st.error(f"❌ Failed to download background music: {e}")
            music_path = None

    if music_path:
        mixed_audio = tempfile.mktemp(suffix=".aac")
        add_background_music(voice_path, music_path, mixed_audio)
        final_audio = mixed_audio

    st.subheader("🎧 Preview Voiceover")
    st.audio(final_audio, format="audio/aac")

    final_output = tempfile.mktemp(suffix=".mp4")
    merge_audio_video(video_path, final_audio, final_output)

    if os.path.exists(final_output):
        st.success("✅ Video generated successfully!")
        with open(final_output, "rb") as f:
            st.download_button("📥 Download Final Video", f, file_name="voiceover_output.mp4")

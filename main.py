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
    "Calm Background": "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Monplaisir/Loyalty_Freak_Music/Monplaisir_-_03_-_Electric_Dawn.mp3"
}

def parse_srt(file_content):
    entries = []
    blocks = re.split(r"\n\n", file_content.strip())
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            times = lines[1].split(" --> ")
            text = " ".join(lines[2:])
            entries.append((times[0], times[1], text))
    return entries

def time_to_seconds(t):
    h, m, s = t.replace(",", ".").split(":")
    return int(h)*3600 + int(m)*60 + float(s)

def generate_tts_clip(text, path):
    tts = gTTS(text)
    tts.save(path)

def combine_audio_clips(srt_entries, output_audio_path):
    temp_audio_list = []
    for idx, (start, end, text) in enumerate(srt_entries):
        start_sec = time_to_seconds(start)
        end_sec = time_to_seconds(end)
        duration = end_sec - start_sec

        tts_path = tempfile.mktemp(suffix=".mp3")
        generate_tts_clip(text, tts_path)

        padded_path = tempfile.mktemp(suffix=".mp3")
        subprocess.run([
            "ffmpeg", "-y", "-i", tts_path,
            "-af", f"apad=pad_dur={duration}",
            "-t", str(duration), padded_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        temp_audio_list.append((start_sec, padded_path))

    temp_audio_list.sort()
    concat_txt = tempfile.mktemp(suffix=".txt")
    with open(concat_txt, "w") as f:
        for _, path in temp_audio_list:
            f.write(f"file '{path}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-c", "copy", output_audio_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return output_audio_path

def merge_audio_music(voice_path, music_path, output_path):
    subprocess.run([
        "ffmpeg", "-y", "-i", voice_path, "-i", music_path, "-filter_complex",
        "[0:a]volume=1.5[a0];[1:a]volume=0.3[a1];[a0][a1]amix=inputs=2:duration=longest",
        "-c:a", "aac", "-shortest", output_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def merge_audio_video(video_path, audio_path, output_path):
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-i", audio_path, "-c:v", "copy", "-c:a", "aac", "-shortest", output_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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

### 🔧 Steps to Use:
1. **Upload your MP4 video** file using the sidebar.
2. **Upload your .srt subtitle file**, which contains the timed narration.
3. **(Optional)** Add your own background music or pick from the default list.
4. Click the **Generate Voiceover** button.
5. Wait for the tool to process and download the final video.

### 📄 SRT File Format Example:
```
1
00:00:00,000 --> 00:00:05,000
Welcome! In this quick guide, you'll learn how to use this tool to create voiceovers with background music.

2
00:00:06,000 --> 00:00:15,000
First, upload your video file and subtitle file using the options on the left.

3
00:00:16,000 --> 00:00:25,000
Then, optionally upload background music or choose a default one. Click the button to generate your final video.
```
Ensure your timestamps are formatted correctly and do not overlap.
""")

if generate and uploaded_video and uploaded_srt:
    with st.spinner("⏳ Generating video with voiceover, please wait..."):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as v_tmp:
                v_tmp.write(uploaded_video.read())
                video_path = v_tmp.name

            srt_text = uploaded_srt.read().decode("utf-8")
            entries = parse_srt(srt_text)

            voice_path = tempfile.mktemp(suffix=".mp3")
            combine_audio_clips(entries, voice_path)

            if uploaded_music:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as m_tmp:
                    m_tmp.write(uploaded_music.read())
                    music_path = m_tmp.name
            elif default_music_choice != "None":
                music_url = DEFAULT_MUSIC[default_music_choice]
                music_path = tempfile.mktemp(suffix=".mp3")
                r = requests.get(music_url)
                with open(music_path, "wb") as f:
                    f.write(r.content)
            else:
                music_path = None

            final_audio = tempfile.mktemp(suffix=".aac")
            if music_path:
                merge_audio_music(voice_path, music_path, final_audio)
            else:
                final_audio = voice_path

            final_video = tempfile.mktemp(suffix=".mp4")
            merge_audio_video(video_path, final_audio, final_video)

            st.success("✅ Processing complete! You can now download your video.")
            with open(final_video, "rb") as f:
                video_bytes = f.read()
                st.video(video_bytes)
            with open(final_video, "rb") as f:
                st.download_button("📥 Download Final Video", f, file_name="final_output.mp4")
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
